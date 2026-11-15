"""Real MCP SDK STDIO + RabbitMQ + Booking/PostgreSQL; provider is explicitly scripted."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import allure
import httpx
import pytest
from mcp import Client

from app.agent import stdio_parameters
from app.config import Settings
from app.errors import AssistantError
from app.rpc import RpcClient

pytestmark = [allure.suite("regression"), allure.feature("assistant real MCP/RabbitMQ/PostgreSQL")]


@pytest.fixture
async def account():
    if not os.environ.get("ASSISTANT_BASE_URL"):
        pytest.skip("Needs isolated Compose stack")
    async with httpx.AsyncClient(base_url=os.environ["BOOKING_BASE_URL"], timeout=30) as booking:
        response = await booking.post(
            "/api/v1/auth/login", json={"username": "e10", "password": "demo-workspace"}
        )
        assert response.status_code == 200
        session = response.json()
        token = booking.cookies.get("biocad_session")
        booking.headers["X-CSRF-Token"] = session["csrf_token"]
        rpc = RpcClient(os.environ["RABBITMQ_URL"], token, session["csrf_token"])
        async with httpx.AsyncClient(
            base_url=os.environ["ASSISTANT_BASE_URL"],
            timeout=75,
            headers={"Cookie": "biocad_session=" + token, "X-CSRF-Token": session["csrf_token"]},
        ) as assistant:
            yield booking, assistant, rpc, session


def context():
    start = (datetime.now(UTC) + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    return {
        "floor_id": "floor-2",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
    }


async def chat(assistant, message="Найди FreeDesk на выбранное время", selected=None):
    return await assistant.post(
        "/api/v1/assistant/chat",
        json={"message": message, "history": [], "consent": True, "context": selected or context()},
    )


async def test_real_mcp_discovers_read_tools_and_gets_live_availability(account):
    booking, _, rpc, session = account
    parameters = stdio_parameters(Settings(), rpc, session["employee"]["id"])
    assert "OPENROUTER_API_KEY" not in parameters.env
    async with Client(parameters) as client:
        tools = {tool.name for tool in (await client.list_tools()).tools}
        assert {"search_employees", "list_spaces", "get_availability", "get_space_details"} <= tools
        assert not {"create_booking", "cancel_booking"} & tools
        selected = context()
        result = await client.call_tool("get_availability", selected)
        assert not result.is_error
        items = result.structured_content["items"]
        assert items and all(item["is_available_for_full_interval"] for item in items)
        assert all(item["desk_mode"] != "DEDICATED" for item in items)
        listed = (await client.call_tool("list_spaces", selected)).structured_content
        assert listed["truncated"] is False
        assert any(space["kind"] == "MEETING_ROOM" for space in listed["items"])
        details = (
            await client.call_tool(
                "get_space_details",
                {"space_id": items[0]["id"], "start_at": selected["start_at"], "end_at": selected["end_at"]},
            )
        ).structured_content
        assert details["space"]["id"] == items[0]["id"]
        employees = (
            await client.call_tool(
                "search_employees",
                {"q": "Анна Смирнова", "start_at": selected["start_at"], "end_at": selected["end_at"]},
            )
        ).structured_content
        assert employees["items"] and employees["items"][0]["fictional"] is True
        nearby = (
            await client.call_tool(
                "get_availability", {**selected, "near_employee_id": employees["items"][0]["id"]}
            )
        ).structured_content
        assert nearby["items"]
        before = (await booking.get("/api/v1/bookings/me")).json()["items"]
        proposal = await client.call_tool(
            "propose_booking",
            {"space_id": items[0]["id"], "start_at": selected["start_at"], "end_at": selected["end_at"]},
        )
        assert proposal.structured_content["proposal"]["selection"]["space_id"] == items[0]["id"]
        after = (await booking.get("/api/v1/bookings/me")).json()["items"]
        assert before == after


async def test_chat_proposal_only_then_concurrent_idempotent_confirmation(account):
    booking, assistant, _, _ = account
    before = (await booking.get("/api/v1/bookings/me")).json()["items"]
    response = await chat(assistant)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["scripted_test"] is True
    assert data["tools_used"] == ["get_availability", "propose_booking"]
    assert (await booking.get("/api/v1/bookings/me")).json()["items"] == before
    proposal = data["proposal"]
    body = {"proposal_token": proposal["token"], "idempotency_key": uuid4().hex}
    forbidden = await assistant.post(
        "/api/v1/assistant/confirm", json=body, headers={"X-CSRF-Token": "wrong"}
    )
    assert forbidden.status_code == 403
    assert (await booking.get("/api/v1/bookings/me")).json()["items"] == before
    try:
        responses = await asyncio.gather(
            *(assistant.post("/api/v1/assistant/confirm", json=body) for _ in range(2))
        )
        assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
        first, second = [r.json() for r in responses]
        assert first == second
        assert first["space_id"] == proposal["selection"]["space_id"]
        assert datetime.fromisoformat(first["start_at"].replace("Z", "+00:00")) == datetime.fromisoformat(
            proposal["selection"]["start_at"].replace("Z", "+00:00")
        )
        own = (await booking.get("/api/v1/bookings/me")).json()["items"]
        assert sum(row["id"] == first["id"] for row in own) == 1
    finally:
        own = (await booking.get("/api/v1/bookings/me")).json()["items"]
        for row in own:
            if row["id"] not in {old["id"] for old in before}:
                assert (await booking.post(f"/api/v1/bookings/{row['id']}/cancel")).status_code == 200


async def test_proposal_cannot_be_confirmed_by_another_user_and_conflicts_are_rechecked(account):
    _, assistant, _, _ = account
    response = await chat(assistant)
    assert response.status_code == 200, response.text
    proposal = response.json()["proposal"]
    body = {"proposal_token": proposal["token"], "idempotency_key": uuid4().hex}
    async with httpx.AsyncClient(base_url=os.environ["BOOKING_BASE_URL"], timeout=30) as other:
        login = await other.post("/api/v1/auth/login", json={"username": "e11", "password": "demo-workspace"})
        assert login.status_code == 200
        csrf = login.json()["csrf_token"]
        token = other.cookies.get("biocad_session")
        forbidden = await assistant.post(
            "/api/v1/assistant/confirm",
            json=body,
            headers={"Cookie": "biocad_session=" + token, "X-CSRF-Token": csrf},
        )
        assert forbidden.status_code == 409
        created = await other.post(
            "/api/v1/bookings",
            json=proposal["selection"],
            headers={"X-CSRF-Token": csrf, "Idempotency-Key": uuid4().hex},
        )
        assert created.status_code == 201, created.text
        try:
            conflict = await assistant.post("/api/v1/assistant/confirm", json=body)
            assert conflict.status_code == 409
            assert conflict.json()["error"]["code"] == "BOOKING_CONFLICT"
        finally:
            cancelled = await other.post(
                f"/api/v1/bookings/{created.json()['id']}/cancel", headers={"X-CSRF-Token": csrf}
            )
            assert cancelled.status_code == 200


async def test_auth_csrf_consent_and_internal_quota_routes_are_protected(account):
    booking, assistant, rpc, _ = account
    bad = RpcClient(rpc.url, rpc.session_token, "wrong")
    with pytest.raises(AssistantError) as failure:
        await bad.call("authorize")
    assert failure.value.status == 403
    internal = await booking.post("/api/v1/internal/assistant/authorize", headers={"X-Biocad-RPC": "true"})
    assert internal.status_code == 403
    response = await assistant.post(
        "/api/v1/assistant/chat", json={"message": "test", "context": context(), "consent": False}
    )
    assert response.status_code == 422
    response = await assistant.post(
        "/api/v1/assistant/confirm", json={"proposal_token": "forged", "idempotency_key": "bad"}
    )
    assert response.status_code == 409


async def test_provider_failure_is_honest_and_manual_booking_remains_available(account):
    booking, assistant, _, _ = account
    response = await chat(assistant, "сбой AI")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    selected = context()
    spaces = (
        await booking.get(
            "/api/v1/spaces",
            params={"floor_id": "floor-2", "from": selected["start_at"], "to": selected["end_at"]},
        )
    ).json()["items"]
    space = next(
        item for item in spaces if item["is_available_for_full_interval"] and item["desk_mode"] != "DEDICATED"
    )
    created = await booking.post(
        "/api/v1/bookings",
        json={"space_id": space["id"], "start_at": selected["start_at"], "end_at": selected["end_at"]},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert created.status_code == 201, created.text
    assert (await booking.post(f"/api/v1/bookings/{created.json()['id']}/cancel")).status_code == 200


async def test_missing_fields_are_clarified_and_hallucinated_space_never_commits(account):
    booking, assistant, _, _ = account
    response = await chat(assistant, "уточни")
    assert response.status_code == 200, response.text
    assert response.json()["proposal"] is None
    assert "Уточните" in response.json()["reply"]
    before = (await booking.get("/api/v1/bookings/me")).json()["items"]
    response = await chat(assistant, "несуществующее место")
    assert response.status_code == 200, response.text
    assert response.json()["proposal"] is None
    assert (await booking.get("/api/v1/bookings/me")).json()["items"] == before
