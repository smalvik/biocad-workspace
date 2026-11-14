import os

import allure
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import create_app


@pytest.fixture(autouse=True)
def report_metadata():
    for name, default in (
        ("run_type", "smoke"),
        ("environment", "local"),
        ("git_sha", "dev"),
        ("release_version", "unreleased"),
        ("working_tree", "unknown"),
    ):
        variable = "REPORT_ENV" if name == "environment" else name.upper()
        allure.dynamic.label(name, os.environ.get(variable, default))


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
def booking_base_url() -> str:
    """URL of a *running* Booking Service (real server + real PostgreSQL) for integration tests."""
    url = os.environ.get("BOOKING_BASE_URL")
    if not url:
        pytest.skip("BOOKING_BASE_URL not set: integration tests need the compose stack")
    return url


@pytest.fixture
async def login_as(booking_base_url):
    clients = []

    async def create(username="e01"):
        client = AsyncClient(base_url=booking_base_url, timeout=30)
        clients.append(client)
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": username,
                "password": os.environ.get("DEMO_PASSWORD", "demo-workspace"),
            },
        )
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        return client

    yield create
    for client in clients:
        await client.aclose()


@pytest.fixture
async def api(login_as):
    return await login_as()


@pytest.fixture
async def database():
    if os.environ.get("ALLOW_DATABASE_TESTS") != "1":
        pytest.skip("Direct database checks require the isolated check runner")
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    yield engine
    await engine.dispose()
