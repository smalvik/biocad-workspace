# Historical pause / resumed release completed

**User resumed on 2026-11-15; v1.3.0 is now published and deployed.**
Main 19a8388; develop 887bcc1. Paused workflow attempt 2 and main workflow passed;
real free staging/production and desktop/mobile acceptance passed, all cost=0.
Next task WB-07. [Current evidence](../evidence/WB-06-remote.md).
The original stopping point below is retained as history and is superseded by this update.

# Paused — 2026-11-15 17:15 MSK

**Later update: user explicitly resumed on 2026-11-15.** The historical stopping
point below remains evidence. Run 43722878517 was requested again; see CURRENT_STATE
and current GitHub status for ongoing results. Free-only consent remains in force.

Explicit user request: «поставь на паузу, продолжим в следующей сессии».
Do not resume work until asked. No main promotion or new release has happened.

## Exact state

- Current local branch `fix/wb-11-free-assistant-planning`, code HEAD
  **993ddbed4f73b1c80e3ca2674dbdc966862c6b05**. Pause notes are saved locally,
  uncommitted/unpushed; preserve them when resuming.
- WB-06 issue [#22](https://github.com/smalvik/biocad-workspace/issues/22),
  [PR #23 merged](https://github.com/smalvik/biocad-workspace/pull/23) into develop
  **c85b8dc8beb0e97197d2bf8b9dfd3c7a9cdda7ba**. Feature CI passed 188 checks;
  [develop/server/staging run 43719293194 passed](https://github.com/smalvik/biocad-workspace/actions/runs/43719293194).
- Real staging room case passed, but near-Anna repeated search and exhausted the
  4-round limit. Failed proof retained:
  `artifacts/WB-06-server-staging-WB-06-live-20261115T134519Z-84d1f2/`.
- Separate defect [issue #24](https://github.com/smalvik/biocad-workspace/issues/24),
  [PR #25 merged](https://github.com/smalvik/biocad-workspace/pull/25), source 993ddbe.
  Controller now immediately calls real MCP recheck/propose after positive filtered
  availability; no write, exact signed period/owner, explicit human confirmation,
  8-tool cap. Temperature 0 and clearer search/clarification instructions.
- **Remote develop: 887bcc18f430974fc7231ed6726a1cd037df0de1**.
  [PR fix CI 43722095606 passed](https://github.com/smalvik/biocad-workspace/actions/runs/43722095606).
  Post-merge [43722878517 intentionally cancelled](https://github.com/smalvik/biocad-workspace/actions/runs/43722878517)
  for the pause: check succeeded, publication cancelled, staging/deployment cancelled
  before running. This run must be rerun, not reported as passed.
- **Production/main: v1.2.0 / bddba674f9966164016d4f6102702074dab41b5e**.
  **Staging: v1.3.0 candidate / c85b8dc**, without the planning fix.
  No main-promotion PR or published v1.3.0 release exists.

## Free-only consent and proof

User chose **«Только бесплатная модель»**. Never use paid inference/fallback,
increase a spending allowance or buy credits. Primary:
`inclusionai/ling-3.2-flash:free`, monetary budget **0**. Catalog zero-price/tool
checks plus prompt/completion/request max_price=0 apply on every attempt.
One bounded same-model 429 retry only. Decision is in DECISIONS.md.

- Local fix regression `20261115T135319Z-f781d9`: **189 passed** = 79 Booking/delivery
  + 24 Assistant + 2 persistence + 26 Vitest + 58 Playwright, Allure **163**,
  all 20 commands exit 0. Base c85b8dc / dirty, not a later clean-head claim.
- Actual free fix run `20261115T135746Z-0e5c21`: **3 cases passed**, 4 successful
  provider responses all cost=0, no booking writes. Metadata and standalone Allure:
  `artifacts/WB-06-live-20261115T135746Z-0e5c21/`.
- Earlier actual desktop/mobile free-browser flow passed through chat/map/exact
  confirmation, booking writes blocked/count=0: `artifacts/WB-06-free-live-browser/`.
  This is a pre-fix local build, not a production/current-main proof.
- CI HTTP provider is explicitly scripted, with real MCP/RabbitMQ/PostgreSQL;
  do not present deterministic regression as actual LLM proof.

## Server safety / helpers

- Root-only BIOCAD tooling and free-model config were prepared; original DB/session/
  broker/demo secrets preserved. No proxy/DNS/other-app change. Credentials remain
  in ignored `.env`/artifacts; never print or commit them.
- Existing helpers: `artifacts/github_ops.py gh|git ...`, pinned-key
  `artifacts/server_ops.py`, and `artifacts/wb06_free_server.py`.
- Real server acceptance after deployment:
  `python artifacts/wb06_free_server.py live staging EXPECTED_40_HEX_SHA`.
  It executes the tracked proposal-only CLI, pins source SHA, downloads sanitized
  metadata/Allure, never confirms a booking. Staging uses a test-client cookie
  exception scoped to private localhost:18081; production uses real HTTPS.
- Pre-change existing-container inventory: `artifacts/WB-06-server-baseline.json`.
  Final preservation comparison for the 23 non-BIOCAD containers is still required.
- Auto-review rejected exporting production account/booking IDs and row digests.
  The rejected command never ran. Approved safer alternative retains them only on
  the same server in root-only 0600
  `/opt/biocad/production/backups/wb06-preservation-before.json`.
  Only counts exported: `artifacts/WB-06-data-before-counts.json`, 7 bookings /
  12 accounts per environment. **Do not download that snapshot or repeat the export.**
  `artifacts/wb06_data_preservation.sh` performs server-only comparison. Its capture
  path exists; on resume consider legitimate user changes during the pause and
  take a fresh server-only baseline in a separate file before further rollout.
- Temporary local live Compose projects have been stopped/removed with their own
  volumes; other local apps were not touched. No live inference process is running.

## Resume after explicit user instruction

1. Read AGENTS/CURRENT_STATE/this handoff, inspect git status, retain pause notes.
2. Rerun the intentionally cancelled workflow:
   `python artifacts/github_ops.py gh run rerun 43722878517`.
   Require full checks/publication/server regression/staging success on 887bcc1.
   Existing partial SHA candidates may be reused by the immutable publisher.
3. Run real free staging acceptance on exact 887bcc18f430974fc7231ed6726a1cd037df0de1.
   Require all 3 cases pass and all actual provider costs 0; retain failures.
4. Only then reviewed PR develop -> main, green PR CI, merge and established main
   pipeline: exact main-SHA images -> stage/regress -> production -> HTTPS smoke ->
   version/latest and real release. Existing authorization covers this workflow.
5. Verify actual production/free API and desktop/mobile flow without booking
   writes, original containers, and server-only data integrity with aggregate output.
   Record real release/digests/Allure evidence; update notes/progress/AI-LOG and close
   completed issues. WB-07 notifications is next P0 after WB-06 acceptance.

Browser incident #21 is monitoring: user says access restored; no alternate ingress
or permanent network-cause fix is claimed. Do not restart DNS/proxy work by default.
