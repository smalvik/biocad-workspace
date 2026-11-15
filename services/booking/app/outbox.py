"""Post-commit publisher; broker failures never participate in the booking transaction."""

import asyncio
import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import aio_pika
from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.config import get_settings
from app.db import get_engine
from app.models import Employee, Floor, Office, OutboxEvent, Space

EXCHANGE = "biocad.booking.events.v1"
QUEUE = "biocad.notifications.v1"
DEAD_EXCHANGE = "biocad.notifications.invalid.v1"
TYPES = ("booking.created.v1", "booking.cancelled.v1")


@lru_cache
def demo_address():
    path = Path("data/demo_fixture.json")
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / "docs/data/demo_fixture.json"
    return json.loads(path.read_text(encoding="utf-8"))["office_address"]


async def notification_snapshot(db, employee_id: str, space_id: str) -> dict:
    row = (
        await db.execute(
            select(Employee, Space, Floor, Office)
            .select_from(Space)
            .join(Floor, Floor.id == Space.floor_id)
            .join(Office, Office.id == Floor.office_id)
            .join(Employee, Employee.id == employee_id)
            .where(Space.id == space_id)
        )
    ).one()
    employee, space, floor, office = row
    return {
        "recipient": employee.id + "@example.test" if employee.fictional else None,
        "employee_name": employee.full_name,
        "fictional": employee.fictional,
        "kind": space.kind,
        "office_name": office.name,
        "office_address": demo_address() if office.id == "moscow-a" else office.name,
        "floor_name": floor.name,
    }


async def topology(channel):
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    dead = await channel.declare_exchange(DEAD_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
    invalid = await channel.declare_queue(QUEUE + ".invalid", durable=True)
    await invalid.bind(dead)
    queue = await channel.declare_queue(
        QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DEAD_EXCHANGE,
            "x-max-length": 10000,
            "x-overflow": "reject-publish",
        },
    )
    for event_type in TYPES:
        await queue.bind(exchange, routing_key=event_type)
    return exchange


async def envelope(db, event: OutboxEvent) -> dict:
    body = {**event.payload, "type": event.event_type}
    # Old committed schema-1 events remain deliverable after an image rollback/upgrade.
    if "notification" not in body:
        body["notification"] = await notification_snapshot(db, body["employee_id"], body["space_id"])
    return body


class OutboxPublisher:
    async def publish_one(self, exchange) -> bool:
        async with AsyncSession(get_engine(), expire_on_commit=False) as db, db.begin():
            earlier = aliased(OutboxEvent)
            event = await db.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.published_at.is_(None),
                    OutboxEvent.event_type.in_(TYPES),
                    or_(
                        OutboxEvent.event_type == TYPES[0],
                        ~exists(
                            select(earlier.id).where(
                                earlier.aggregate_id == OutboxEvent.aggregate_id,
                                earlier.event_type == TYPES[0],
                                earlier.published_at.is_(None),
                            )
                        ),
                    ),
                )
                .order_by(OutboxEvent.occurred_at, OutboxEvent.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if event is None:
                return False
            body = await envelope(db, event)
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body, ensure_ascii=False).encode(),
                    message_id=str(event.id),
                    correlation_id=body["correlation_id"],
                    type=event.event_type,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=event.event_type,
                mandatory=True,
                timeout=5,
            )
            # This transaction commits only after RabbitMQ's persistent publisher confirm.
            # An ambiguous confirm/DB commit may republish the same stable event_id.
            event.published_at = datetime.now(UTC)
        return True

    async def run(self):
        settings = get_settings()
        if not settings.notifications_enabled:
            return
        while True:
            try:
                async with await aio_pika.connect_robust(
                    settings.rabbitmq_url.get_secret_value(), timeout=3
                ) as connection:
                    channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
                    exchange = await topology(channel)
                    while True:
                        if not await self.publish_one(exchange):
                            await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                print(
                    json.dumps({"service": "outbox", "state": "retry", "error_type": type(error).__name__}),
                    flush=True,
                )
                await asyncio.sleep(2)
