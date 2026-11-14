from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import db
from app.config import get_settings

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
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

    @app.get("/healthz", tags=["ops"])
    @app.get(f"{API_PREFIX}/healthz", tags=["ops"], include_in_schema=False)
    async def healthz() -> dict:
        """Liveness: the process is up. Does not touch dependencies."""
        return {"status": "ok", "service": "booking", "version": get_settings().git_sha}

    @app.get("/readyz", tags=["ops"])
    @app.get(f"{API_PREFIX}/readyz", tags=["ops"], include_in_schema=False)
    async def readyz():
        """Readiness: PostgreSQL is reachable."""
        db_ok = await db.ping()
        body = {"status": "ok" if db_ok else "degraded", "checks": {"postgres": db_ok}}
        return JSONResponse(body, status_code=200 if db_ok else 503)

    return app


app = create_app()
