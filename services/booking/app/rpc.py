"""Bounded RabbitMQ adapter to the same authenticated Booking REST handlers in-process."""

import asyncio
import json
import time
from typing import Literal
from urllib.parse import quote
from uuid import UUID

import aio_pika
import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

QUEUE = "biocad.booking.rpc.v1"
REPLY_PREFIX = "biocad.rpc.reply."
OPERATIONS = Literal[
    "auth",
    "authorize",
    "reserve_llm",
    "search_employees",
    "list_spaces",
    "get_availability",
    "get_space_details",
    "create_booking",
    "replay_booking",
]


class Envelope(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal[1]
    request_id: UUID
    deadline_at: float
    operation: OPERATIONS
    session_token: str = Field(max_length=1024, pattern=r"^[A-Za-z0-9._-]*$")
    csrf: str = Field(default="", max_length=128, pattern=r"^[A-Za-z0-9_-]*$")
    payload: dict = Field(default_factory=dict)


def public_space(space):
    return {
        key: space[key]
        for key in (
            "id",
            "floor_id",
            "kind",
            "desk_mode",
            "capacity",
            "zone",
            "layout",
            "is_available_for_full_interval",
            "is_partial",
        )
    }


class RpcServer:
    def __init__(self, app, url):
        self.app, self.url = app, url
        self.connection = None
        self.channel = None

    async def dispatch(self, body: Envelope):
        async def trusted(scope, receive, send):
            scope.setdefault("extensions", {})["biocad.rpc"] = True
            await self.app(scope, receive, send)

        headers = {
            "Cookie": "biocad_session=" + body.session_token,
            "X-CSRF-Token": body.csrf,
            "X-Request-ID": str(body.request_id),
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=trusted), base_url="http://booking-rpc", headers=headers
        ) as api:

            async def call(method, path, **kwargs):
                response = await api.request(method, path, **kwargs)
                return response.status_code, response.json()

            params = body.payload
            if body.operation == "auth":
                status, data = await call("GET", "/api/v1/auth/me")
                return (
                    (
                        status,
                        {
                            "employee_id": data["employee"]["id"],
                            "fictional": data["employee"]["fictional"],
                            "csrf_token": data["csrf_token"],
                        },
                    )
                    if status == 200
                    else (status, data)
                )
            if body.operation in {"authorize", "reserve_llm"}:
                return await call(
                    "POST",
                    "/api/v1/internal/assistant/"
                    + ("authorize" if body.operation == "authorize" else "reserve"),
                    json=params,
                )
            if body.operation == "replay_booking":
                return await call("POST", "/api/v1/internal/assistant/replay", json=params)
            if body.operation == "create_booking":
                if set(params) != {"space_id", "start_at", "end_at", "idempotency_key"}:
                    return 422, {
                        "error": {"code": "VALIDATION_ERROR", "message": "Проверьте параметры подтверждения"}
                    }
                key = params["idempotency_key"]
                if (
                    not isinstance(key, str)
                    or not key.isascii()
                    or not 1 <= len(key) <= 128
                    or any(
                        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
                        for c in key
                    )
                ):
                    return 422, {
                        "error": {"code": "VALIDATION_ERROR", "message": "Некорректный ключ подтверждения"}
                    }
                response = await api.post(
                    "/api/v1/bookings",
                    json={k: v for k, v in params.items() if k != "idempotency_key"},
                    headers={"Idempotency-Key": key},
                )
                return response.status_code, response.json()
            if body.operation == "search_employees":
                if set(params) - {"q", "from", "to"}:
                    return 422, {
                        "error": {"code": "VALIDATION_ERROR", "message": "Некорректные параметры поиска"}
                    }
                status, data = await call("GET", "/api/v1/employees", params=params)
                if status == 200:
                    data["items"] = [p for p in data["items"] if p.get("fictional") is True]
                return status, data
            allowed = {"floor_id", "from", "to", "kind", "min_capacity", "near_employee_id", "space_id"}
            if set(params) - allowed:
                return 422, {
                    "error": {"code": "VALIDATION_ERROR", "message": "Некорректные параметры доступности"}
                }
            if body.operation == "get_space_details":
                status, data = await call(
                    "GET",
                    "/api/v1/spaces/" + quote(str(params.get("space_id", "")), safe=""),
                    params={k: params.get(k, "") for k in ("from", "to")},
                )
                if status != 200:
                    return status, data
                space = public_space(data["space"])
                _, floors = await call("GET", "/api/v1/floors")
                floor = next(row for row in floors["items"] if row["id"] == space["floor_id"])
                return 200, {
                    **{k: data[k] for k in ("from", "to", "snapshot_at")},
                    "space": space,
                    "floor": {k: floor[k] for k in ("id", "name", "number", "office_id", "office_name")},
                }
            status, data = await call(
                "GET", "/api/v1/spaces", params={k: params.get(k, "") for k in ("floor_id", "from", "to")}
            )
            if status != 200:
                return status, data
            spaces = [public_space(space) for space in data["items"]]
            if body.operation == "get_availability":
                spaces = [
                    s for s in spaces if s["is_available_for_full_interval"] and s["desk_mode"] != "DEDICATED"
                ]
                if params.get("kind"):
                    spaces = [s for s in spaces if s["kind"] == params["kind"]]
                capacity = params.get("min_capacity", 1)
                if not isinstance(capacity, int) or not 1 <= capacity <= 100:
                    return 422, {"error": {"code": "VALIDATION_ERROR", "message": "Проверьте вместимость"}}
                spaces = [s for s in spaces if s["capacity"] >= capacity]
                if params.get("near_employee_id"):
                    status, employee = await call(
                        "GET",
                        "/api/v1/employees/" + quote(str(params["near_employee_id"]), safe="") + "/location",
                        params={k: params.get(k, "") for k in ("from", "to")},
                    )
                    if status != 200:
                        return status, employee
                    if employee["employee"].get("fictional") is not True:
                        return 403, {
                            "error": {
                                "code": "DEMO_DATA_ONLY",
                                "message": "AI работает только с вымышленными профилями",
                            }
                        }
                    targets = [
                        s
                        for s in data["items"]
                        if any(loc["space_id"] == s["id"] for loc in employee["locations"])
                    ]
                    if not targets:
                        spaces = []
                    else:

                        def center(s):
                            return (
                                s["layout"]["x"] + s["layout"]["width"] / 2,
                                s["layout"]["y"] + s["layout"]["height"] / 2,
                            )

                        def distance(s):
                            x, y = center(s)
                            return min((x - center(t)[0]) ** 2 + (y - center(t)[1]) ** 2 for t in targets)

                        spaces.sort(key=lambda s: (distance(s), s["id"]))
            limit = 64 if body.operation == "list_spaces" else 24
            return 200, {
                **{k: data[k] for k in ("from", "to", "snapshot_at", "floor_id")},
                "items": spaces[:limit],
                "total": len(spaces),
                "truncated": len(spaces) > limit,
            }

    async def handle(self, message):
        async with message.process(requeue=False):
            if (
                not message.reply_to
                or not message.reply_to.startswith(REPLY_PREFIX)
                or not message.correlation_id
                or len(message.body) > 32768
            ):
                return
            try:
                body = Envelope.model_validate_json(message.body)
                if str(body.request_id) != message.correlation_id:
                    return
                remaining = min(body.deadline_at - time.time(), 10)
                if remaining <= 0:
                    raise TimeoutError
                async with asyncio.timeout(remaining):
                    status, data = await self.dispatch(body)
            except (ValidationError, ValueError, TypeError):
                status, data = 422, {"error": {"code": "RPC_INVALID", "message": "Некорректный RPC-запрос"}}
            except TimeoutError:
                status, data = 504, {"error": {"code": "RPC_TIMEOUT", "message": "Сервис не ответил вовремя"}}
            except Exception:
                status, data = (
                    503,
                    {"error": {"code": "RPC_UNAVAILABLE", "message": "Сервис временно недоступен"}},
                )
            reply = {
                "schema_version": 1,
                "request_id": message.correlation_id,
                "type": "booking.response.v1",
                "status": status,
                "data": data,
            }
            try:
                await self.channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(reply).encode(),
                        correlation_id=message.correlation_id,
                        content_type="application/json",
                    ),
                    routing_key=message.reply_to,
                    mandatory=False,
                )
            except Exception:
                pass  # A timed-out caller may have removed its reply queue; never repeat a committed write.

    async def run(self):
        if not self.url:
            return
        while True:
            try:
                self.connection = await aio_pika.connect_robust(self.url, timeout=3)
                channel = await self.connection.channel(publisher_confirms=True)
                self.channel = channel
                await channel.set_qos(prefetch_count=4)
                queue = await channel.declare_queue(
                    QUEUE,
                    durable=True,
                    arguments={"x-message-ttl": 15000, "x-max-length": 256, "x-overflow": "reject-publish"},
                )
                await queue.consume(self.handle)
                await asyncio.Future()
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(3)
            finally:
                if self.connection is not None:
                    await self.connection.close()
