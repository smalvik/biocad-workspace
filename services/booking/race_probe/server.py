"""Real production routers over loopback HTTP; test lifecycle excludes broker consumers."""

import os
import socket
import sys
from contextlib import asynccontextmanager

from sqlalchemy.engine import make_url

from app import db
from app.main import create_app
from race_probe.guard import CHILD


def create_probe_app():
    if (
        os.environ.get("WB08_PROBE") != "1"
        or os.environ.get("APP_ENV") != "local"
        or not CHILD.fullmatch(make_url(os.environ["DATABASE_URL"]).database or "")
    ):
        raise RuntimeError("Test-only server requires its generated child database")

    @asynccontextmanager
    async def isolated_lifespan(app):
        try:
            yield
        finally:
            await db.dispose()

    app = create_app()
    # Do not consume the main disposable project's RPC queue using a child database.
    # Routers/authentication/booking transactions are the unchanged production code.
    app.router.lifespan_context = isolated_lifespan
    return app


if __name__ == "__main__":
    import uvicorn

    inherited = socket.socket(fileno=int(sys.argv[1]))
    uvicorn.Server(uvicorn.Config(create_probe_app(), log_level="warning", access_log=False)).run(
        sockets=[inherited]
    )
