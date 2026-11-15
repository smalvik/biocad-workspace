"""Opt-in real-provider acceptance. Proposal-only; never confirms/cancels a booking."""

import argparse
import json
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
UTC = timezone.utc  # noqa: UP017 -- keep server Python 3.10 compatibility


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--expected-sha", default="", help="Optional exact deployed source SHA")
    parser.add_argument(
        "--allow-free-live", action="store_true", help="Explicit opt-in to real zero-price inference"
    )
    args = parser.parse_args()
    if not args.allow_free_live or not args.expected_model.endswith(":free"):
        parser.error("Real inference requires --allow-free-live and an explicitly free model variant")
    url = urlsplit(args.base_url)
    if (
        url.hostname not in {"localhost", "127.0.0.1", "web", "biocad.smalvik.dev"}
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
        or url.scheme not in {"http", "https"}
        or (url.hostname == "biocad.smalvik.dev" and url.scheme != "https")
    ):
        parser.error("Use the known BIOCAD HTTPS origin or the isolated local test stack")
    base = args.base_url.rstrip("/")
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    csrf = ""

    def request(path, body=None):
        headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf}
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        with opener.open(
            urllib.request.Request(base + path, data=data, headers=headers), timeout=75
        ) as response:
            if response.status == 204:
                return None
            return json.load(response)

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    output = ROOT / "artifacts" / ("WB-06-live-" + stamp)
    results = output / "allure-results"
    results.mkdir(parents=True)
    report = {
        "run_id": stamp,
        "base_url": base,
        "expected_model": args.expected_model,
        "provider_mode": "real OpenRouter, not scripted",
        "booking_writes_attempted": 0,
        "working_tree": os.environ.get("WORKING_TREE", "unknown"),
        "cases": [],
    }
    success = False
    try:
        identity = request(
            "/api/v1/auth/login",
            {"username": "e12", "password": os.environ.get("DEMO_PASSWORD", "demo-workspace")},
        )
        csrf = identity["csrf_token"]
        assert identity["employee"]["fictional"] is True
        health = request("/api/v1/assistant/healthz")
        report["source_sha"] = health["version"]
        if args.expected_sha:
            assert health["version"] == args.expected_sha, "Unexpected deployed source SHA"
        before = request("/api/v1/bookings/me")["items"]
        floors = request("/api/v1/floors")["items"]
        floor = next(row for row in floors if row["number"] == 2)
        zone = timezone(timedelta(hours=3))
        start = (datetime.now(zone) + timedelta(days=3)).replace(hour=12, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        context = {
            "floor_id": floor["id"],
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "floors": [{key: row[key] for key in ("id", "name", "number")} for row in floors],
        }
        period = f"{start:%d.%m.%Y} с 12:00 до 13:00 МСК, на втором этаже"
        cases = [
            ("meeting room for six", "Найди переговорную на 6 человек " + period, "MEETING_ROOM"),
            ("FreeDesk near fictional Anna", "Найди FreeDesk рядом с Анной Смирновой " + period, "DESK"),
            ("missing date and time", "Найди переговорную", None),
        ]
        for name, message, kind in cases:
            started = int(time.time() * 1000)
            case = {"name": name, "status": "failed"}
            try:
                data = request(
                    "/api/v1/assistant/chat",
                    {"message": message, "history": [], "context": context, "consent": True},
                )
                assert data["scripted_test"] is False, "A scripted provider is not live acceptance"
                assert data["model"] == args.expected_model, "Unexpected requested model"
                case.update(model=data["model"], tools_used=data["tools_used"])
                calls = data["provider_calls"]
                assert calls and all(
                    call["cost"] == 0 and call["model"] == args.expected_model for call in calls
                )
                case["provider_calls"] = calls
                if kind:
                    proposal = data["proposal"]
                    assert proposal["space"]["kind"] == kind
                    assert proposal["space"]["is_available_for_full_interval"] is True
                    assert proposal["floor"]["number"] == 2
                    if kind == "MEETING_ROOM":
                        assert proposal["space"]["capacity"] >= 6
                    else:
                        assert "search_employees" in data["tools_used"]
                    assert "propose_booking" in data["tools_used"]
                    selection = proposal["selection"]
                    assert datetime.fromisoformat(selection["start_at"].replace("Z", "+00:00")) == start
                    assert datetime.fromisoformat(selection["end_at"].replace("Z", "+00:00")) == end
                    case["selection"] = selection  # Opaque signed token is deliberately excluded.
                else:
                    assert data["proposal"] is None and "ask_clarification" in data["tools_used"]
                case["status"] = "passed"
            finally:
                report["cases"].append(case)
                labels = {
                    "suite": "live_llm",
                    "run_type": "smoke",
                    "environment": base,
                    "git_sha": report["source_sha"],
                    "llm_mode": "real OpenRouter",
                }
                result = {
                    "uuid": str(uuid4()),
                    "name": name,
                    "fullName": "assistant.live." + name,
                    "status": case["status"],
                    "start": started,
                    "stop": int(time.time() * 1000),
                    "labels": [{"name": key, "value": value} for key, value in labels.items()],
                }
                (results / (result["uuid"] + "-result.json")).write_text(json.dumps(result), encoding="utf-8")
        assert (
            request("/api/v1/bookings/me")["items"] == before
        ), "Proposal-only check must not change bookings"
        success = True
    except Exception as error:
        # No raw HTTP response, cookie, request body or credential enters evidence.
        report["failure_type"] = type(error).__name__
    finally:
        if csrf:
            try:
                request("/api/v1/auth/logout", {})
            except Exception:
                pass
        report["result"] = "passed" if success else "failed"
        (output / "run.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Live acceptance: {report['result']}; evidence {output.relative_to(ROOT)}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
