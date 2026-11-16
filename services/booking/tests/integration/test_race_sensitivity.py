"""A genuine failing child pytest run followed by a restored passing run, in owned storage only."""

import allure
import pytest

from race_probe.experiment import Experiment

pytestmark = [pytest.mark.integration, allure.suite("regression"), allure.feature("race-red-green")]


async def test_real_two_process_race_detects_missing_constraint_and_passes_after_restore(database, tmp_path):
    allure.dynamic.title("Race sensitivity: genuine red FAIL, restored green PASS (disposable DB only)")
    try:
        proof = await Experiment(tmp_path).run()
        assert proof["status"] == "passed" and proof["owned_database_removed"]
        print(
            "WB-08: genuine red pytest exit 1 (2 failed); restored green exit 0 (3 passed); owned DB removed"
        )
    finally:
        for path in sorted(tmp_path.glob("*.log")):
            allure.attach(path.read_text(), path.name, allure.attachment_type.TEXT)
        if (tmp_path / "proof.json").exists():
            allure.attach(
                (tmp_path / "proof.json").read_text(),
                "Actual red/green HTTP, catalog and database proof",
                allure.attachment_type.JSON,
            )
