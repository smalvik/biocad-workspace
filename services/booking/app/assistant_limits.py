from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text

from app.auth import DB, Writer
from app.config import get_settings
from app.errors import ApiError
from app.models import Booking
from app.schemas import BookingRequest, BookingView

router = APIRouter(prefix="/api/v1/internal/assistant", include_in_schema=False)
# At most 32768 input tokens at $1/M + 768 output at $3/M, with conservative margin.
# The model client also limits serialized input size and provider prices. No refunds
# on unknown provider outcomes: a lost response must not allow exceeding the cap.
RESERVATION_MICRO_USD = 50_000


def internal_only(request: Request):
    if request.scope.get("extensions", {}).get("biocad.rpc") is not True:
        raise ApiError(403, "INTERNAL_ONLY", "Внутренний маршрут недоступен через браузер")


@router.post("/authorize")
async def authorize(request: Request, db: DB, user: Writer):
    internal_only(request)
    minute = datetime.now(UTC).replace(second=0, microsecond=0)
    await db.execute(
        text("DELETE FROM assistant_rate_windows WHERE minute_at < :old"), {"old": minute - timedelta(days=1)}
    )
    allowed = await db.scalar(
        text("""
        INSERT INTO assistant_rate_windows (employee_id, minute_at, requests)
        VALUES (:user, :minute, 1)
        ON CONFLICT (employee_id, minute_at) DO UPDATE
        SET requests = assistant_rate_windows.requests + 1
        WHERE assistant_rate_windows.requests < :maximum
        RETURNING requests
    """),
        {"user": user.employee.id, "minute": minute, "maximum": get_settings().assistant_requests_per_minute},
    )
    if allowed is None:
        raise ApiError(
            429, "AI_RATE_LIMIT", "Слишком много AI-запросов. Подождите минуту или используйте форму."
        )
    await db.commit()
    return {"employee_id": user.employee.id, "fictional": user.employee.fictional}


class ReserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    free_only: bool = False


class ReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selection: BookingRequest
    idempotency_key: str


@router.post("/replay")
async def replay_confirmation(body: ReplayRequest, request: Request, db: DB, user: Writer):
    internal_only(request)
    existing = await db.scalar(
        select(Booking).where(
            Booking.employee_id == user.employee.id, Booking.idempotency_key == body.idempotency_key
        )
    )
    if existing is None:
        return {"booking": None}
    if existing.request_hash != body.selection.fingerprint():
        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Этот ключ использован для другого подтверждения")
    return {"booking": BookingView.model_validate(existing).model_dump(mode="json")}


@router.post("/reserve")
async def reserve(body: ReserveRequest, request: Request, db: DB, user: Writer):
    internal_only(request)
    settings = get_settings()
    if settings.assistant_free_only:
        if not body.free_only:
            raise ApiError(403, "AI_FREE_ONLY", "Разрешены только бесплатные модели")
        # No monetary reservation for zero-price inference. The durable user rate
        # window is still checked before the chat; Assistant enforces price=0.
        return {"reserved_micro_usd": 0, "replayed": False, "free_only": True}
    if body.free_only:
        raise ApiError(403, "AI_CONFIG_MISMATCH", "Проверьте бесплатный режим сервисов")
    limit = int(Decimal(str(settings.assistant_budget_usd)) * 1_000_000)
    if limit < RESERVATION_MICRO_USD:
        raise ApiError(429, "AI_BUDGET_EXHAUSTED", "Демо-лимит AI исчерпан. Бронируйте через обычную форму.")
    await db.execute(
        text("INSERT INTO assistant_budgets (epoch) VALUES (:epoch) ON CONFLICT DO NOTHING"),
        {"epoch": settings.assistant_budget_epoch},
    )
    inserted = await db.scalar(
        text("""
        INSERT INTO assistant_spend_reservations (id, employee_id, epoch, reserved_micro_usd)
        VALUES (:id, :user, :epoch, :amount) ON CONFLICT DO NOTHING RETURNING id
    """),
        {
            "id": body.request_id,
            "user": user.employee.id,
            "epoch": settings.assistant_budget_epoch,
            "amount": RESERVATION_MICRO_USD,
        },
    )
    if inserted is None:
        owner = await db.scalar(
            text("SELECT employee_id FROM assistant_spend_reservations WHERE id=:id"), {"id": body.request_id}
        )
        if owner != user.employee.id:
            raise ApiError(409, "AI_REQUEST_CONFLICT", "Запрос принадлежит другой операции")
        await db.commit()
        return {"reserved_micro_usd": RESERVATION_MICRO_USD, "replayed": True}
    spent = await db.scalar(
        text("""
        UPDATE assistant_budgets SET reserved_micro_usd = reserved_micro_usd + :amount
        WHERE epoch=:epoch AND reserved_micro_usd + :amount <= :maximum RETURNING reserved_micro_usd
    """),
        {"epoch": settings.assistant_budget_epoch, "amount": RESERVATION_MICRO_USD, "maximum": limit},
    )
    if spent is None:
        await db.rollback()
        raise ApiError(429, "AI_BUDGET_EXHAUSTED", "Демо-лимит AI исчерпан. Бронируйте через обычную форму.")
    await db.commit()
    return {"reserved_micro_usd": RESERVATION_MICRO_USD, "replayed": False}
