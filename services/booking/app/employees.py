"""Authenticated fictional directory and selected-period reservations/assignments."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.auth import DB, User
from app.errors import ApiError
from app.models import Booking, Employee, Floor, Office, PermanentAssignment, Space
from app.people import person_public
from app.schemas import OffsetDateTime

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


def period(start_at: datetime, end_at: datetime) -> tuple[datetime, datetime]:
    if start_at >= end_at:
        raise ApiError(422, "VALIDATION_ERROR", "Начало интервала должно быть раньше конца")
    return start_at.astimezone(UTC), end_at.astimezone(UTC)


async def locations(db, ids: list[str], start_at: datetime, end_at: datetime) -> dict[str, list]:
    """Two batch queries for the entire result set, independent of employee count.

    Authenticated demo users share the fictional Moscow office. Enterprise office ACL/SSO
    is outside this demo; this endpoint never accepts an identity to act as on writes.
    """
    result = {employee_id: [] for employee_id in ids}
    if not ids:
        return result

    def resource(space: Space, floor: Floor, office: Office) -> dict:
        return {
            "space_id": space.id,
            "space_kind": space.kind,
            "desk_mode": space.desk_mode,
            "floor_id": floor.id,
            "floor_number": floor.number,
            "floor_name": floor.name,
            "office_id": office.id,
            "office_name": office.name,
        }

    assignments = await db.execute(
        select(PermanentAssignment, Space, Floor, Office)
        .join(Space, Space.id == PermanentAssignment.space_id)
        .join(Floor, Floor.id == Space.floor_id)
        .join(Office, Office.id == Floor.office_id)
        .where(
            PermanentAssignment.employee_id.in_(ids),
            PermanentAssignment.valid_from < end_at,
            or_(PermanentAssignment.valid_to.is_(None), PermanentAssignment.valid_to > start_at),
        )
        .order_by(PermanentAssignment.valid_from, Space.id)
    )
    for assignment, space, floor, office in assignments:
        result[assignment.employee_id].append(
            {
                **resource(space, floor, office),
                "relation": "assignment",
                "valid_from": assignment.valid_from,
                "valid_to": assignment.valid_to,
            }
        )
    reservations = await db.execute(
        select(Booking, Space, Floor, Office)
        .join(Space, Space.id == Booking.space_id)
        .join(Floor, Floor.id == Space.floor_id)
        .join(Office, Office.id == Floor.office_id)
        .where(
            Booking.employee_id.in_(ids),
            Booking.status == "confirmed",
            Booking.start_at < end_at,
            Booking.end_at > start_at,
        )
        .order_by(Booking.start_at, Space.id, Booking.id)
    )
    for booking, space, floor, office in reservations:
        result[booking.employee_id].append(
            {
                **resource(space, floor, office),
                "relation": "reservation",
                "booking_id": booking.id,
                "start_at": booking.start_at,
                "end_at": booking.end_at,
            }
        )
    return result


@router.get("")
async def search(
    db: DB,
    user: User,
    q: Annotated[str, Query(max_length=80)] = "",
    start_at: Annotated[OffsetDateTime | None, Query(alias="from")] = None,
    end_at: Annotated[OffsetDateTime | None, Query(alias="to")] = None,
):
    if (start_at is None) != (end_at is None):
        raise ApiError(422, "VALIDATION_ERROR", "Укажите начало и конец выбранного интервала")
    if start_at is not None and end_at is not None:
        start_at, end_at = period(start_at, end_at)
    query = select(Employee)
    if term := q.strip():
        # Treat SQL LIKE metacharacters as literal search characters, not wildcards.
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(
                Employee.full_name.ilike(f"%{term}%", escape="\\"),
                Employee.department.ilike(f"%{term}%", escape="\\"),
            )
        )
    people = list(await db.scalars(query.order_by(func.lower(Employee.full_name), Employee.id).limit(50)))
    by_person = (
        await locations(db, [p.id for p in people], start_at, end_at)
        if start_at is not None and end_at is not None
        else None
    )
    return {
        "items": [
            {**person_public(p), "locations": by_person[p.id] if by_person is not None else None}
            for p in people
        ],
        "from": start_at,
        "to": end_at,
        "snapshot_at": datetime.now(UTC),
    }


@router.get("/{employee_id}/location")
async def location(
    employee_id: str,
    start_at: Annotated[OffsetDateTime, Query(alias="from")],
    end_at: Annotated[OffsetDateTime, Query(alias="to")],
    db: DB,
    user: User,
):
    start_at, end_at = period(start_at, end_at)
    employee = await db.get(Employee, employee_id)
    if employee is None:
        raise ApiError(404, "EMPLOYEE_NOT_FOUND", "Сотрудник не найден")
    by_person = await locations(db, [employee_id], start_at, end_at)
    return {
        "employee": person_public(employee),
        "locations": by_person[employee_id],
        "from": start_at,
        "to": end_at,
        "snapshot_at": datetime.now(UTC),
    }
