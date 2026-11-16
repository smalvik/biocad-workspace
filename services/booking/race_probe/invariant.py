"""Run explicitly in child pytest processes; the winner oracle is identical in both phases."""

import asyncio
import json
import os
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import allure
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

GATE = 841008
pytestmark = [pytest.mark.integration, allure.feature("race-red-green")]


def metadata():
    allure.dynamic.suite("Intentional mutation / " + os.environ.get("WB08_PHASE", "unknown"))
    for name, variable, default in (
        ("run_type", "RUN_TYPE", "regression"),
        ("environment", "REPORT_ENV", "local"),
        ("git_sha", "GIT_SHA", "dev"),
        ("release_version", "RELEASE_VERSION", "unreleased"),
        ("working_tree", "WORKING_TREE", "unknown"),
        ("mutation_phase", "WB08_PHASE", "unknown"),
    ):
        allure.dynamic.label(name, os.environ.get(variable, default))


async def authenticated(url, employee):
    client = httpx.AsyncClient(base_url=url, timeout=30)
    response = await client.post(
        "/api/v1/auth/login", json={"username": employee, "password": "demo-workspace"}
    )
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client


@pytest.mark.parametrize("resource", ["D-15", "M-03"])
async def test_two_process_confirmations_have_one_winner(resource):
    metadata()
    urls = json.loads(os.environ["WB08_URLS"])
    clients = [await authenticated(urls[0], "e01"), await authenticated(urls[1], "e02")]
    engine = create_async_engine(os.environ["DATABASE_URL"])
    phase = os.environ["WB08_PHASE"]
    key_prefix = f"wb08:{phase}:{resource}:{uuid4().hex}:"
    start = (datetime.now(UTC) + timedelta(days=60)).replace(hour=9, minute=0, second=0, microsecond=0)
    body = {
        "space_id": resource,
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
    }
    tasks = []
    request_ids = [str(uuid4()), str(uuid4())]
    try:
        async with engine.connect() as controller:
            await controller.execute(text("SELECT pg_advisory_lock(:gate)"), {"gate": GATE})
            try:
                tasks = [
                    asyncio.create_task(
                        client.post(
                            "/api/v1/bookings",
                            json=body,
                            headers={
                                "Idempotency-Key": key_prefix + str(index),
                                "X-Request-ID": request_ids[index],
                            },
                        )
                    )
                    for index, client in enumerate(clients)
                ]
                # Observe both real INSERT transactions blocked inside the BEFORE trigger.
                # Release according to database state, not a guessed sleep duration.
                async with asyncio.timeout(20):
                    while True:
                        arrivals = await controller.scalar(
                            text("""SELECT count(*) FROM pg_locks l
                            JOIN pg_stat_activity a ON a.pid=l.pid
                            WHERE a.datname=current_database() AND l.locktype='advisory'
                            AND l.mode='ShareLock' AND NOT l.granted AND l.classid=0 AND l.objid=841008""")
                        )
                        if arrivals == 2:
                            break
                        if any(task.done() for task in tasks):
                            raise AssertionError("A candidate returned before reaching the INSERT gate")
                        await asyncio.sleep(0.02)
            finally:
                await controller.execute(text("SELECT pg_advisory_unlock(:gate)"), {"gate": GATE})
            responses = await asyncio.gather(*tasks)
            persisted = await controller.scalar(
                text("""SELECT count(*) FROM bookings
                WHERE idempotency_key LIKE :prefix AND status='confirmed'"""),
                {"prefix": key_prefix + "%"},
            )
            events = await controller.scalar(
                text("""SELECT count(*) FROM outbox_events o JOIN bookings b
                ON b.id=o.aggregate_id WHERE b.idempotency_key LIKE :prefix"""),
                {"prefix": key_prefix + "%"},
            )
        observed = {
            "resource": resource,
            "phase": phase,
            "blocked_insert_transactions": arrivals,
            "http_statuses": sorted(row.status_code for row in responses),
            "committed_confirmed": persisted,
            "outbox_events": events,
            "request_ids": request_ids,
            "response_request_ids": [row.headers.get("x-request-id") for row in responses],
        }
        Path(os.environ["WB08_OUTPUT"], resource + ".json").write_text(json.dumps(observed), encoding="utf-8")
        allure.attach(
            json.dumps(observed, indent=2),
            "Actual synchronized HTTP/database observations",
            allure.attachment_type.JSON,
        )
        assert (
            Counter(row.status_code for row in responses) == {201: 1, 409: 1} and persisted == events == 1
        ), ("NONOVERLAP_INVARIANT: exactly one committed winner/event required", observed)
        assert (
            next(row for row in responses if row.status_code == 409).json()["error"]["code"]
            == "BOOKING_CONFLICT"
        )
        assert observed["response_request_ids"] == request_ids
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for client in clients:
            await client.aclose()
        await engine.dispose()


async def test_restored_half_open_constraint_allows_adjacency_and_cancelled_interval():
    metadata()
    client = await authenticated(json.loads(os.environ["WB08_URLS"])[0], "e01")
    start = datetime.now(UTC) + timedelta(days=61)

    async def book(first, last):
        return await client.post(
            "/api/v1/bookings",
            json={"space_id": "D-16", "start_at": first.isoformat(), "end_at": last.isoformat()},
            headers={"Idempotency-Key": "wb08:control:" + uuid4().hex},
        )

    try:
        first = await book(start, start + timedelta(hours=1))
        adjacent = await book(start + timedelta(hours=1), start + timedelta(hours=2))
        assert first.status_code == adjacent.status_code == 201
        assert (await client.post("/api/v1/bookings/" + first.json()["id"] + "/cancel")).status_code == 200
        assert (await book(start, start + timedelta(hours=1))).status_code == 201
    finally:
        await client.aclose()
