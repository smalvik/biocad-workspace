"""Explicitly invoked before/after Docker restarts; not part of default pytest collection."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import allure
import pytest

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("persistence")]


@pytest.mark.parametrize("phase", [os.environ.get("PERSISTENCE_PHASE", "unset")])
async def test_booking_survives_service_and_postgres_restart(api, database, phase):
    marker = Path("/allure-results/persistence-check.json")
    if phase == "prepare":
        start = datetime.now(UTC) + timedelta(days=30)
        body = {
            "space_id": "M-03",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        }
        key = uuid4().hex
        response = await api.post("/api/v1/bookings", json=body, headers={"Idempotency-Key": key})
        assert response.status_code == 201, response.text
        # No authentication cookies, CSRF or personal information are written to artifacts.
        marker.write_text(
            json.dumps({"payload": body, "key": key, "booking": response.json()}), encoding="utf-8"
        )
    else:
        assert phase == "verify", "Set PERSISTENCE_PHASE=prepare|verify"
        previous = json.loads(marker.read_text(encoding="utf-8"))
        ready = await api.get("/api/v1/readyz")
        assert ready.status_code == 200
        rows = (await api.get("/api/v1/bookings/me")).json()["items"]
        assert previous["booking"] in rows
        replay = await api.post(
            "/api/v1/bookings", json=previous["payload"], headers={"Idempotency-Key": previous["key"]}
        )
        assert replay.status_code == 200
        assert replay.json() == previous["booking"]
