"""Security boundaries and failed-deploy recovery, executed in the real test image."""

import copy
import json
import sys
from unittest.mock import MagicMock, Mock

import allure
import pytest

sys.path.insert(0, "/delivery")
import delivery_manifest as contract  # noqa: E402
import deploy_server as server  # noqa: E402
import package_images as package  # noqa: E402

pytestmark = [allure.suite("regression"), allure.feature("delivery")]


@pytest.fixture
def manifest():
    return {
        "schema": 1,
        "source_sha": "a" * 40,
        "version": "1.0.0",
        "images": {name: f"smalvik/biocad-{name}@sha256:{'b' * 64}" for name in contract.SERVICES},
    }


@pytest.mark.parametrize(
    "reference",
    [
        "smalvik/biocad-booking:latest",
        "attacker/biocad-booking@sha256:" + "b" * 64,
        "smalvik/biocad-booking@sha256:" + "b" * 64 + "\n; touch /tmp/injected",
    ],
)
def test_rejects_mutable_foreign_and_shell_image_references(manifest, reference):
    manifest["images"]["booking"] = reference
    with pytest.raises(ValueError):
        contract.validate(manifest, "smalvik")


def test_requires_complete_test_image_set_and_strict_version(manifest):
    del manifest["images"]["e2e"]
    with pytest.raises(ValueError):
        contract.validate(manifest, "smalvik")
    manifest["images"]["e2e"] = "smalvik/biocad-e2e@sha256:" + "b" * 64
    manifest["version"] = "1.01.0"
    with pytest.raises(ValueError):
        contract.validate(manifest, "smalvik")


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "shell", "command": "id"},
        {"action": "report", "source_sha": "../../production/secrets.json"},
        {"action": "rollback", "environment": "../another-app"},
        {"action": "status", "path": "/etc/shadow"},
    ],
)
def test_dispatcher_rejects_arbitrary_operations_and_paths(payload):
    with pytest.raises(ValueError):
        server.dispatch(payload, {"namespace": "smalvik"})


def test_production_requires_exact_successful_staging_manifest(tmp_path, monkeypatch, manifest):
    monkeypatch.setattr(server, "ROOT", tmp_path)
    report = tmp_path / "reports" / manifest["source_sha"]
    report.mkdir(parents=True)
    staging = tmp_path / "staging"
    staging.mkdir()
    other = copy.deepcopy(manifest)
    other["images"]["web"] = "smalvik/biocad-web@sha256:" + "c" * 64
    (report / "staging.json").write_text(json.dumps({"status": "passed", "manifest": other}))
    (staging / "current.json").write_text(json.dumps(other))
    deploy = Mock()
    monkeypatch.setattr(server, "deploy", deploy)
    with pytest.raises(ValueError, match="Exact manifest"):
        server.dispatch({"action": "production", "manifest": manifest}, {"namespace": "smalvik"})
    deploy.assert_not_called()


def test_failed_smoke_restores_previous_images_without_restoring_database(tmp_path, monkeypatch, manifest):
    monkeypatch.setattr(server, "ROOT", tmp_path)
    directory = tmp_path / "production"
    directory.mkdir()
    previous = copy.deepcopy(manifest)
    previous["source_sha"] = "c" * 40
    (directory / "current.json").write_text(json.dumps(previous))
    monkeypatch.setattr(server, "compose", lambda env, m, s: (["compose", m["source_sha"]], {}))
    backup = Mock(return_value="actual-backup.dump")
    monkeypatch.setattr(server, "backup", backup)
    monkeypatch.setattr(server, "verify_local_images", Mock())
    commands = []
    monkeypatch.setattr(server, "run", lambda command, env, **kw: commands.append(command))
    smoke = Mock(side_effect=[RuntimeError("bad candidate"), None])
    monkeypatch.setattr(server, "smoke", smoke)
    with pytest.raises(RuntimeError, match="bad candidate"):
        server.deploy(
            "production",
            manifest,
            {"namespace": "smalvik", "production_url": "https://example.test"},
            tmp_path / "report",
        )
    backup.assert_called_once()
    assert commands[-1][:2] == ["compose", previous["source_sha"]]
    assert "--no-build" in commands[-1]
    assert not any("down" in cmd or "pg_restore" in cmd for cmd in commands)
    assert json.loads((directory / "current.json").read_text()) == previous


def test_version_bumps_feature_minor_and_fix_patch(monkeypatch):
    responses = iter(["v1.2.3", "common-base", "feat(map): avatars\nfix(api): validation"])
    monkeypatch.setattr(package, "git", lambda *args: next(responses))
    assert package.release_version() == "1.3.0"
    responses = iter(["v1.2.3", "common-base", "fix(api): validation"])
    assert package.release_version() == "1.2.4"
    monkeypatch.setattr(package, "git", lambda *args: "")
    assert package.release_version() == "1.0.0"


def test_digest_with_wrong_baked_source_revision_is_rejected(monkeypatch, manifest):
    labels = {"org.opencontainers.image.revision": "c" * 40}
    monkeypatch.setattr(contract.subprocess, "check_output", lambda *args, **kwargs: json.dumps(labels))
    with pytest.raises(ValueError, match="revision mismatch"):
        contract.verify_local_images(manifest)


def test_first_https_route_waits_for_certificate_without_recording_failed_smoke(
    monkeypatch, tmp_path, manifest
):
    calls = []

    def response(request, **kwargs):
        path = request.full_url.removeprefix("https://example.test")
        calls.append(path)
        if len(calls) == 1:
            raise server.URLError("certificate not issued yet")
        body = {
            "/version.json": {"git_sha": manifest["source_sha"]},
            "/api/v1/healthz": {"version": manifest["source_sha"]},
            "/api/v1/assistant/healthz": {"version": manifest["source_sha"]},
            "/api/v1/readyz": {"checks": {"postgres": True}},
            "/api/v1/auth/login": {"csrf_token": "fictional-test-only"},
            "/api/v1/auth/me": {"employee": {"id": "e01"}},
            "/api/v1/floors": {"items": [1, 2]},
        }.get(path, {})
        opened = MagicMock()
        opened.__enter__.return_value = opened
        opened.read.return_value = b'<div id="root"></div>' if path == "/" else json.dumps(body).encode()
        opened.headers = {"Set-Cookie": "fictional=demo; Secure; HttpOnly; SameSite=lax"}
        return opened

    client = Mock()
    client.open.side_effect = response
    monkeypatch.setattr(server.urllib.request, "build_opener", lambda *args: client)
    sleep = Mock()
    monkeypatch.setattr(server.time, "sleep", sleep)
    server.smoke("https://example.test", manifest, "production", tmp_path)
    sleep.assert_called_once_with(5)
    assert calls[-1] == "/api/v1/auth/logout"
    results = list(tmp_path.rglob("*-result.json"))
    assert len(results) == 1 and json.loads(results[0].read_text())["status"] == "passed"
