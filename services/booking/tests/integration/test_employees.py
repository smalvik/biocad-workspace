from datetime import UTC, datetime, timedelta
from uuid import uuid4

import allure
import httpx
import pytest

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("employee-locations")]


def window(start="10:00", end="12:00", day="2026-11-16"):
    return {"from": f"{day}T{start}:00+03:00", "to": f"{day}T{end}:00+03:00"}


def assert_public(person):
    assert set(person) == {"id", "full_name", "job_title", "department", "avatar_url", "fictional"}
    assert person["fictional"] is True
    assert person["avatar_url"].startswith("/demo-avatars/v1/")


async def test_directory_location_and_canonical_occupancy_require_a_session(booking_base_url):
    async with httpx.AsyncClient(base_url=booking_base_url) as client:
        for path in (
            "/api/v1/employees",
            "/api/v1/employees/e01/location",
            "/api/v1/floors/floor-2/occupancy",
        ):
            response = await client.get(path, params=window())
            assert response.status_code == 401


async def test_directory_returns_twelve_safe_profiles_without_assuming_current_location(api):
    response = await api.get("/api/v1/employees")
    assert response.status_code == 200
    data = response.json()
    assert data["from"] is None and data["to"] is None
    assert {item["id"] for item in data["items"]} == {f"e{i:02}" for i in range(1, 13)}
    for item in data["items"]:
        assert item.pop("locations") is None
        assert_public(item)


async def test_cyrillic_case_insensitive_name_and_department_search_with_period(api):
    response = await api.get("/api/v1/employees", params={"q": "  сМиРнО  ", **window()})
    assert response.status_code == 200
    people = response.json()["items"]
    assert len(people) == 1
    anna = people[0]
    assert anna["id"] == "e01" and anna["full_name"] == "Анна Смирнова"
    assert anna["locations"][0]["space_id"] == "D-07"
    assert anna["locations"][0]["relation"] == "assignment"
    assert anna["locations"][0]["floor_id"] == "floor-2"
    department = await api.get("/api/v1/employees", params={"q": "r&d", **window()})
    found = department.json()["items"]
    assert found and all(p["department"].lower() == "r&d" for p in found)


@pytest.mark.parametrize("query", ["никогонет123", "%", "_", "\\"])
async def test_empty_search_and_literal_sql_wildcards(api, query):
    response = await api.get("/api/v1/employees", params={"q": query, **window()})
    assert response.status_code == 200 and response.json()["items"] == []


@pytest.mark.parametrize(
    "params",
    [
        {"q": "x" * 81},
        {"from": "2026-11-16T10:00:00+03:00"},
        {"from": "2026-11-16T10:00:00", "to": "2026-11-16T12:00:00"},
        window("14:00", "12:00"),
    ],
)
async def test_invalid_search_context_is_rejected_server_side(api, params):
    assert (await api.get("/api/v1/employees", params=params)).status_code == 422


@pytest.mark.parametrize(
    "start,end,owners,available",
    [
        ("10:00", "12:00", ["e03"], False),
        ("12:00", "14:00", [], True),
        ("14:00", "16:00", ["e04"], False),
        ("09:00", "17:00", ["e03", "e04"], False),
    ],
)
async def test_avatar_profiles_follow_exact_half_open_windows_and_full_timeline(
    api, start, end, owners, available
):
    response = await api.get("/api/v1/floors/floor-2/occupancy", params=window(start, end))
    assert response.status_code == 200
    spaces = {item["id"]: item for item in response.json()["items"]}
    desk = spaces["D-03"]
    assert desk["is_available_for_full_interval"] is available
    assert [r["person_public"]["id"] for r in desk["reservations"]] == owners
    for reservation in desk["reservations"]:
        assert_public(reservation["person_public"])
        assert reservation["person_public"]["id"] == reservation["employee_id"]
        assert datetime.fromisoformat(reservation["start_at"]) < datetime.fromisoformat(reservation["end_at"])
    if not owners:
        assert datetime.fromisoformat(desk["next_reservation"]["start_at"]) == datetime.fromisoformat(
            "2026-11-16T14:00:00+03:00"
        )
    if len(owners) > 1:
        assert desk["occupancy_kind"] == "multiple" and desk["is_partial"]
        assert [r["start_at"] for r in desk["reservations"]] == sorted(
            r["start_at"] for r in desk["reservations"]
        )
    dedicated = spaces["D-07"]
    assert dedicated["is_available_for_full_interval"] is False
    assert dedicated["assignments"][0]["person_public"]["id"] == "e01"


async def test_employee_location_does_not_invent_a_freedesk_between_adjacent_bookings(api):
    morning = await api.get("/api/v1/employees/e03/location", params=window())
    assert morning.status_code == 200
    assert morning.json()["locations"][0]["space_id"] == "D-03"
    gap = await api.get("/api/v1/employees/e03/location", params=window("12:00", "14:00"))
    assert gap.json()["locations"] == []
    other = await api.get("/api/v1/employees/e04/location", params=window("14:00", "16:00"))
    assert other.json()["locations"][0]["space_id"] == "D-03"


async def test_cross_floor_permanent_validity_and_unknown_employee(api):
    result = (await api.get("/api/v1/employees/e12/location", params=window())).json()
    assert [(p["space_id"], p["floor_id"]) for p in result["locations"]] == [("D-32", "floor-3")]
    historical = await api.get("/api/v1/employees/e01/location", params=window(day="2025-11-16"))
    assert historical.json()["locations"] == []
    assert (await api.get("/api/v1/employees/unknown/location", params=window())).status_code == 404


async def test_cancelled_own_reservation_disappears_from_location_and_avatar_snapshot(api):
    start = (datetime.now(UTC) + timedelta(days=90)).replace(microsecond=0)
    end = start + timedelta(hours=1)
    interval = {"from": start.isoformat(), "to": end.isoformat()}
    booking = await api.post(
        "/api/v1/bookings",
        json={"space_id": "D-02", "start_at": start.isoformat(), "end_at": end.isoformat()},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert booking.status_code == 201
    found = (await api.get("/api/v1/employees/e01/location", params=interval)).json()
    assert any(p.get("booking_id") == booking.json()["id"] for p in found["locations"])
    assert (await api.post(f"/api/v1/bookings/{booking.json()['id']}/cancel")).status_code == 200
    after = (await api.get("/api/v1/employees/e01/location", params=interval)).json()
    assert not any(p.get("booking_id") == booking.json()["id"] for p in after["locations"])
    snapshot = (await api.get("/api/v1/floors/floor-2/occupancy", params=interval)).json()
    desk = next(p for p in snapshot["items"] if p["id"] == "D-02")
    assert desk["is_available_for_full_interval"] and desk["reservations"] == []
