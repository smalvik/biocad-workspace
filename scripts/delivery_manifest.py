"""Immutable delivery contract shared by CI and the restricted server dispatcher."""

import json
import re
import subprocess
from pathlib import Path

LEGACY_SERVICES = ("booking", "assistant", "web", "booking-tests", "assistant-tests", "web-tests", "e2e")
SERVICES = (*LEGACY_SERVICES, "notification", "notification-tests")
RUNTIME = ("booking", "assistant", "web", "notification")


def runtime_services(manifest: dict):
    return tuple(name for name in RUNTIME if name in manifest["images"])


SHA = re.compile(r"[0-9a-f]{40}")
VERSION = re.compile(r"1\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
NAMESPACE = re.compile(r"[a-z0-9][a-z0-9_-]{1,38}")


def validate(manifest: dict, namespace: str) -> dict:
    if not NAMESPACE.fullmatch(namespace):
        raise ValueError("Invalid Docker Hub namespace")
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "source_sha", "version", "images"}:
        raise ValueError("Unexpected manifest fields")
    if (
        type(manifest["schema"]) is not int
        or manifest["schema"] not in {1, 2}
        or not isinstance(manifest["source_sha"], str)
        or not SHA.fullmatch(manifest["source_sha"])
    ):
        raise ValueError("Invalid source SHA")
    if not isinstance(manifest["version"], str) or not VERSION.fullmatch(manifest["version"]):
        raise ValueError("Expected SemVer 1.MINOR.PATCH without leading zeros")
    expected_services = SERVICES if manifest["schema"] == 2 else LEGACY_SERVICES
    if not isinstance(manifest["images"], dict) or set(manifest["images"]) != set(expected_services):
        raise ValueError("Expected the complete runtime and regression image set")
    for service, reference in manifest["images"].items():
        expected = rf"{re.escape(namespace)}/biocad-{service}@sha256:[0-9a-f]{{64}}"
        if not isinstance(reference, str) or not re.fullmatch(expected, reference):
            raise ValueError(f"Only an immutable allowed {service} repository is accepted")
    return manifest


def load(path: Path, namespace: str) -> dict:
    return validate(json.loads(path.read_text(encoding="utf-8")), namespace)


def image_environment(manifest: dict) -> dict[str, str]:
    return {
        **{name.upper().replace("-", "_") + "_IMAGE": value for name, value in manifest["images"].items()},
        "GIT_SHA": manifest["source_sha"],
        "RELEASE_VERSION": manifest["version"],
    }


def verify_local_images(manifest: dict, services=None) -> None:
    """Inspect only public OCI labels; never dump Config.Env or container secrets."""
    for service in manifest["images"] if services is None else services:
        labels = (
            json.loads(
                subprocess.check_output(
                    [
                        "docker",
                        "image",
                        "inspect",
                        manifest["images"][service],
                        "--format",
                        "{{json .Config.Labels}}",
                    ],
                    text=True,
                )
            )
            or {}
        )
        if labels.get("org.opencontainers.image.revision") != manifest["source_sha"]:
            raise ValueError(f"Image source revision mismatch: {service}")
        if labels.get("org.opencontainers.image.source") != "https://github.com/smalvik/biocad-workspace":
            raise ValueError(f"Image source repository mismatch: {service}")
