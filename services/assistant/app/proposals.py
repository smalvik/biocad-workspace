import re
from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.errors import AssistantError


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    space_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    start_at: datetime
    end_at: datetime

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def explicit_offset(cls, value):
        if isinstance(value, str) and ("T" not in value or not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", value)):
            raise ValueError("Use ISO 8601 with an explicit UTC offset")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timezone offset is required")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def interval(self):
        zone = ZoneInfo("Europe/Moscow")
        if self.start_at >= self.end_at:
            raise ValueError("Start must precede end")
        if self.start_at.astimezone(zone).date() != self.end_at.astimezone(zone).date():
            raise ValueError("For the demo, choose an interval within one Moscow calendar day")
        return self


def signer(secret: str):
    return URLSafeTimedSerializer(secret, salt="biocad-proposal-v1")


async def propose(rpc, user_id: str, secret: str, selection: Selection):
    if selection.start_at <= datetime.now(UTC):
        raise AssistantError(422, "VALIDATION_ERROR", "Выберите время в будущем")
    data = await rpc.call(
        "get_space_details",
        {
            "space_id": selection.space_id,
            "from": selection.start_at.isoformat(),
            "to": selection.end_at.isoformat(),
        },
    )
    space = data["space"]
    if space["desk_mode"] == "DEDICATED" or not space["is_available_for_full_interval"]:
        raise AssistantError(409, "BOOKING_CONFLICT", "Место недоступно на весь интервал. Уточните запрос.")
    payload = selection.model_dump(mode="json")
    token = signer(secret).dumps({"user_id": user_id, "selection": payload, "proposal_id": str(uuid4())})
    return {
        "token": token,
        "selection": payload,
        "space": space,
        "floor": data["floor"],
        "snapshot_at": data["snapshot_at"],
        "expires_in_seconds": 600,
    }


def verified(secret: str, token: str, user_id: str, max_age: int = 600) -> Selection:
    try:
        data = signer(secret).loads(token, max_age=max_age)
        if data["user_id"] != user_id:
            raise ValueError("owner")
        return Selection.model_validate(data["selection"])
    except (BadSignature, ValueError, TypeError, KeyError):
        raise AssistantError(
            409,
            "PROPOSAL_EXPIRED",
            "Предложение истекло или недействительно. Повторите поиск; время не изменено.",
        ) from None
