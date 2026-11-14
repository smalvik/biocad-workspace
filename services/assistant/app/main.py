from fastapi import FastAPI

from app.config import get_settings

API_PREFIX = "/api/v1/assistant"


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
