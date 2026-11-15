import os
from uuid import uuid4

import allure
import pytest

from app.events import Event


@pytest.fixture(autouse=True)
def metadata():
    for name, value in {
        "run_type": os.getenv("RUN_TYPE", "regression"),
        "environment": os.getenv("REPORT_ENV", "local"),
        "git_sha": os.getenv("GIT_SHA", "dev"),
        "release_version": os.getenv("RELEASE_VERSION", "unreleased"),
    }.items():
        allure.dynamic.label(name, value)


@pytest.fixture
def event():
    return Event.model_validate(
        {
            "event_id": str(uuid4()),
            "booking_id": str(uuid4()),
            "correlation_id": str(uuid4()),
            "schema_version": 1,
            "type": "booking.created.v1",
            "employee_id": "e01",
            "space_id": "D-15",
            "occurred_at": "2026-11-15T12:00:00Z",
            "start_at": "2026-11-18T07:00:00Z",
            "end_at": "2026-11-18T09:00:00Z",
            "status": "confirmed",
            "notification": {
                "recipient": "e01@example.test",
                "employee_name": "Анна Смирнова",
                "fictional": True,
                "kind": "DESK",
                "office_name": "Москва, Корпус А",
                "office_address": "Вымышленный адрес, 1",
                "floor_name": "Этаж 2",
            },
        }
    )
