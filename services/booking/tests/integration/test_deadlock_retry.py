"""Deterministic PostgreSQL SQLSTATE injection over real HTTP, in the isolated runner only."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import allure
import pytest
from sqlalchemy import text

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("booking-deadlock")]


@pytest.mark.parametrize(
    "failures,sqlstate,expected", [(1, "40P01", 201), (3, "40P01", 503), (1, "23514", 500)]
)
async def test_real_postgresql_error_retry_is_bounded_and_keeps_idempotency(
    api, database, failures, sqlstate, expected
):
    suffix = uuid4().hex
    name, key = "wb11_" + suffix, "deadlock-" + suffix
    # Separate each parameter case by whole days; random hour windows could overlap.
    day = 80 + failures + (4 if sqlstate != "40P01" else 0)
    start = (datetime.now(UTC) + timedelta(days=day)).replace(hour=9, minute=0, second=0, microsecond=0)
    body = {
        "space_id": "D-15",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
    }
    async with database.begin() as connection:
        # nextval is nontransactional: a rolled-back attempt still consumes one fault.
        await connection.execute(text(f"CREATE SEQUENCE {name}"))
        await connection.execute(
            text(f"""CREATE FUNCTION {name}() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.idempotency_key='{key}' AND nextval('{name}')<={failures} THEN
            RAISE EXCEPTION USING ERRCODE='{sqlstate}', MESSAGE='isolated retry probe';
          END IF; RETURN NEW; END $$""")
        )
        await connection.execute(
            text(f"CREATE TRIGGER {name} BEFORE INSERT ON bookings FOR EACH ROW EXECUTE FUNCTION {name}()")
        )
    try:
        response = await api.post(
            "/api/v1/bookings", json=body, headers={"Idempotency-Key": key, "Connection": "close"}
        )
        assert response.status_code == expected, response.text
        if expected == 503:
            assert response.json()["error"]["code"] == "BOOKING_RETRY"
        async with database.connect() as connection:
            attempts = await connection.scalar(text(f"SELECT last_value FROM {name}"))
            assert attempts == (2 if expected == 201 else failures)
            assert await connection.scalar(
                text("SELECT count(*) FROM bookings WHERE idempotency_key=:key"), {"key": key}
            ) == (1 if expected == 201 else 0)
    finally:
        async with database.begin() as connection:
            await connection.execute(text(f"DROP TRIGGER {name} ON bookings"))
            await connection.execute(text(f"DROP FUNCTION {name}()"))
            await connection.execute(text(f"DROP SEQUENCE {name}"))
    # Same key is safe both after an exhausted/unsupported failure and after success.
    replay = await api.post("/api/v1/bookings", json=body, headers={"Idempotency-Key": key})
    assert replay.status_code == (200 if expected == 201 else 201)
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM bookings WHERE idempotency_key=:key"), {"key": key}
            )
            == 1
        )
        assert (
            await connection.scalar(
                text("""SELECT count(*) FROM outbox_events o JOIN bookings b
            ON b.id=o.aggregate_id WHERE b.idempotency_key=:key"""),
                {"key": key},
            )
            == 1
        )
