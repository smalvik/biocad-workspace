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
        variable = "REPORT_ENV" if name == "environment" else name.upper()
        allure.dynamic.label(name, os.environ.get(variable, default))


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c
