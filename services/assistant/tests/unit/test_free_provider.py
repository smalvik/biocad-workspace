import json

import allure
import httpx
import pytest

from app.config import Settings
from app.errors import AssistantError
from app.provider import complete, verify_free_model

pytestmark = [allure.suite("regression"), allure.feature("zero-price provider boundary")]
MODEL = "inclusionai/ling-3.2-flash:free"


@pytest.mark.parametrize(
    "price,parameters,allowed",
    [("0", ["tools", "tool_choice"], True), ("0.00001", ["tools", "tool_choice"], False), ("0", [], False)],
)
async def test_catalog_must_confirm_zero_price_and_required_tools(monkeypatch, price, parameters, allowed):
    original = httpx.AsyncClient

    def respond(request):
        assert request.method == "GET" and request.url.path.endswith("/models")
        assert "Authorization" not in request.headers
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": MODEL,
                        "pricing": {"prompt": price, "completion": "0"},
                        "supported_parameters": parameters,
                    }
                ]
            },
        )

    monkeypatch.setattr(
        "app.provider.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    settings = Settings(openrouter_primary_model=MODEL)
    if allowed:
        await verify_free_model(settings)
    else:
        with pytest.raises(AssistantError):
            await verify_free_model(settings)


async def test_inference_sets_all_price_caps_zero_and_preserves_zero_cost_evidence(monkeypatch):
    original = httpx.AsyncClient

    def respond(request):
        assert request.method == "POST"
        body = json.loads(request.content)
        assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
        assert body["provider"]["allow_fallbacks"] is False
        return httpx.Response(
            200,
            json={
                "model": MODEL,
                "provider": "test",
                "usage": {"cost": 0},
                "choices": [{"message": {"tool_calls": []}}],
            },
        )

    monkeypatch.setattr(
        "app.provider.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    message, evidence = await complete(Settings(openrouter_primary_model=MODEL), [], [])
    assert evidence["cost"] == 0 and evidence["model"] == MODEL
    assert message["tool_calls"] == []


@pytest.mark.parametrize("recover", [True, False])
async def test_free_rate_limit_has_one_bounded_retry_without_paid_fallback(monkeypatch, recover):
    original = httpx.AsyncClient
    requests = []
    delays = []

    async def sleep(delay):
        delays.append(delay)

    def respond(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1 or not recover:
            return httpx.Response(429, headers={"Retry-After": "4"})
        return httpx.Response(200, json={"model": MODEL, "usage": {"cost": 0}, "choices": [{"message": {}}]})

    monkeypatch.setattr("app.provider.asyncio.sleep", sleep)
    monkeypatch.setattr(
        "app.provider.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    if recover:
        await complete(Settings(openrouter_primary_model=MODEL), [], [])
    else:
        with pytest.raises(AssistantError) as error:
            await complete(Settings(openrouter_primary_model=MODEL), [], [])
        assert error.value.code == "AI_RATE_LIMIT"
    assert delays == [4] and len(requests) == 2
    assert all(body["model"] == MODEL and body["provider"]["max_price"]["prompt"] == 0 for body in requests)
