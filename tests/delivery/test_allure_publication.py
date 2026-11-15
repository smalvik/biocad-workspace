"""Publication boundaries: only real release HTML, atomic latest and preserved history."""

import copy
import hashlib
import json
import sys
from unittest.mock import MagicMock, Mock

import allure
import pytest

sys.path.insert(0, "/delivery")
import deploy_server as server  # noqa: E402
import publish_allure as publisher  # noqa: E402
from delivery_manifest import SERVICES  # noqa: E402

pytestmark = [allure.suite("regression"), allure.feature("delivery-allure")]


@pytest.fixture
def release(tmp_path, monkeypatch):
    manifest = {
        "schema": 1,
        "source_sha": "a" * 40,
        "version": "1.3.0",
        "images": {name: f"smalvik/biocad-{name}@sha256:{'b' * 64}" for name in SERVICES},
    }
    bodies = {
        "candidate.json": json.dumps(manifest).encode(),
        "index.html": b"<!doctype html><html><title>Allure Report</title>regression</html>",
        "live-llm-allure.html": b"<html><title>Allure Report</title>real free live</html>",
    }
    data = {
        "tag_name": "v1.3.0",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-11-15T17:04:06Z",
        "assets": [],
    }
    for name, body in bodies.items():
        data["assets"].append(
            {
                "name": name,
                "state": "uploaded",
                "size": len(body),
                "digest": "sha256:" + hashlib.sha256(body).hexdigest(),
                "browser_download_url": publisher.DOWNLOAD + "v1.3.0/" + name,
            }
        )

    def download(url, limit, digest=None):
        if url.startswith(publisher.API):
            return json.dumps(data).encode()
        return bodies[url.rsplit("/", 1)[-1]]

    monkeypatch.setattr(publisher, "download", download)
    directory = tmp_path / "public/allure"
    directory.mkdir(parents=True)
    return manifest, data, bodies, directory


def test_publishes_inline_documents_and_preserves_version_on_repeat(release):
    manifest, _, bodies, directory = release
    result = publisher.publish(manifest, directory)
    assert result["status"] == "passed"
    assert (directory / "index.html").read_bytes() == bodies["index.html"]
    assert (directory / "v1.3.0/live/index.html").read_bytes() == bodies["live-llm-allure.html"]
    assert json.loads((directory / "latest.json").read_text())["manifest"] == manifest
    stamp = (directory / "v1.3.0/index.html").stat().st_mtime_ns
    publisher.publish(manifest, directory)
    assert (directory / "v1.3.0/index.html").stat().st_mtime_ns == stamp
    assert not (directory / "candidate.json").exists()


@pytest.mark.parametrize(
    "field,value", [("draft", True), ("prerelease", True), ("published_at", None), ("tag_name", "v1.2.0")]
)
def test_rejects_unpublished_or_other_release(release, field, value):
    manifest, data, _, directory = release
    data[field] = value
    with pytest.raises(ValueError, match="published stable"):
        publisher.publish(manifest, directory)
    assert not list(directory.iterdir())


@pytest.mark.parametrize(
    "field,value",
    [
        ("browser_download_url", "https://example.test/private"),
        ("state", "new"),
        ("digest", None),
        ("size", 1),
    ],
)
def test_rejects_foreign_unverified_or_incomplete_asset(release, field, value):
    manifest, data, _, directory = release
    data["assets"][0][field] = value
    with pytest.raises(ValueError):
        publisher.publish(manifest, directory)
    assert not list(directory.iterdir())


def test_failed_or_changed_publication_keeps_previous_latest(release):
    manifest, data, bodies, directory = release
    publisher.publish(manifest, directory)
    previous = (directory / "index.html").read_bytes()
    bodies["index.html"] = b"<html><title>Allure Report</title>different report</html>"
    data["assets"][1].update(
        size=len(bodies["index.html"]), digest="sha256:" + hashlib.sha256(bodies["index.html"]).hexdigest()
    )
    with pytest.raises(ValueError, match="immutable"):
        publisher.publish(manifest, directory)
    assert (directory / "index.html").read_bytes() == previous
    bodies["candidate.json"] = json.dumps({**manifest, "source_sha": "c" * 40}).encode()
    with pytest.raises(ValueError, match="match deployed"):
        publisher.publish(manifest, directory)
    assert (directory / "index.html").read_bytes() == previous


def test_missing_optional_live_asset_does_not_claim_live_acceptance(release):
    manifest, data, _, directory = release
    data["assets"] = data["assets"][:2]
    result = publisher.publish(manifest, directory)
    assert result["reports"] == ["index.html"]
    assert not (directory / "v1.3.0/live").exists()


def test_later_live_acceptance_is_append_only(release):
    manifest, data, bodies, directory = release
    live = data["assets"].pop()
    publisher.publish(manifest, directory)
    original = (directory / "v1.3.0/index.html").read_bytes()
    data["assets"].append(live)
    publisher.publish(manifest, directory)
    assert (directory / "v1.3.0/index.html").read_bytes() == original
    assert (directory / "v1.3.0/live/index.html").read_bytes() == bodies["live-llm-allure.html"]


def test_rejects_symlink_publication_directory(release, tmp_path):
    manifest, _, _, directory = release
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="owned publication"):
        publisher.publish(manifest, alias)


@pytest.mark.parametrize(
    "body,digest,origin,limit",
    [
        (b"html", "sha256:" + "0" * 64, "https://github.com/report", 20),
        (b"x" * 21, None, "https://github.com/report", 20),
        (b"html", None, "http://github.com/report", 20),
        (b"html", None, "https://foreign.test/report", 20),
    ],
)
def test_download_rejects_bad_checksum_size_or_origin(monkeypatch, body, digest, origin, limit):
    response = MagicMock()
    response.__enter__.return_value = response
    response.url = origin
    response.read.return_value = body
    monkeypatch.setattr(publisher.urllib.request, "urlopen", lambda *a, **kw: response)
    with pytest.raises(ValueError):
        publisher.download(publisher.DOWNLOAD + "v1.3.0/index.html", limit, digest)


def test_dispatcher_requires_exact_current_production_manifest(release, tmp_path, monkeypatch):
    manifest, _, _, _ = release
    monkeypatch.setattr(server, "ROOT", tmp_path)
    production = tmp_path / "production"
    production.mkdir()
    previous = copy.deepcopy(manifest)
    previous["source_sha"] = "c" * 40
    (production / "current.json").write_text(json.dumps(previous))
    publish = Mock()
    monkeypatch.setattr(server, "publish_allure", publish)
    with pytest.raises(ValueError, match="current production"):
        server.dispatch({"action": "publish-allure", "manifest": manifest}, {"namespace": "smalvik"})
    with pytest.raises(ValueError, match="Unsupported"):
        server.dispatch(
            {"action": "publish-allure", "manifest": manifest, "url": "/etc/shadow"}, {"namespace": "smalvik"}
        )
    publish.assert_not_called()
