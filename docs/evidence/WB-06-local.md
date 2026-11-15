# WB-06 local evidence — 2026-11-15

Issue [#22](https://github.com/smalvik/biocad-workspace/issues/22), branch
`feat/wb-06-assistant-mcp`. Production remains published v1.2.0.

Command: `python artifacts/run_logged.py artifacts/WB-06-final-regression.log python scripts/check.py --run-type regression`.
Run **20261115T113244Z-e7d765**, base HEAD **04a0da22040592a581500af692bb6111bb4af363**,
working tree **dirty**, result **passed**, **20 commands / all exit 0**.

- **180 passed** = 78 Booking/delivery + 16 Assistant + 2 restart persistence +
  26 Vitest + 58 desktop/mobile Playwright. **154 passed Allure results**;
  Vitest results are recorded separately, not invented as Allure cases.
- [Commands](../../artifacts/20261115T113244Z-e7d765/commands.log),
  [metadata](../../artifacts/20261115T113244Z-e7d765/run.json),
  [Allure standalone HTML](../../artifacts/20261115T113244Z-e7d765/allure-report/index.html),
  [raw Allure](../../artifacts/20261115T113244Z-e7d765/allure-results/).
- Real PostgreSQL/RabbitMQ and official SDK MCP STDIO transport: discovery, all
  four read tools, selected-time search near fictional Anna, real details, proposal
  without write, CSRF, cross-user rejection, idempotent concurrent confirmation,
  racing reservation conflict, manual booking after provider outage.
- Real PostgreSQL quota test: ten concurrent reservations against a 0.10 USD
  synthetic cap yield exactly two successes / eight rejected; same-ID replay is
  not charged twice, recreating the connection pool does not reset the cap.
- Browser: consent, request/proposal/map highlight, no write before explicit
  confirmation, exact payload/result, mobile usable proposal action, provider
  failure/manual create, clarification, close pending chat and ignore late result.
- HTTP provider is **scripted**, isolated and explicitly labelled. No actual
  OpenRouter inference is implied by these results. The OpenRouter key passed
  a separate read-only validity check; **0 paid inference requests** so far.

Follow-up review changes after this full run: reject the known local signing key
outside local, enforce explicit ISO offsets including rejection of epoch strings,
hide configuration input values in exception text, clear AI proposal on later
manual map/search/filter selection, and attach a proposal screenshot in browser CI.
Current mounted-source Assistant unit command passed **11 tests**, exit 0;
Ruff / TypeScript passed. CI must validate the final committed snapshot; the dirty
run above is not labelled as a pass of a later commit.

Earlier outcomes retained:

| Run | Actual outcome |
|---|---|
| 20261115T111337Z-4e6573 | Failed: SDK returned text instead of structured output; async fixture loop mismatch. Corrected typed output and function loop scope. |
| 20261115T112131Z-47a1d0 | Backend 78 / Assistant 13 / persistence 2 / Vitest 26 passed; Playwright 57 passed, one mobile AI action occluded by resource drawer. Corrected UI, normal click retained. |
| 20261115T112714Z-54bd2c | Passed 179 = 78 + 15 + 2 + 26 + 58, Allure 153, launcher exit 0. |

No WB-06 merge, server rollout or release is claimed. Model and spending approval
are still required for real-provider acceptance; manual booking on v1.2.0 remains live.

Committed implementation **89ad3d5b4e0ce195b85b646a12e6a8354e6cd0a3** passed
[PR CI 43710246930](https://github.com/smalvik/biocad-workspace/actions/runs/43710246930):
**181 checks** = 78 + 17 + 2 + 26 + 58, **155 Allure**. Run metadata
`20261115T114304Z-dd647d`, working_tree clean. Check and seven immutable candidate
publication jobs succeeded; staging/production job was correctly skipped on a draft
feature PR. Artifacts: `checks-43710246930-1`, `candidate-43710246930`.
Follow-up changes prepare the opt-in live acceptance CLI and record this evidence;
they do not change the tested runtime behavior. CI for each later head is tracked separately.
