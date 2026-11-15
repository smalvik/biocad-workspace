import time

import allure
import pytest
from itsdangerous.timed import TimestampSigner

from app.config import get_settings
from app.proposals import signer

pytestmark = [allure.suite("regression"), allure.feature("proposal expiry and lost confirmation")]


@pytest.mark.parametrize("existing", [True, False])
async def test_expired_proposal_can_only_read_exact_existing_booking(client, monkeypatch, existing):
    secret = get_settings().assistant_proposal_secret.get_secret_value()
    token = signer(secret).dumps(
        {
            "user_id": "e01",
            "selection": {
                "space_id": "D-12",
                "start_at": "2030-11-16T07:00:00Z",
                "end_at": "2030-11-16T08:00:00Z",
            },
        }
    )
    issued_at = int(time.time())
    monkeypatch.setattr(TimestampSigner, "get_timestamp", lambda self: issued_at + 601)
    calls = []

    class Rpc:
        async def call(self, operation, payload=None):
            calls.append((operation, payload))
            if operation == "auth":
                return {"employee_id": "e01"}
            assert operation == "replay_booking"
            return {"booking": {"id": "previously-committed"} if existing else None}

    monkeypatch.setattr("app.main.rpc_for", lambda request: Rpc())
    response = await client.post(
        "/api/v1/assistant/confirm", json={"proposal_token": token, "idempotency_key": "original-key"}
    )
    assert response.status_code == (200 if existing else 409)
    assert [name for name, _ in calls] == ["auth", "replay_booking"]
    assert calls[1][1]["idempotency_key"] == "original-key"
    assert calls[1][1]["selection"]["space_id"] == "D-12"
