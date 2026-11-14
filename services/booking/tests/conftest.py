import os

import allure
import pytest
from httpx import ASGITransport, AsyncClient

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
        variable = "APP_ENV" if name == "environment" else name.upper()
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
