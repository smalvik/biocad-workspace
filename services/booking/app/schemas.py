import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def explicit_offset(value):
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or "T" not in value or not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", value):
        raise ValueError("Use ISO 8601 with an explicit UTC offset")
    return value


OffsetDateTime = Annotated[AwareDatetime, BeforeValidator(explicit_offset)]


class BookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    space_id: str = Field(min_length=1, max_length=64)
    start_at: OffsetDateTime
    end_at: OffsetDateTime

    @field_validator("start_at", "end_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be earlier than end_at")
        return self

    def fingerprint(self) -> str:
        body = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(body.encode()).hexdigest()


class BookingView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employee_id: str
    space_id: str
    start_at: datetime
    end_at: datetime
    status: str
    created_at: datetime
    cancelled_at: datetime | None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
