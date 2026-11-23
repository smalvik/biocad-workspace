"""Bounded, request-local routing between explicitly configured zero-price models."""

import asyncio
import json
import math
from decimal import Decimal, InvalidOperation

import httpx

from app.errors import AssistantError, unavailable

MAX_REQUESTS = 6


class ProviderFailure(AssistantError):
    def __init__(self, reason, *, fallback_allowed=True, rate_limit=False):
        error = (
            AssistantError(
                429, "AI_RATE_LIMIT", "Бесплатная модель занята. Повторите позже или используйте форму."
            )
            if rate_limit
            else unavailable()
        )
        super().__init__(error.status, error.code, error.message)
        self.reason = reason
        self.fallback_allowed = fallback_allowed


class RequestBudget:
    def __init__(self):
        self.used = 0
        self.events = []

    def take(self):
        if self.used >= MAX_REQUESTS:
            raise unavailable()
        self.used += 1

    def record(self, model, outcome):
        self.events.append({"model": model, "outcome": outcome})


def parse_response(data, model, tools):
    try:
        result = json.loads(data)
        if not isinstance(result, dict):
            raise ValueError
        usage = result.get("usage") or {}
        if not isinstance(usage, dict):
            raise ValueError
        cost = usage.get("cost")
        if cost is not None:
            try:
                price = Decimal(str(cost))
            except InvalidOperation:
                raise unavailable() from None
            if not price.is_finite() or price != 0:
                # A price-boundary violation is terminal, not another inference attempt.
                raise unavailable()
        actual_model = result.get("model")
        if actual_model is not None and actual_model not in {model, model.removesuffix(":free")}:
            raise unavailable()
        message = result["choices"][0]["message"]
        if not isinstance(message, dict):
            raise ValueError
        if tools:
            calls = message.get("tool_calls")
            allowed = {tool["function"]["name"] for tool in tools}
            if not isinstance(calls, list) or not 1 <= len(calls) <= 4:
                raise ValueError
            for call in calls:
                if (
                    not isinstance(call.get("id"), str)
                    or call["function"]["name"] not in allowed
                    or not isinstance(json.loads(call["function"]["arguments"]), dict)
                ):
                    raise ValueError
        return message, {
            "model": actual_model,
            "requested_model": model,
            "provider": result.get("provider"),
            "cost": cost,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        }
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ProviderFailure("invalid_response") from None


async def complete(settings, messages, tools, *, model=None, budget=None):
    """Transport helper; runtime callers must first create a catalog-verified route."""
    model = model or settings.openrouter_primary_model
    budget = budget or RequestBudget()
    body = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "required",
        "max_tokens": 768,
        "temperature": 0,
        "reasoning": {"enabled": False},
        "provider": {
            "require_parameters": True,
            "allow_fallbacks": False,
            "data_collection": "deny",
            "max_price": {"prompt": 0, "completion": 0, "request": 0},
        },
    }
    if len(json.dumps(body, ensure_ascii=False).encode()) > 24000:
        raise unavailable()
    async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), follow_redirects=False) as client:
        for attempt in range(2):
            budget.take()
            try:
                async with client.stream(
                    "POST",
                    settings.openrouter_base_url + "/chat/completions",
                    json=body,
                    headers={
                        "Authorization": "Bearer " + settings.openrouter_api_key.get_secret_value(),
                        "X-OpenRouter-Title": "BIOCAD fictional workspace demo",
                    },
                ) as response:
                    if response.status_code == 429:
                        budget.record(model, "rate_limited")
                        error = ProviderFailure("rate_limited", rate_limit=True)
                        if attempt:
                            raise error
                        try:
                            delay = float(response.headers.get("Retry-After", "5"))
                        except ValueError:
                            raise error from None
                        if not math.isfinite(delay) or delay < 0 or delay > 10:
                            raise error
                    elif response.status_code != 200:
                        budget.record(model, "http_" + str(response.status_code))
                        raise ProviderFailure(
                            "http_" + str(response.status_code),
                            fallback_allowed=response.status_code == 408 or response.status_code >= 500,
                        )
                    else:
                        data = bytearray()
                        async for part in response.aiter_bytes():
                            data.extend(part)
                            if len(data) > 65536:
                                raise unavailable()
                        try:
                            parsed = parse_response(data, model, tools)
                        except ProviderFailure:
                            budget.record(model, "invalid_response")
                            raise
                        budget.record(model, "success")
                        return parsed
            except httpx.TransportError as error:
                reason = "timeout" if isinstance(error, httpx.TimeoutException) else "network_error"
                budget.record(model, reason)
                raise ProviderFailure(reason) from None
            # One same-model 429 retry; Retry-After is never shortened.
            await asyncio.sleep(max(3, delay))
    raise unavailable()


async def eligible_models(settings):
    models = {settings.openrouter_primary_model, settings.openrouter_fallback_model} - {""}
    if settings.enable_llm_test_fixture:
        return models & {"test/scripted", "test/fallback"}
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.get(settings.openrouter_base_url + "/models")
        response.raise_for_status()
        if len(response.content) > 4_000_000:
            raise unavailable()
        verified = set()
        for model in response.json()["data"]:
            if model["id"] not in models or not model["id"].endswith(":free"):
                continue
            pricing = model["pricing"]
            if (
                {"prompt", "completion"} <= pricing.keys()
                and all(Decimal(str(value)) == 0 for value in pricing.values())
                and {"tools", "tool_choice"} <= set(model.get("supported_parameters", []))
            ):
                verified.add(model["id"])
        return verified
    except Exception:
        # Without a current trusted catalog, neither model may be used.
        raise unavailable() from None


async def verify_free_model(settings):
    if settings.openrouter_primary_model not in await eligible_models(settings):
        raise unavailable()


class ProviderRoute:
    def __init__(self, settings, eligible):
        self.settings = settings
        self.eligible = eligible
        self.budget = RequestBudget()
        self.model = settings.openrouter_primary_model
        self.state = "primary"
        if self.model not in eligible:
            self.switch()

    @classmethod
    async def create(cls, settings):
        return cls(settings, await eligible_models(settings))

    def switch(self):
        fallback = self.settings.openrouter_fallback_model
        if self.state == "fallback" or not fallback or fallback not in self.eligible:
            raise unavailable()
        self.state, self.model = "fallback", fallback

    def metadata(self):
        return {"state": self.state, "model": self.model}

    async def complete(self, messages, tools):
        try:
            return await complete(self.settings, messages, tools, model=self.model, budget=self.budget)
        except ProviderFailure as error:
            if not error.fallback_allowed or self.state == "fallback":
                raise
            fallback = self.settings.openrouter_fallback_model
            if not fallback or fallback not in self.eligible:
                raise
            self.switch()
            return await complete(self.settings, messages, tools, model=self.model, budget=self.budget)
