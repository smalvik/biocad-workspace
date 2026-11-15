from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Details(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    recipient: str = Field(max_length=254, pattern=r"^[A-Za-z0-9._+-]+@example\.test$")
    employee_name: str = Field(min_length=1, max_length=256)
    fictional: Literal[True]
    kind: Literal["DESK", "MEETING_ROOM"]
    office_name: str = Field(min_length=1, max_length=256)
    office_address: str = Field(min_length=1, max_length=512)
    floor_name: str = Field(min_length=1, max_length=128)


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    event_id: UUID
    schema_version: Literal[1]
    type: Literal["booking.created.v1", "booking.cancelled.v1"]
    occurred_at: AwareDatetime
    correlation_id: UUID
    booking_id: UUID
    employee_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    space_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    start_at: AwareDatetime
    end_at: AwareDatetime
    status: Literal["confirmed", "cancelled"]
    notification: Details

    @model_validator(mode="after")
    def coherent(self):
        expected = "confirmed" if self.type == "booking.created.v1" else "cancelled"
        if self.status != expected or self.end_at <= self.start_at:
            raise ValueError("Inconsistent booking event")
        return self
