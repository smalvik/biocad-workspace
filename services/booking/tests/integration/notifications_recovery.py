"""Explicit runner phases: real broker/SMTP outages in the disposable Compose project only."""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import aio_pika
import allure
import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OutboxEvent
from app.outbox import envelope, topology

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("notification-recovery")]
MARKER = Path("/allure-results/notification-recovery.json")


async def mail(api_url, booking_id, title, expected=1):
    async with httpx.AsyncClient(base_url=api_url, timeout=10) as client:
        for _ in range(120):
            response = await client.get("/api/v1/search", params={"query": f'subject:"{booking_id}"'})
            response.raise_for_status()
            found = [row for row in response.json()["messages"] if row["Subject"].startswith(title)]
            if len(found) == expected:
                body = await client.get("/api/v1/message/" + found[0]["ID"])
                body.raise_for_status()
                return found, body.json()
            await asyncio.sleep(0.5)
    pytest.fail("Expected exactly one captured notification for the isolated booking")


async def published(database, booking_id, expected):
    for _ in range(80):
        async with AsyncSession(database) as db:
            row = await db.scalar(
                select(OutboxEvent).where(
                    OutboxEvent.aggregate_id == UUID(booking_id),
                    OutboxEvent.event_type == "booking.created.v1",
                )
            )
            assert row is not None
            if (row.published_at is not None) == expected:
                return
        await asyncio.sleep(0.25)
    pytest.fail("Unexpected outbox publication state")


async def test_notification_outage_and_restart_recovery(api, database):
    phase = os.environ.get("NOTIFICATION_PHASE")
    assert phase in {
        "broker_down",
        "broker_recovered",
        "duplicate_after_restart",
        "smtp_down",
        "smtp_recovered",
    }
    allure.dynamic.title("Notification recovery: " + phase)
    allure.dynamic.parameter("phase", phase)
    mailpit = os.environ["MAILPIT_API_URL"]
    if phase == "broker_down":
        start = (datetime.now(UTC) + timedelta(days=100 + uuid4().int % 20000)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        slot = {
            "space_id": "D-15",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        }
        response = await api.post("/api/v1/bookings", json=slot, headers={"Idempotency-Key": uuid4().hex})
        assert response.status_code == 201
        assert response.json()["status"] == "confirmed"
        await published(database, response.json()["id"], False)
        MARKER.write_text(json.dumps({"slot": slot, "broker_booking": response.json()}), encoding="utf-8")
        return
    saved = json.loads(MARKER.read_text())
    booking_id = saved["broker_booking"]["id"]
    if phase == "broker_recovered":
        await published(database, booking_id, True)
        _, body = await mail(mailpit, booking_id, "Бронь подтверждена")
        assert body["To"][0]["Address"] == "e01@example.test"
        assert "Демонстрационный проезд" in body["HTML"]
        assert "12:00" in body["Text"] and "13:00 МСК" in body["Text"]
        assert "http://web/" in body["HTML"] and "D-15" in body["Text"]
        assert booking_id in body["Text"] and "Этаж 2" in body["Text"]
        assert "Анна Смирнова" in body["Text"] and "support@example.test" in body["HTML"]
        first = await api.post(f"/api/v1/bookings/{booking_id}/cancel")
        second = await api.post(f"/api/v1/bookings/{booking_id}/cancel")
        assert first.status_code == second.status_code == 200
        await mail(mailpit, booking_id, "Бронь отменена")
    elif phase == "duplicate_after_restart":
        async with AsyncSession(database) as db:
            events = list(
                await db.scalars(select(OutboxEvent).where(OutboxEvent.aggregate_id == UUID(booking_id)))
            )
            assert len(events) == 2
            connection = await aio_pika.connect(os.environ["RABBITMQ_URL"], timeout=5)
            async with connection:
                channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
                exchange = await topology(channel)
                for event in events:
                    body = await envelope(db, event)
                    for _ in range(2):
                        await exchange.publish(
                            aio_pika.Message(
                                body=json.dumps(body).encode(),
                                message_id=str(event.id),
                                correlation_id=body["correlation_id"],
                                type=event.event_type,
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=event.event_type,
                            timeout=5,
                        )
        await asyncio.sleep(3)
        await mail(mailpit, booking_id, "Бронь подтверждена")
        await mail(mailpit, booking_id, "Бронь отменена")
    elif phase == "smtp_down":
        start = datetime.fromisoformat(saved["slot"]["start_at"]) + timedelta(days=1)
        slot = {
            "space_id": "D-15",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        }
        response = await api.post("/api/v1/bookings", json=slot, headers={"Idempotency-Key": uuid4().hex})
        assert response.status_code == 201 and response.json()["status"] == "confirmed"
        await published(database, response.json()["id"], True)
        saved["smtp_booking"] = response.json()
        MARKER.write_text(json.dumps(saved), encoding="utf-8")
    else:
        await mail(mailpit, saved["smtp_booking"]["id"], "Бронь подтверждена")
        records = (await api.get("/api/v1/bookings/me")).json()["items"]
        assert (
            next(row for row in records if row["id"] == saved["smtp_booking"]["id"])["status"] == "confirmed"
        )
