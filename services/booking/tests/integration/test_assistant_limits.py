import asyncio
from uuid import uuid4

import allure
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app import assistant_limits, db
from app.config import get_settings
from app.main import create_app

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("durable AI limits")]


@pytest.fixture
async def internal(api, database, monkeypatch):
    settings = get_settings().model_copy(
        update={
            "assistant_budget_usd": 0.1,
            "assistant_free_only": False,
            "assistant_budget_epoch": "test-" + uuid4().hex,
            "assistant_requests_per_minute": 3,
        }
    )
    monkeypatch.setattr(assistant_limits, "get_settings", lambda: settings)
    app = create_app()

    async def trusted(scope, receive, send):
        scope.setdefault("extensions", {})["biocad.rpc"] = True
        await app(scope, receive, send)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=trusted),
            base_url="http://internal",
            headers={
                "Cookie": "biocad_session=" + api.cookies.get("biocad_session"),
                "X-CSRF-Token": api.headers["X-CSRF-Token"],
            },
        ) as client:
            yield client, settings, database
    finally:
        await db.dispose()


async def test_concurrent_reservations_cannot_exceed_durable_cap_and_replays_do_not_charge_twice(internal):
    client, settings, database = internal
    ids = [str(uuid4()) for _ in range(10)]
    responses = await asyncio.gather(
        *(client.post("/api/v1/internal/assistant/reserve", json={"request_id": id}) for id in ids)
    )
    assert sorted(r.status_code for r in responses) == [200, 200] + [429] * 8
    successful = next(id for id, response in zip(ids, responses, strict=True) if response.status_code == 200)
    repeated = await client.post("/api/v1/internal/assistant/reserve", json={"request_id": successful})
    assert repeated.status_code == 200 and repeated.json()["replayed"] is True
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT reserved_micro_usd FROM assistant_budgets WHERE epoch=:epoch"),
                {"epoch": settings.assistant_budget_epoch},
            )
            == 100000
        )
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM assistant_spend_reservations WHERE epoch=:epoch"),
                {"epoch": settings.assistant_budget_epoch},
            )
            == 2
        )
    await db.dispose()  # New connection pool/process state must not reset the persisted cap.
    exhausted = await client.post("/api/v1/internal/assistant/reserve", json={"request_id": str(uuid4())})
    assert exhausted.status_code == 429


async def test_rate_limit_is_shared_across_concurrent_requests_and_csrf_is_required(internal):
    client, _, database = internal
    # Isolated tests own this database. Clear only this demo user's current quota fixture.
    async with database.begin() as connection:
        await connection.execute(text("DELETE FROM assistant_rate_windows WHERE employee_id='e01'"))
    responses = await asyncio.gather(*(client.post("/api/v1/internal/assistant/authorize") for _ in range(6)))
    assert sorted(r.status_code for r in responses) == [200] * 3 + [429] * 3
    invalid = await client.post(
        "/api/v1/internal/assistant/reserve",
        json={"request_id": str(uuid4())},
        headers={"X-CSRF-Token": "invalid"},
    )
    assert invalid.status_code == 403


async def test_free_only_mode_works_with_zero_budget_and_rejects_paid_reservations(internal):
    client, settings, database = internal
    settings.assistant_free_only = True
    settings.assistant_budget_usd = 0
    free = await client.post(
        "/api/v1/internal/assistant/reserve", json={"request_id": str(uuid4()), "free_only": True}
    )
    assert free.status_code == 200 and free.json()["reserved_micro_usd"] == 0
    paid = await client.post("/api/v1/internal/assistant/reserve", json={"request_id": str(uuid4())})
    assert paid.status_code == 403 and paid.json()["error"]["code"] == "AI_FREE_ONLY"
    async with database.connect() as connection:
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM assistant_spend_reservations WHERE epoch=:epoch"),
                {"epoch": settings.assistant_budget_epoch},
            )
            == 0
        )
