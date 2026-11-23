import json

import allure
import httpx
import pytest

from app.config import Settings
from app.errors import AssistantError
from app.provider import MAX_REQUESTS, ProviderRoute

pytestmark = [allure.suite("regression"), allure.feature("bounded free-model failover")]
PRIMARY = "inclusionai/ling-3.2-flash:free"
FALLBACK = "google/gemma-4-26b-a4b-it:free"


def settings():
    return Settings(openrouter_primary_model=PRIMARY, openrouter_fallback_model=FALLBACK)


def success(model, message=None, **extra):
    return httpx.Response(
        200,
        json={
            "model": model,
            "usage": {"cost": 0},
            "choices": [{"message": message or {"tool_calls": []}}],
            **extra,
        },
    )


def transport(monkeypatch, respond):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.provider.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )


@pytest.mark.parametrize(
    "failure", [503, 502, 408, "timeout", "network", "bad_json", "bad_tools", "rate_limit"]
)
async def test_eligible_failure_switches_once_and_stays_on_verified_free_fallback(monkeypatch, failure):
    requests = []

    async def no_delay(_delay):
        pass

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
        assert body["provider"]["allow_fallbacks"] is False
        if body["model"] == FALLBACK:
            return success(FALLBACK)
        if failure == "timeout":
            raise httpx.ReadTimeout("fictional timeout", request=request)
        if failure == "network":
            raise httpx.ConnectError("fictional network", request=request)
        if failure == "bad_json":
            return httpx.Response(200, content=b"not-json")
        if failure == "bad_tools":
            return httpx.Response(200, json={"model": PRIMARY, "usage": {"cost": 0}, "choices": []})
        if failure == "rate_limit":
            return httpx.Response(429, headers={"Retry-After": "3"})
        return httpx.Response(failure)

    transport(monkeypatch, respond)
    monkeypatch.setattr("app.provider.asyncio.sleep", no_delay)
    route = ProviderRoute(settings(), {PRIMARY, FALLBACK})
    await route.complete([], [])
    await route.complete([], [])
    assert route.metadata() == {"state": "fallback", "model": FALLBACK}
    expected = (
        [PRIMARY, PRIMARY, FALLBACK, FALLBACK] if failure == "rate_limit" else [PRIMARY, FALLBACK, FALLBACK]
    )
    assert [body["model"] for body in requests] == expected
    assert route.budget.used == len(requests)


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404])
async def test_auth_billing_input_or_policy_errors_never_try_another_model(monkeypatch, status):
    attempts = []

    def respond(request):
        attempts.append(json.loads(request.content)["model"])
        return httpx.Response(status)

    transport(monkeypatch, respond)
    with pytest.raises(AssistantError):
        await ProviderRoute(settings(), {PRIMARY, FALLBACK}).complete([], [])
    assert attempts == [PRIMARY]


@pytest.mark.parametrize("boundary", ["nonzero_cost", "unknown_model", "huge_response"])
async def test_response_boundary_violations_are_terminal_without_more_inference(monkeypatch, boundary):
    attempts = []

    def respond(request):
        attempts.append(json.loads(request.content)["model"])
        if boundary == "nonzero_cost":
            return success(PRIMARY, usage={"cost": "0.01"})
        if boundary == "unknown_model":
            return success("unapproved/model")
        return httpx.Response(200, content=b"x" * 65537)

    transport(monkeypatch, respond)
    with pytest.raises(AssistantError):
        await ProviderRoute(settings(), {PRIMARY, FALLBACK}).complete([], [])
    assert attempts == [PRIMARY]


async def test_global_attempt_budget_cannot_be_bypassed_by_switching_models(monkeypatch):
    attempts = []

    def respond(request):
        model = json.loads(request.content)["model"]
        attempts.append(model)
        if len(attempts) == MAX_REQUESTS - 1:
            return httpx.Response(503)
        return success(model)

    transport(monkeypatch, respond)
    route = ProviderRoute(settings(), {PRIMARY, FALLBACK})
    for _ in range(MAX_REQUESTS - 1):
        await route.complete([], [])
    assert route.state == "fallback"
    with pytest.raises(AssistantError):
        await route.complete([], [])
    assert attempts == [PRIMARY] * (MAX_REQUESTS - 1) + [FALLBACK]


async def test_failure_in_one_chat_does_not_switch_other_users_to_backup(monkeypatch):
    def respond(request):
        body = json.loads(request.content)
        if body["messages"] == ["first"] and body["model"] == PRIMARY:
            return httpx.Response(503)
        return success(body["model"])

    transport(monkeypatch, respond)
    first, other = (ProviderRoute(settings(), {PRIMARY, FALLBACK}) for _ in range(2))
    await first.complete(["first"], [])
    await other.complete(["other"], [])
    assert first.state == "fallback" and other.state == "primary"
    assert first.budget.used == 2 and other.budget.used == 1


@pytest.mark.parametrize("catalog_state", ["primary_paid", "primary_missing", "backup_paid", "outage"])
async def test_catalog_verifies_both_models_and_never_sends_to_an_unverified_model(
    monkeypatch, catalog_state
):
    attempts = []

    def respond(request):
        if request.method == "GET":
            assert "Authorization" not in request.headers
            if catalog_state == "outage":
                return httpx.Response(503)
            rows = [
                {
                    "id": model,
                    "pricing": {"prompt": "0", "completion": "0"},
                    "supported_parameters": ["tools", "tool_choice"],
                }
                for model in [PRIMARY, FALLBACK]
            ]
            if catalog_state == "primary_missing":
                rows.pop(0)
            elif catalog_state == "primary_paid":
                rows[0]["pricing"]["prompt"] = "0.001"
            elif catalog_state == "backup_paid":
                rows[1]["pricing"]["completion"] = "0.001"
            return httpx.Response(200, json={"data": rows})
        model = json.loads(request.content)["model"]
        attempts.append(model)
        return httpx.Response(503) if model == PRIMARY else success(model)

    transport(monkeypatch, respond)
    if catalog_state in {"outage", "backup_paid"}:
        with pytest.raises(AssistantError):
            route = await ProviderRoute.create(settings())
            await route.complete([], [])
        assert attempts == ([] if catalog_state == "outage" else [PRIMARY])
    else:
        route = await ProviderRoute.create(settings())
        await route.complete([], [])
        assert route.state == "fallback" and attempts == [FALLBACK]


async def test_catalog_is_checked_again_for_a_new_chat_not_cached_across_users(monkeypatch):
    catalogs = []

    def respond(request):
        assert request.method == "GET"
        catalogs.append(True)
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": PRIMARY,
                        "pricing": {"prompt": "0" if len(catalogs) == 1 else "0.01", "completion": "0"},
                        "supported_parameters": ["tools", "tool_choice"],
                    }
                ]
            },
        )

    transport(monkeypatch, respond)
    assert (await ProviderRoute.create(settings())).state == "primary"
    with pytest.raises(AssistantError):
        await ProviderRoute.create(settings())
    assert len(catalogs) == 2


@pytest.mark.parametrize("fallback", ["paid/model", PRIMARY])
def test_fallback_configuration_rejects_paid_or_duplicate_models(fallback):
    with pytest.raises(ValueError):
        Settings(openrouter_primary_model=PRIMARY, openrouter_fallback_model=fallback)


def test_test_fixture_flag_cannot_enable_an_arbitrary_fallback():
    with pytest.raises(ValueError):
        Settings(
            app_env="local",
            enable_llm_test_fixture=True,
            openrouter_primary_model="test/scripted",
            openrouter_api_key="fixture-not-secret",
            openrouter_base_url="http://llm-fixture:8090/v1",
            openrouter_fallback_model="paid/model",
        )
