import allure
import httpx
import pytest

pytestmark = pytest.mark.integration


@allure.suite("smoke")
@allure.feature("ops")
async def test_running_service_is_ready_with_real_postgres(booking_base_url):
    async with httpx.AsyncClient(base_url=booking_base_url, timeout=10) as c:
        resp = await c.get("/readyz")
    assert resp.status_code == 200, resp.text
    assert resp.json()["checks"]["postgres"] is True
