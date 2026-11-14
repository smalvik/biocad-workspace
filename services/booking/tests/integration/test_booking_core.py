import asyncio
from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import allure
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("booking-core")]


def slot(space_id="D-02"):
    # Unique, future windows without depending on the date of the fixed demo scenario.
    start = datetime.now(UTC) + timedelta(days=3, seconds=uuid4().int % 1000000)
    return {
        "space_id": space_id,
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
    }


async def book(api, body=None, key=None):
    return await api.post(
        "/api/v1/bookings", json=body or slot(), headers={"Idempotency-Key": key or uuid4().hex}
    )


async def test_twenty_concurrent_confirmations_have_one_winner(login_as, database):
    clients = [await login_as("e01"), await login_as("e02")]
    body = slot("M-01")
    barrier = asyncio.Event()

    async def compete(index):
        await barrier.wait()
        return await book(clients[index % 2], body)

    tasks = [asyncio.create_task(compete(index)) for index in range(20)]
    barrier.set()
    responses = await asyncio.gather(*tasks)
    assert Counter(item.status_code for item in responses) == {201: 1, 409: 19}, [r.text for r in responses]
    winner = next(item.json() for item in responses if item.status_code == 201)
    async with database.connect() as connection:
        count = await connection.scalar(
            text("SELECT count(*) FROM outbox_events WHERE aggregate_id=:id"), {"id": UUID(winner["id"])}
        )
        assert count == 1


async def test_parallel_retries_with_same_key_return_one_booking_and_event(api, database):
    body, key = slot("M-02"), uuid4().hex
    barrier = asyncio.Event()

    async def retry():
        await barrier.wait()
        return await book(api, body, key)

    tasks = [asyncio.create_task(retry()) for _ in range(20)]
    barrier.set()
    responses = await asyncio.gather(*tasks)
    assert Counter(r.status_code for r in responses) == {201: 1, 200: 19}, [r.text for r in responses]
    assert len({r.json()["id"] for r in responses}) == 1
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM bookings WHERE idempotency_key=:key"), {"key": key}
            )
            == 1
        )
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM outbox_events WHERE aggregate_id=:id"),
                {"id": UUID(responses[0].json()["id"])},
            )
            == 1
        )


async def test_adjacent_intervals_are_allowed_and_utc_is_returned(api):
    first = slot("D-04")
    second = {
        **first,
        "start_at": first["end_at"],
        "end_at": (datetime.fromisoformat(first["end_at"]) + timedelta(hours=1)).isoformat(),
    }
    created, adjacent = await book(api, first), await book(api, second)
    assert created.status_code == adjacent.status_code == 201
    assert datetime.fromisoformat(created.json()["end_at"].replace("Z", "+00:00")) == datetime.fromisoformat(
        second["start_at"]
    )
    assert created.json()["start_at"].endswith("Z") or created.json()["start_at"].endswith("+00:00")


async def test_idempotent_replay_after_cancel_does_not_rebook_and_changed_payload_conflicts(api, database):
    body, key = slot("D-06"), uuid4().hex
    created = await book(api, body, key)
    assert created.status_code == 201
    booking_id = created.json()["id"]
    cancelled = await api.post(f"/api/v1/bookings/{booking_id}/cancel")
    again = await api.post(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancelled.status_code == again.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    replay = await book(api, body, key)
    assert replay.status_code == 200 and replay.json()["id"] == booking_id
    assert replay.json()["status"] == "cancelled"
    changed = await book(api, {**body, "space_id": "D-08"}, key)
    assert changed.status_code == 409
    assert changed.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert (await book(api, body)).status_code == 201  # Cancelled rows no longer exclude.
    async with database.connect() as connection:
        types = list(
            (
                await connection.execute(
                    text("SELECT event_type FROM outbox_events WHERE aggregate_id=:id ORDER BY occurred_at"),
                    {"id": UUID(booking_id)},
                )
            ).scalars()
        )
        assert types == ["booking.created.v1", "booking.cancelled.v1"]


async def test_equivalent_offsets_replay_same_confirmation(api):
    body, key = slot("D-10"), uuid4().hex
    created = await book(api, body, key)
    moscow = {
        **body,
        **{
            name: datetime.fromisoformat(body[name]).astimezone(ZoneInfo("Europe/Moscow")).isoformat()
            for name in ("start_at", "end_at")
        },
    }
    replay = await book(api, moscow, key)
    assert created.status_code == 201 and replay.status_code == 200
    assert replay.json()["id"] == created.json()["id"]


async def test_foreign_cancellation_is_forbidden_and_own_list_is_scoped(login_as):
    owner, other = await login_as("e01"), await login_as("e02")
    created = await book(owner, slot("D-11"))
    assert created.status_code == 201
    booking_id = created.json()["id"]
    response = await other.post(f"/api/v1/bookings/{booking_id}/cancel")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "BOOKING_FORBIDDEN"
    mine = (await owner.get("/api/v1/bookings/me")).json()["items"]
    theirs = (await other.get("/api/v1/bookings/me")).json()["items"]
    assert booking_id in {row["id"] for row in mine}
    assert booking_id not in {row["id"] for row in theirs}
    assert all(row["employee_id"] == "e02" for row in theirs)


@pytest.mark.parametrize(
    ("change", "status", "code"),
    [
        ({"space_id": "D-07"}, 409, "SPACE_DEDICATED"),
        ({"space_id": "missing"}, 404, "SPACE_NOT_FOUND"),
        ({"start_at": "2026-11-16T10:00:00"}, 422, "VALIDATION_ERROR"),
        ({"start_at": "2020-01-01T00:00:00Z", "end_at": "2020-01-01T01:00:00Z"}, 422, "VALIDATION_ERROR"),
        ({"employee_id": "e02"}, 422, "VALIDATION_ERROR"),
    ],
)
async def test_server_rejects_invalid_confirmations_without_events(api, database, change, status, code):
    key = uuid4().hex
    response = await book(api, slot() | change, key)
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM bookings WHERE idempotency_key=:key"), {"key": key}
            )
            == 0
        )


async def test_session_cookie_csrf_and_logout(api, booking_base_url):
    assert (await api.get("/api/v1/auth/me")).status_code == 200
    async with httpx.AsyncClient(base_url=booking_base_url, cookies=api.cookies) as attacker:
        response = await book(attacker)
        assert response.status_code == 403 and response.json()["error"]["code"] == "CSRF_INVALID"
    cookie = api.cookies.get("biocad_session")
    logout = await api.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    async with httpx.AsyncClient(base_url=booking_base_url, cookies={"biocad_session": cookie}) as expired:
        assert (await expired.get("/api/v1/auth/me")).status_code == 401


async def test_bad_credentials_and_tampered_cookie_do_not_authenticate(booking_base_url):
    async with httpx.AsyncClient(base_url=booking_base_url) as client:
        response = await client.post("/api/v1/auth/login", json={"username": "e01", "password": "wrong"})
        assert response.status_code == 401 and "biocad_session" not in client.cookies
        client.cookies.set("biocad_session", "tampered")
        assert (await client.get("/api/v1/floors")).status_code == 401


async def test_seed_and_time_window_availability_match_canonical_scenario(api):
    floors = (await api.get("/api/v1/floors")).json()["items"]
    assert {row["number"] for row in floors} == {2, 3}
    for start, end, employees in [
        (10, 12, ["e03"]),
        (12, 14, []),
        (14, 16, ["e04"]),
        (9, 17, ["e03", "e04"]),
    ]:
        response = await api.get(
            "/api/v1/spaces",
            params={
                "floor_id": "floor-2",
                "from": f"2026-11-16T{start:02}:00:00+03:00",
                "to": f"2026-11-16T{end:02}:00:00+03:00",
            },
        )
        assert response.status_code == 200, response.text
        rows = {row["id"]: row for row in response.json()["items"]}
        assert len(rows) == 27
        assert [row["employee_id"] for row in rows["D-03"]["reservations"]] == employees
        assert rows["D-03"]["is_available_for_full_interval"] is (not employees)
        assert rows["D-07"]["desk_mode"] == "DEDICATED"
        assert rows["D-07"]["assignments"][0]["employee_id"] == "e01"
        assert rows["D-07"]["is_available_for_full_interval"] is False


async def test_database_itself_rejects_overlap_and_invalid_bounds(database):
    body = slot("D-15")
    start, end = datetime.fromisoformat(body["start_at"]), datetime.fromisoformat(body["end_at"])
    statement = text("""INSERT INTO bookings
        (id, employee_id, space_id, start_at, end_at, status, idempotency_key, request_hash)
        VALUES (:id, 'e01', 'D-15', :start, :end, 'confirmed', :key, :hash)""")

    async def insert(connection, first, last):
        await connection.execute(
            statement, {"id": uuid4(), "start": first, "end": last, "key": uuid4().hex, "hash": "0" * 64}
        )

    async with database.connect() as connection:
        await insert(connection, start, end)
        with pytest.raises(IntegrityError) as overlap:
            async with connection.begin_nested():
                await insert(connection, start + timedelta(minutes=1), end)
        assert overlap.value.orig.sqlstate == "23P01"
        with pytest.raises(IntegrityError) as invalid:
            async with connection.begin_nested():
                await insert(connection, end, start)
        assert invalid.value.orig.sqlstate == "23514"
        await insert(connection, end, end + timedelta(hours=1))
        # Direct writes are test-only and deliberately rolled back, including the adjacent row.
        await connection.rollback()


async def test_outbox_failure_rolls_back_booking_and_allows_clean_retry(api, database):
    correlation, key = str(uuid4()), uuid4().hex
    constraint = "wb02_outbox_" + uuid4().hex
    async with database.begin() as connection:
        await connection.execute(
            text(
                f"ALTER TABLE outbox_events ADD CONSTRAINT {constraint} "
                f"CHECK (payload->>'correlation_id' <> '{correlation}') NOT VALID"
            )
        )
    body = slot("D-16")
    try:
        response = await api.post(
            "/api/v1/bookings", json=body, headers={"Idempotency-Key": key, "X-Request-ID": correlation}
        )
        assert response.status_code == 500
        async with database.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM bookings WHERE idempotency_key=:key"), {"key": key}
                )
                == 0
            )
    finally:
        async with database.begin() as connection:
            await connection.execute(text(f"ALTER TABLE outbox_events DROP CONSTRAINT {constraint}"))
    assert (await book(api, body, key)).status_code == 201


async def test_same_key_is_scoped_to_employee(login_as):
    owner, other = await login_as("e01"), await login_as("e02")
    key = uuid4().hex
    first, second = await book(owner, slot("D-12"), key), await book(other, slot("D-13"), key)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": "invalid key"}, {"Idempotency-Key": "x" * 129}])
async def test_confirmation_requires_valid_idempotency_key(api, headers):
    response = await api.post("/api/v1/bookings", json=slot(), headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_login_cookie_is_httponly_and_not_returned_as_json(booking_base_url):
    async with httpx.AsyncClient(base_url=booking_base_url) as client:
        response = await client.post(
            "/api/v1/auth/login", json={"username": "e03", "password": "demo-workspace"}
        )
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/api" in cookie
        assert "password" not in response.json() and "session" not in response.json()
