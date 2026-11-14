from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    full_name: Mapped[str]
    job_title: Mapped[str]
    department: Mapped[str]
    avatar_url: Mapped[str | None]
    fictional: Mapped[bool] = mapped_column(default=True)


class DemoAccount(Base):
    __tablename__ = "demo_accounts"
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    csrf_token: Mapped[str]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Office(Base):
    __tablename__ = "offices"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class Floor(Base):
    __tablename__ = "floors"
    id: Mapped[str] = mapped_column(primary_key=True)
    office_id: Mapped[str] = mapped_column(ForeignKey("offices.id"))
    number: Mapped[int]
    name: Mapped[str]


class Space(Base):
    __tablename__ = "spaces"
    id: Mapped[str] = mapped_column(primary_key=True)
    floor_id: Mapped[str] = mapped_column(ForeignKey("floors.id"))
    kind: Mapped[str]
    desk_mode: Mapped[str | None]
    capacity: Mapped[int]
    zone: Mapped[str]
    layout: Mapped[dict] = mapped_column(JSON)


class PermanentAssignment(Base):
    __tablename__ = "permanent_assignments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"))
    space_id: Mapped[str] = mapped_column(ForeignKey("spaces.id"))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default="confirmed")
    idempotency_key: Mapped[str]
    request_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aggregate_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"))
    event_type: Mapped[str]
    schema_version: Mapped[int] = mapped_column(default=1)
    payload: Mapped[dict] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
