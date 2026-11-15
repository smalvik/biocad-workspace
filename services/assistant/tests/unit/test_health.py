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


@allure.suite("regression")
async def test_streamed_body_limit_does_not_echo_input(client):
    async def chunks():
        yield b'{"message":"'
        yield b"x" * 20001
        yield b'"}'

    response = await client.post("/api/v1/assistant/chat", content=chunks())
    assert response.status_code == 413
    assert "x" * 20 not in response.text
