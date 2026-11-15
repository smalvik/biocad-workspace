from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth import DB, User, Writer
from app.errors import ApiError
from app.models import Booking, Employee, Floor, Office, OutboxEvent, PermanentAssignment, Space
from app.outbox import notification_snapshot
from app.people import person_public
from app.schemas import BookingRequest, BookingView, OffsetDateTime

router = APIRouter(prefix="/api/v1", tags=["booking"])
Key = Annotated[str, Header(alias="Idempotency-Key", pattern=r"^[A-Za-z0-9._:-]{1,128}$")]


async def outbox(db, booking: Booking, event_type: str, request_id: str) -> OutboxEvent:
    event_id, now = uuid4(), datetime.now(UTC)
    return OutboxEvent(
        id=event_id,
        aggregate_id=booking.id,
        event_type=event_type,
        occurred_at=now,
        payload={
            "event_id": str(event_id),
            "schema_version": 1,
            "occurred_at": now.isoformat(),
            "correlation_id": request_id,
            "booking_id": str(booking.id),
            "employee_id": booking.employee_id,
            "space_id": booking.space_id,
            "start_at": booking.start_at.isoformat(),
            "end_at": booking.end_at.isoformat(),
            "status": booking.status,
            "type": event_type,
            "notification": await notification_snapshot(db, booking.employee_id, booking.space_id),
        },
    )


def replay(existing: Booking, fingerprint: str) -> BookingView:
    if existing.request_hash != fingerprint:
        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Этот ключ использован для другого подтверждения")
    return BookingView.model_validate(existing)


@router.post("/bookings", response_model=BookingView, status_code=201)
async def create_booking(
    body: BookingRequest, request: Request, response: Response, db: DB, user: Writer, idempotency_key: Key
):
    employee_id = user.employee.id
    fingerprint = body.fingerprint()
    lookup = select(Booking).where(
        Booking.employee_id == employee_id,
        Booking.idempotency_key == idempotency_key,
    )
    existing = await db.scalar(lookup)
    # Replays remain valid even when the original interval is now past/cancelled.
    if existing:
        response.status_code = 200
        return replay(existing, fingerprint)
    space = await db.get(Space, body.space_id)
    if space is None:
        raise ApiError(404, "SPACE_NOT_FOUND", "Ресурс не найден")
    if space.desk_mode == "DEDICATED":
        raise ApiError(409, "SPACE_DEDICATED", "Постоянное место недоступно для бронирования")
    if body.start_at <= datetime.now(UTC):
        raise ApiError(422, "VALIDATION_ERROR", "Начало бронирования должно быть в будущем")
    booking = Booking(
        id=uuid4(),
        employee_id=employee_id,
        idempotency_key=idempotency_key,
        request_hash=fingerprint,
        **body.model_dump(),
    )
    db.add(booking)
    try:
        # PostgreSQL, rather than a preceding availability SELECT, decides the winner.
        await db.flush()
        db.add(await outbox(db, booking, "booking.created.v1", request.state.request_id))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        sqlstate = getattr(exc.orig, "sqlstate", None)
        if sqlstate not in {"23P01", "23505"}:
            raise
        # A concurrent request with the same key may hit either exclusion or uniqueness.
        existing = await db.scalar(lookup)
        if existing:
            response.status_code = 200
            return replay(existing, fingerprint)
        if sqlstate == "23P01":
            raise ApiError(409, "BOOKING_CONFLICT", "Ресурс уже занят на выбранный интервал") from None
        raise
    return BookingView.model_validate(booking)


@router.get("/bookings/me")
async def my_bookings(db: DB, user: User):
    rows = await db.execute(
        select(Booking, Space, Floor, Office)
        .join(Space, Space.id == Booking.space_id)
        .join(Floor, Floor.id == Space.floor_id)
        .join(Office, Office.id == Floor.office_id)
        .where(Booking.employee_id == user.employee.id)
        .order_by(Booking.start_at, Booking.id)
    )
    return {
        "items": [
            {
                **BookingView.model_validate(booking).model_dump(mode="json"),
                "resource": {
                    "kind": space.kind,
                    "floor_id": floor.id,
                    "floor_name": floor.name,
                    "office_name": office.name,
                },
            }
            for booking, space, floor, office in rows
        ]
    }


@router.post("/bookings/{booking_id}/cancel", response_model=BookingView)
async def cancel_booking(booking_id: UUID, request: Request, db: DB, user: Writer):
    employee_id = user.employee.id
    booking = await db.scalar(select(Booking).where(Booking.id == booking_id).with_for_update())
    if booking is None:
        raise ApiError(404, "BOOKING_NOT_FOUND", "Бронь не найдена")
    if booking.employee_id != employee_id:
        raise ApiError(403, "BOOKING_FORBIDDEN", "Можно отменить только собственную бронь")
    if booking.status == "confirmed":
        booking.status = "cancelled"
        booking.cancelled_at = datetime.now(UTC)
        db.add(await outbox(db, booking, "booking.cancelled.v1", request.state.request_id))
        await db.commit()
    return BookingView.model_validate(booking)


@router.get("/floors")
async def floors(db: DB, user: User):
    rows = await db.execute(
        select(Floor, Office.name).join(Office, Office.id == Floor.office_id).order_by(Floor.number)
    )
    return {
        "items": [
            {
                "id": row.id,
                "number": row.number,
                "name": row.name,
                "office_id": row.office_id,
                "office_name": office_name,
                "plan": row.plan,
            }
            for row, office_name in rows
        ],
        "timezone": "Europe/Moscow",
    }


async def snapshot(
    floor_id: str, start_at: datetime, end_at: datetime, db, employee_id: str, space_id: str | None = None
):
    if start_at >= end_at:
        raise ApiError(422, "VALIDATION_ERROR", "Начало интервала должно быть раньше конца")
    start_at, end_at = start_at.astimezone(UTC), end_at.astimezone(UTC)
    if await db.get(Floor, floor_id) is None:
        raise ApiError(404, "FLOOR_NOT_FOUND", "Этаж не найден")
    query = select(Space).where(Space.floor_id == floor_id)
    if space_id:
        query = query.where(Space.id == space_id)
    spaces = list(await db.scalars(query.order_by(Space.id)))
    ids = [space.id for space in spaces]
    reservations = list(
        await db.scalars(
            select(Booking)
            .where(
                Booking.space_id.in_(ids),
                Booking.status == "confirmed",
                Booking.start_at < end_at,
                Booking.end_at > start_at,
            )
            .order_by(Booking.start_at, Booking.id)
        )
    )
    assignments = list(
        await db.scalars(
            select(PermanentAssignment)
            .where(
                PermanentAssignment.space_id.in_(ids),
                PermanentAssignment.valid_from < end_at,
                (PermanentAssignment.valid_to.is_(None)) | (PermanentAssignment.valid_to > start_at),
            )
            .order_by(PermanentAssignment.valid_from)
        )
    )
    employee_ids = {row.employee_id for row in [*reservations, *assignments]}
    people = {
        person.id: person_public(person)
        for person in await db.scalars(select(Employee).where(Employee.id.in_(employee_ids)))
    }
    # PostgreSQL DISTINCT ON keeps one next reservation per resource in a single query.
    upcoming = {
        row.space_id: {"start_at": row.start_at, "end_at": row.end_at}
        for row in await db.scalars(
            select(Booking)
            .where(Booking.space_id.in_(ids), Booking.status == "confirmed", Booking.start_at >= end_at)
            .distinct(Booking.space_id)
            .order_by(Booking.space_id, Booking.start_at, Booking.id)
        )
    }
    items = []
    for space in spaces:
        periods = [row for row in reservations if row.space_id == space.id]
        covered = sum(
            (min(row.end_at, end_at) - max(row.start_at, start_at)).total_seconds() for row in periods
        )
        items.append(
            {
                "id": space.id,
                "floor_id": space.floor_id,
                "kind": space.kind,
                "desk_mode": space.desk_mode,
                "capacity": space.capacity,
                "zone": space.zone,
                "layout": space.layout,
                "is_available_for_full_interval": space.desk_mode != "DEDICATED" and not periods,
                "is_partial": bool(periods) and covered < (end_at - start_at).total_seconds(),
                "occupancy_kind": (
                    "dedicated"
                    if space.desk_mode == "DEDICATED"
                    else "multiple"
                    if len(periods) > 1
                    else "reserved"
                    if periods
                    else "free"
                ),
                "next_reservation": upcoming.get(space.id),
                "reservations": [
                    {
                        "booking_id": row.id,
                        "employee_id": row.employee_id,
                        "start_at": row.start_at,
                        "end_at": row.end_at,
                        "is_mine": row.employee_id == employee_id,
                        "person_public": people.get(row.employee_id),
                    }
                    for row in periods
                ],
                "assignments": [
                    {
                        "employee_id": row.employee_id,
                        "valid_from": row.valid_from,
                        "valid_to": row.valid_to,
                        "person_public": people.get(row.employee_id),
                    }
                    for row in assignments
                    if row.space_id == space.id
                ],
            }
        )
    return {
        "floor_id": floor_id,
        "from": start_at,
        "to": end_at,
        "snapshot_at": datetime.now(UTC),
        "items": items,
    }


@router.get("/floors/{floor_id}/occupancy")
@router.get("/spaces")
async def spaces(
    floor_id: str,
    start_at: Annotated[OffsetDateTime, Query(alias="from")],
    end_at: Annotated[OffsetDateTime, Query(alias="to")],
    db: DB,
    user: User,
):
    return await snapshot(floor_id, start_at, end_at, db, user.employee.id)


@router.get("/spaces/{space_id}")
async def space_details(
    space_id: str,
    start_at: Annotated[OffsetDateTime, Query(alias="from")],
    end_at: Annotated[OffsetDateTime, Query(alias="to")],
    db: DB,
    user: User,
):
    space = await db.get(Space, space_id)
    if space is None:
        raise ApiError(404, "SPACE_NOT_FOUND", "Ресурс не найден")
    result = await snapshot(space.floor_id, start_at, end_at, db, user.employee.id, space_id)
    return {
        "from": result["from"],
        "to": result["to"],
        "snapshot_at": result["snapshot_at"],
        "space": result["items"][0],
    }
