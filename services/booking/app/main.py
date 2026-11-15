import asyncio
from contextlib import asynccontextmanager, suppress
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import db
from app.assistant_limits import router as assistant_limits_router
from app.auth import router as auth_router
from app.bookings import router as booking_router
from app.config import get_settings
from app.employees import router as employee_router
from app.errors import ApiError
from app.rpc import RpcServer

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = RpcServer(app, get_settings().rabbitmq_url.get_secret_value())
    task = asyncio.create_task(worker.run())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await db.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="BIOCAD Workspace — Booking Service",
        version="0.1.0",
        description="Floors, spaces, occupancy and bookings. The only service allowed to write bookings.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        try:
            correlation = UUID(request.headers.get("X-Request-ID", ""))
        except ValueError:
            correlation = uuid4()
        request.state.request_id = str(correlation)
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(correlation)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        details = [
            {"loc": list(error["loc"]), "type": error["type"], "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            {"error": {"code": "VALIDATION_ERROR", "message": "Проверьте параметры", "details": details}},
            status_code=422,
        )

    app.include_router(auth_router)
    app.include_router(booking_router)
    app.include_router(employee_router)
    app.include_router(assistant_limits_router)

    @app.get("/healthz", tags=["ops"])
    @app.get(f"{API_PREFIX}/healthz", tags=["ops"], include_in_schema=False)
    async def healthz() -> dict:
        """Liveness: the process is up. Does not touch dependencies."""
        return {
            "status": "ok",
            "service": "booking",
            "version": get_settings().git_sha,
            "release_version": get_settings().release_version,
        }

    @app.get("/readyz", tags=["ops"])
    @app.get(f"{API_PREFIX}/readyz", tags=["ops"], include_in_schema=False)
    async def readyz():
        """Readiness: PostgreSQL is reachable."""
        db_ok = await db.ping()
        body = {"status": "ok" if db_ok else "degraded", "checks": {"postgres": db_ok}}
        return JSONResponse(body, status_code=200 if db_ok else 503)

    return app


app = create_app()
