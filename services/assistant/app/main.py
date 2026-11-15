from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.agent import run_agent
from app.config import get_settings
from app.errors import AssistantError
from app.proposals import verified
from app.rpc import RpcClient

API_PREFIX = "/api/v1/assistant"


class Context(BaseModel):
    model_config = ConfigDict(extra="forbid")
    floor_id: str = Field(min_length=1, max_length=64)
    start_at: str = Field(max_length=40)
    end_at: str = Field(max_length=40)
    floors: list[dict[str, str | int]] = Field(default_factory=list, max_length=10)


class History(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1500)
    history: list[History] = Field(default_factory=list, max_length=6)
    context: Context
    consent: Literal[True]


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_token: str = Field(min_length=1, max_length=2048)
    idempotency_key: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")


def rpc_for(request):
    return RpcClient(
        get_settings().rabbitmq_url.get_secret_value(),
        request.cookies.get("biocad_session", ""),
        request.headers.get("X-CSRF-Token", ""),
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="BIOCAD Workspace — Assistant Service",
        version="0.1.0",
        description=(
            "AI chat over a real LLM. Reads up-to-date data through MCP tools and only *proposes* "
            "a booking; the user confirms it via the Booking Service."
        ),
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.active_chats = 0

    @app.middleware("http")
    async def bounded(request: Request, call_next):
        # Bound actual streamed bytes: Content-Length is optional and untrusted.
        received = 0
        chunks = []
        async for chunk in request.stream():
            received += len(chunk)
            if received > 20000:
                return JSONResponse(
                    {"error": {"code": "VALIDATION_ERROR", "message": "Запрос слишком большой"}},
                    status_code=413,
                )
            chunks.append(chunk)
        # Starlette's CachedRequest replays this bounded body to the route parser.
        request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = str(uuid4())
        return response

    @app.exception_handler(AssistantError)
    async def assistant_error(_request, error):
        return JSONResponse(
            {"error": {"code": error.code, "message": error.message}}, status_code=error.status
        )

    @app.exception_handler(RequestValidationError)
    async def invalid(_request, _error):
        return JSONResponse(
            {"error": {"code": "VALIDATION_ERROR", "message": "Проверьте параметры запроса"}}, status_code=422
        )

    @app.post(f"{API_PREFIX}/chat")
    async def chat(body: ChatRequest, request: Request):
        rpc = rpc_for(request)
        identity = await rpc.call("authorize")
        if identity.get("fictional") is not True:
            raise AssistantError(403, "DEMO_DATA_ONLY", "AI доступен только для вымышленных демо-профилей")
        settings = get_settings()
        if app.state.active_chats >= settings.assistant_max_concurrent:
            raise AssistantError(429, "AI_BUSY", "AI занят. Повторите позже или используйте форму.")
        app.state.active_chats += 1
        try:
            return await run_agent(settings, rpc, identity["employee_id"], body)
        finally:
            app.state.active_chats -= 1

    @app.post(f"{API_PREFIX}/confirm")
    async def confirm(body: Confirmation, request: Request):
        rpc = rpc_for(request)
        identity = await rpc.call("auth")
        secret = get_settings().assistant_proposal_secret.get_secret_value()
        try:
            selection = verified(secret, body.proposal_token, identity["employee_id"])
        except AssistantError as expired:
            # A lost committed response remains recoverable after proposal expiry.
            # This branch can ONLY read the same user's exact existing confirmation.
            selection = verified(secret, body.proposal_token, identity["employee_id"], max_age=8 * 60 * 60)
            replay = await rpc.call(
                "replay_booking",
                {"selection": selection.model_dump(mode="json"), "idempotency_key": body.idempotency_key},
            )
            if replay["booking"] is None:
                raise expired
            return replay["booking"]
        return await rpc.call(
            "create_booking", {**selection.model_dump(mode="json"), "idempotency_key": body.idempotency_key}
        )

    @app.get("/healthz", tags=["ops"])
    @app.get(f"{API_PREFIX}/healthz", tags=["ops"], include_in_schema=False)
    async def healthz() -> dict:
        return {
            "status": "ok",
            "service": "assistant",
            "version": get_settings().git_sha,
            "release_version": get_settings().release_version,
        }

    return app


app = create_app()
