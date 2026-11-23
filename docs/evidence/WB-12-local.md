# WB-12 local evidence — 23 November 2026 Moscow

Issue [#44](https://github.com/smalvik/biocad-workspace/issues/44),
`feat/wb-12-llm-failover`, base `1219797795658d182c31315f43217a39e341728d`,
working tree **dirty**, unreleased. This is pre-commit evidence, not production proof.

Actual command: `python scripts/check.py --run-type regression`, through
`python artifacts/run_logged.py artifacts/WB-12-local-regression.log ...`.
Run **20261123T075832Z-5fd8c1**, result passed, **35 commands exit0**:

| Checks | Passed |
|---|---:|
| Booking and delivery unit/integration | 111 |
| Assistant unit/integration | 51 |
| Notification Worker | 20 |
| PostgreSQL persistence phases | 2 |
| Real broker/SMTP outage/recovery phases | 5 |
| React Vitest | 26 |
| Desktop/mobile Playwright | 62 |
| Total | 277 |

Raw Allure **251 passed**, Vitest26 separately. Evidence retained locally in
`artifacts/20261123T075832Z-5fd8c1/{run.json,allure-results}` and the command log.
No fabricated CI URL or remote deployment is attributed to this run.

The provider is explicitly scripted, but PostgreSQL/RabbitMQ/STDIO MCP are real.
New integration proves primary failure → fallback → live availability/proposal,
zero pre-confirmation booking writes and concurrent same-key confirmations yielding
one booking. New desktop/mobile cases verify the required fallback warning; existing
both-model outage cases successfully complete manual form bookings. Disposable test
projects/volumes were cleaned; developer/production data were not used.

Focused Docker Ruff and Assistant `pytest -q tests/unit` passed **43 tests**;
the shared-budget test was strengthened after the full run to exhaust attempts
across primary and backup, then the same 43 unit tests passed again (5.28 s).
Initial focused Ruff import ordering failed, was corrected and rechecked.
React TypeScript/Vite build passed. Full CI must validate the final committed tree.

Real-free backup acceptance is separate and **did not pass**. Initial isolated live harness
startup found a missing healthcheck on its test-image override; the harness was
corrected and six owned local services became healthy. This was not a production
failure. No paid route is enabled; all inference requires fresh catalog verification
and zero prompt/completion/request caps.

The isolated API/desktop/mobile live attempt returned503 in all three cases:
the Docker catalog GET returned403 "Access denied by security policy", before
inference. Results are retained under `artifacts/WB-12-live-acceptance`; the
explicitly simulated primary fault never reached its inference stage. No response
from a real backup is claimed. Owned live-test containers/volumes were removed.

Separate actual host probes, each with a fresh zero-price/tool catalog and zero
caps (fictional clarification only, no booking writes):

| Model | HTTP result |
|---|---|
| Nvidia Nemotron3.5 Lightning free | 404: no endpoints matching Free model training policy |
| Existing Ling3.2 Flash free | 429: provider returned error |
| Gemma4 26B free | 429: provider returned error, 32.92 seconds |
| Liquid LFM3 1.7B free | 404: no endpoints matching Free model training policy |

No success/zero `usage.cost` response was obtained. No charge is inferred from
catalog prices alone. Privacy settings and `data_collection=deny` were preserved;
no paid routing, credits or training opt-in. Reject Nvidia/Liquid as current backup
candidates; Gemma4 is a candidate only, pending actual successful acceptance.
Probe logs and sanitized endpoint metadata are retained in ignored artifacts.

Remote SSH currently times out on port22 from both Windows and Docker; HTTPS443
connects. The earlier VPN interface is absent. No server/DNS/proxy/firewall change
was made, and no WB-12 deployment is claimed. The user was asked to restore the
previous VPN path or provide updated SSH connection details.
