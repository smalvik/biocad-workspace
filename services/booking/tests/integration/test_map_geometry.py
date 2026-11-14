import math

import allure
import pytest

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("floor-map")]


async def test_two_floors_have_real_geometry_and_resources(api):
    response = await api.get("/api/v1/floors")
    assert response.status_code == 200
    floors = response.json()["items"]
    assert len(floors) == 2
    counts = {}
    for floor in floors:
        assert floor["office_name"] == "Москва, Корпус А"
        plan = floor["plan"]
        assert plan["width"] > 0 and plan["height"] > 0
        assert {zone["kind"] for zone in plan["zones"]} >= {"kitchen", "bathroom", "recreation"}
        assert plan["walls"] and plan["windows"] and plan["doors"] and plan["hvac"]
        response = await api.get(
            "/api/v1/spaces",
            params={
                "floor_id": floor["id"],
                "from": "2026-11-16T10:00:00+03:00",
                "to": "2026-11-16T12:00:00+03:00",
            },
        )
        assert response.status_code == 200
        spaces = response.json()["items"]
        counts[floor["number"]] = (
            sum(row["kind"] == "DESK" for row in spaces),
            sum(row["kind"] == "MEETING_ROOM" for row in spaces),
        )
        for space in spaces:
            layout = space["layout"]
            assert all(math.isfinite(layout[key]) for key in ("x", "y", "width", "height"))
            assert layout["width"] > 0 and layout["height"] > 0
            assert 0 <= layout["x"] < layout["x"] + layout["width"] <= plan["width"]
            assert 0 <= layout["y"] < layout["y"] + layout["height"] <= plan["height"]
    assert counts == {2: (24, 3), 3: (12, 2)}


async def test_second_floor_snapshot_is_independent_of_first_floor(api):
    response = await api.get(
        "/api/v1/spaces",
        params={
            "floor_id": "floor-3",
            "from": "2026-11-16T10:00:00+03:00",
            "to": "2026-11-16T12:00:00+03:00",
        },
    )
    assert response.status_code == 200
    rows = {row["id"]: row for row in response.json()["items"]}
    assert len(rows) == 14 and "D-03" not in rows
    assert rows["D-31"]["desk_mode"] == "DEDICATED"
    assert not rows["D-32"]["is_available_for_full_interval"]
    assert rows["M-32"]["is_available_for_full_interval"]
