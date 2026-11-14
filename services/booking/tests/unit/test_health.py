import allure
import pytest

from app import db


@allure.suite("smoke")
@allure.feature("ops")
async def test_healthz_reports_service(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["service"] == "booking"


@allure.suite("smoke")
@allure.feature("ops")
async def test_api_prefixed_healthz_for_public_proxy(client):
    resp = await client.get("/api/v1/healthz")
    assert resp.status_code == 200


@allure.suite("smoke")
@allure.feature("ops")
async def test_openapi_served_under_api_docs_path(client):
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"].startswith("BIOCAD Workspace")


@allure.suite("smoke")
@allure.feature("ops")
@pytest.mark.parametrize("path", ["/readyz", "/api/v1/readyz"])
async def test_dependency_failure_degrades_readiness_but_not_liveness(client, monkeypatch, path):
    async def unavailable():
        return False

    monkeypatch.setattr(db, "ping", unavailable)
    ready = await client.get(path)
    assert ready.status_code == 503
    assert ready.json() == {"status": "degraded", "checks": {"postgres": False}}
    assert (await client.get("/healthz")).status_code == 200
