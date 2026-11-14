import allure


@allure.suite("smoke")
@allure.feature("ops")
async def test_healthz_reports_service(client):
    resp = await client.get("/api/v1/assistant/healthz")
    assert resp.status_code == 200
    assert resp.json()["service"] == "assistant"


@allure.suite("smoke")
@allure.feature("ops")
async def test_swagger_under_assistant_prefix(client):
    resp = await client.get("/api/v1/assistant/openapi.json")
    assert resp.status_code == 200
