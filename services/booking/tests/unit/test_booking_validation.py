from datetime import UTC, datetime

import allure
import pytest
from pydantic import ValidationError

from app.auth import hash_password, verify_password
from app.schemas import BookingRequest

pytestmark = [allure.suite("regression"), allure.feature("booking-validation")]

BASE = {"space_id": "D-02", "start_at": "2026-11-16T10:00:00+03:00", "end_at": "2026-11-16T11:00:00+03:00"}


@pytest.mark.parametrize(
    "change",
    [
        {"start_at": "2026-11-16T10:00:00"},
        {"end_at": "2026-11-16T11:00:00"},
        {"start_at": "2026-11-16T12:00:00+03:00"},
        {"end_at": "2026-11-16T10:00:00+03:00"},
        {"start_at": 1794812400},
        {"start_at": "1794812400"},
        {"employee_id": "e02"},
        {"status": "confirmed"},
        {"space_id": ""},
    ],
)
def test_rejects_ambiguous_periods_and_client_owned_fields(change):
    with pytest.raises(ValidationError):
        BookingRequest(**(BASE | change))


def test_offset_equivalent_requests_have_same_persistent_fingerprint():
    moscow = BookingRequest(**BASE)
    utc = BookingRequest(**(BASE | {"start_at": "2026-11-16T07:00:00Z", "end_at": "2026-11-16T08:00:00Z"}))
    assert moscow.fingerprint() == utc.fingerprint()
    assert moscow.start_at == datetime(2026, 11, 16, 7, tzinfo=UTC)
    assert moscow.start_at.tzinfo == UTC


def test_password_storage_is_salted_and_checks_password_without_reversibility():
    first, second = hash_password("fictional-demo"), hash_password("fictional-demo")
    assert first != second
    assert "fictional-demo" not in first
    assert verify_password("fictional-demo", first)
    assert not verify_password("wrong-password", first)
    assert not verify_password("fictional-demo", "malformed")


async def test_unauthenticated_resource_access_has_machine_readable_error(client):
    response = await client.get("/api/v1/floors")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert response.headers["X-Request-ID"]
