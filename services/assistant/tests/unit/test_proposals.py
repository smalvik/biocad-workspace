from datetime import UTC, datetime, timedelta

import allure
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.errors import AssistantError
from app.proposals import Selection, signer, verified

pytestmark = [allure.suite("regression"), allure.feature("assistant trust boundary")]


def interval():
    start = (datetime.now(UTC) + timedelta(days=4)).replace(hour=8, minute=0, second=0, microsecond=0)
    return {
        "space_id": "D-12",
        "start_at": start.isoformat(),
        "end_at": (start + timedelta(hours=1)).isoformat(),
    }


def test_proposal_is_user_bound_and_tamper_evident():
    data = interval()
    token = signer("test-secret").dumps({"user_id": "e01", "selection": data})
    assert verified("test-secret", token, "e01").space_id == "D-12"
    for candidate, user in ((token, "e02"), (token + "tampered", "e01")):
        with pytest.raises(AssistantError) as failure:
            verified("test-secret", candidate, user)
        assert failure.value.code == "PROPOSAL_EXPIRED"


@pytest.mark.parametrize(
    "field,value", [("start_at", "2026-11-20T10:00:00"), ("start_at", "2000000000"), ("space_id", "../auth")]
)
def test_selection_rejects_naive_time_and_paths(field, value):
    data = interval()
    data[field] = value
    with pytest.raises(ValidationError):
        Selection.model_validate(data)


def test_selection_rejects_inverted_and_cross_day_intervals():
    data = interval()
    data["end_at"] = data["start_at"]
    with pytest.raises(ValidationError):
        Selection.model_validate(data)
    data["end_at"] = (datetime.fromisoformat(data["start_at"]) + timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        Selection.model_validate(data)


def test_production_disallows_fake_provider_and_insecure_urls():
    for values in (
        {"app_env": "production", "enable_llm_test_fixture": True},
        {"app_env": "production", "assistant_proposal_secret": "local-only-proposal-secret-change-me"},
        {"openrouter_base_url": "http://example.com/v1"},
    ):
        with pytest.raises(ValidationError) as invalid:
            Settings(openrouter_api_key="unit-test-sensitive-key", **values)
        assert "unit-test-sensitive-key" not in str(invalid.value)
