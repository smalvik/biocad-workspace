"""Explicit, idempotent fictional seed; never truncates tables or overwrites user bookings."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.config import get_settings
from app.db import dispose, get_engine
from app.models import Booking, DemoAccount, Employee, Floor, Office, OutboxEvent, PermanentAssignment, Space
from app.schemas import BookingRequest


async def seed():
    settings = get_settings()
    if not settings.seed_demo_data:
        print("Demo seed disabled")
        return
    fixture_path = Path("data/demo_fixture.json")
    if not fixture_path.exists():
        fixture_path = Path(__file__).resolve().parents[3] / "docs/data/demo_fixture.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    async with AsyncSession(get_engine(), expire_on_commit=False) as db, db.begin():

        async def add(model, **values):
            await db.execute(insert(model).values(**values).on_conflict_do_nothing())

        await add(Office, id="moscow-a", name=fixture["office"])
        for number in (2, 3):
            await add(Floor, id=f"floor-{number}", office_id="moscow-a", number=number, name=f"Этаж {number}")
        for item in fixture["employees"]:
            await add(
                Employee,
                id=item["id"],
                full_name=item["full_name"],
                job_title=item["job_title"],
                department=item["department"],
                avatar_url=None,
                fictional=True,
            )
            if await db.get(DemoAccount, item["id"]) is None:
                await add(
                    DemoAccount,
                    employee_id=item["id"],
                    username=item["id"],
                    password_hash=hash_password(settings.demo_password),
                )
        for item in fixture["spaces"]:
            await add(
                Space,
                id=item["id"],
                floor_id=f"floor-{item['floor_number']}",
                kind=item["kind"],
                desk_mode=item["desk_mode"],
                capacity=item.get("capacity", 1),
                zone=item["zone"],
                layout={key: item[key] for key in ("x", "y") if key in item},
            )
        for item in fixture["permanent_assignments"]:
            await add(
                PermanentAssignment,
                id=uuid5(NAMESPACE_URL, "assignment:" + item["space_id"]),
                space_id=item["space_id"],
                employee_id=item["employee_id"],
                valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                valid_to=None,
            )
        for item in fixture["bookings"]:
            request = BookingRequest(
                space_id=item["space_id"], start_at=item["start_at"], end_at=item["end_at"]
            )
            values = dict(
                id=uuid5(NAMESPACE_URL, item["id"]),
                employee_id=item["employee_id"],
                **request.model_dump(),
                status="confirmed",
                request_hash=request.fingerprint(),
                idempotency_key="seed:" + item["id"],
                created_at=datetime(2026, 11, 14, tzinfo=UTC),
            )
            created_id = await db.scalar(
                insert(Booking).values(**values).on_conflict_do_nothing().returning(Booking.id)
            )
            if created_id is not None:
                event_id = uuid5(NAMESPACE_URL, "seed-event:" + item["id"])
                occurred = datetime(2026, 11, 14, tzinfo=UTC)
                await add(
                    OutboxEvent,
                    id=event_id,
                    aggregate_id=created_id,
                    event_type="booking.created.v1",
                    schema_version=1,
                    occurred_at=occurred,
                    payload={
                        "event_id": str(event_id),
                        "booking_id": str(created_id),
                        "schema_version": 1,
                        "occurred_at": occurred.isoformat(),
                        "correlation_id": str(uuid5(NAMESPACE_URL, "fictional-seed")),
                        "employee_id": item["employee_id"],
                        "space_id": item["space_id"],
                        "start_at": request.start_at.isoformat(),
                        "end_at": request.end_at.isoformat(),
                        "status": "confirmed",
                    },
                )
        # Validate the canonical dedicated-desk scenario; do not silently accept fixture drift.
        anna = await db.scalar(select(PermanentAssignment).where(PermanentAssignment.space_id == "D-07"))
        assert anna is not None and anna.employee_id == "e01"
    print("Fictional demo seed applied (existing records preserved)")
    await dispose()


if __name__ == "__main__":
    asyncio.run(seed())
