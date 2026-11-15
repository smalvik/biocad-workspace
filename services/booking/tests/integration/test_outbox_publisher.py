"""Publisher confirmation/ordering against a private PostgreSQL outbox table and real row locks."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import allure
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import app.outbox as publisher

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("outbox")]


@pytest.fixture
async def isolated_outbox(database, monkeypatch):
    schema = "wb07_" + uuid4().hex
    async with database.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.execute(
            text(f'CREATE TABLE "{schema}".outbox_events (LIKE public.outbox_events INCLUDING ALL)')
        )
    import os

    engine = create_async_engine(
        os.environ["DATABASE_URL"], connect_args={"server_settings": {"search_path": schema}}
    )
    monkeypatch.setattr(publisher, "get_engine", lambda: engine)
    try:
        yield engine
    finally:
        await engine.dispose()
        async with database.begin() as connection:
            # Only this test's generated table/schema; no live booking-table mutation.
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


async def add_event(engine, booking, kind, offset):
    ident = uuid4()
    body = {
        "event_id": str(ident),
        "booking_id": str(booking),
        "schema_version": 1,
        "correlation_id": str(uuid4()),
        "notification": {"fictional": True},
    }
    async with engine.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,aggregate_id,event_type,schema_version,payload,occurred_at)
            VALUES(:id,:booking,:kind,1,CAST(:payload AS jsonb),:at)"""),
            {
                "id": ident,
                "booking": booking,
                "kind": kind,
                "payload": json.dumps(body),
                "at": datetime.now(UTC) + timedelta(seconds=offset),
            },
        )
    return ident


async def test_nack_or_unroutable_publish_remains_pending_and_reuses_identity(isolated_outbox):
    engine = isolated_outbox
    ident = await add_event(engine, uuid4(), publisher.TYPES[0], 0)

    class Broken:
        async def publish(self, *args, **kwargs):
            raise RuntimeError("No persistent broker confirmation")

    with pytest.raises(RuntimeError):
        await publisher.OutboxPublisher().publish_one(Broken())
    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT published_at FROM outbox_events")) is None
    sent = []

    class Confirmed:
        async def publish(self, message, **kwargs):
            sent.append((message, kwargs))

    assert await publisher.OutboxPublisher().publish_one(Confirmed())
    assert sent[0][0].message_id == str(ident)
    assert sent[0][0].delivery_mode.value == 2
    assert sent[0][1]["mandatory"] is True
    async with engine.connect() as connection:
        assert await connection.scalar(text("SELECT published_at FROM outbox_events")) is not None


async def test_two_publishers_do_not_overtake_unconfirmed_creation(isolated_outbox):
    engine = isolated_outbox
    booking = uuid4()
    await add_event(engine, booking, publisher.TYPES[0], 0)
    await add_event(engine, booking, publisher.TYPES[1], 1)
    entered, release = asyncio.Event(), asyncio.Event()
    sent = []

    class Slow:
        async def publish(self, message, **kwargs):
            entered.set()
            await release.wait()
            sent.append(message.type)

    class Fast:
        async def publish(self, message, **kwargs):
            sent.append(message.type)

    first = asyncio.create_task(publisher.OutboxPublisher().publish_one(Slow()))
    try:
        await asyncio.wait_for(entered.wait(), timeout=5)
        assert not await publisher.OutboxPublisher().publish_one(Fast())
    finally:
        release.set()
        await first
    assert await publisher.OutboxPublisher().publish_one(Fast())
    assert sent == [publisher.TYPES[0], publisher.TYPES[1]]
