# WB-18 — verified interview playbook evidence

Continued **21 November 2026 Moscow**, [issue #41](https://github.com/smalvik/biocad-workspace/issues/41),
`docs/wb-18-interview-playbook` from develope8e29cf with final WB-10 notes carried as e7af1e4.
The original uncommitted Markdown changes were preserved. Documentation only, no runtime,
schema, frontend-flow or API change. Existing published baseline v1.4.2 remains historical.

## Actual documentation verification

18 sections /72 Q&A, four questions each, checked structurally and manually reviewed
against code/tests by the agent; this is not independent human approval or a claim
that a parser proves semantic correctness. Compared 13 listed commit IDs with local
Git history; they exist with corresponding merged PR subjects. Current GitHub release
v1.4.2/source4a40e18 verified before starting, no newer release assumed.

Corrected speculative API/shared-type/ACL claims, SMTP ambiguity, authenticated trace
policy, actual restricted SSH flow and disposable full regression vs persistent staging
smoke. New [PLAYBOOK](../interview/PLAYBOOK.md) distinguishes implemented/P1, explains
independent browser sessions, conflicts before cancellation, future writes vs historical
16 November seed, scripted provider vs actual archived free-model smoke and real
child RED/GREEN vs genuine WB-11 failure. Published `releases.json` is a release asset,
not an implemented in-product history. The original three-day target is not claimed met
by documentation completed on 21 November.

`python artifacts/wb18_check_links.py` was run on the changed Markdown set: relative
links missing0. `git diff --check`, configured-secret scan and branch/policy accompany
the staged commit. The ignored standalone personal-hours estimate is illustrative,
not approved/factual, not committed or published; README/AI-LOG keep hours unmeasured.

## Complete local real-service regression

`python artifacts/run_logged.py artifacts/WB-18-regression.log python scripts/check.py --run-type regression`
**PASS**, run **20261121T112324Z-e3bdea**, base **e7af1e4b336d2805aa1b2818d5823103f57180ac**, tree **dirty**:
**248 checks /35 commands exit0 /222 raw Allure**, 26 Vitest separate.
111 Booking/delivery +24 Assistant +20 Worker +2 persistence +5 recovery phases
+26 Vitest +60 desktop/mobile Playwright. Nested genuine RED2 failed/GREEN3 passed
remain attachments of the passing outer gate, not extra headline checks or xfail.
MCP/PostgreSQL/RabbitMQ/Mailpit real, LLM explicitly scripted; no new inference calls.
[Run metadata](../../artifacts/20261121T112324Z-e3bdea/run.json),
[actual log](../../artifacts/WB-18-regression.log).
No new unit/browser tests mirroring documentation were added; existing real behavioral
coverage validates the implementation described by the playbook.

## Initial preservation snapshot (before delivery)

Fresh counts before delivery: staging **7 bookings /
12 accounts**; production **9
bookings /12 accounts**. These are the actual
21 November baseline, not copied from old seven-booking release notes.
Individual IDs/fingerprints stay root-only on the server; only aggregates exported.
[Actual counts](../../artifacts/WB-18-data-before.json).
**23 unrelated containers** recorded. Final preservation results are below.
## Completed remote gates

| Gate | Actual result |
|---|---|
| [PR #42](https://github.com/smalvik/biocad-workspace/pull/42), head312f9a2 | [CI 44899736150 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44899736150); check/package pass, PR delivery correctly skipped |
| Develop merge | **9c30d7a096b3b1ad104a4413b21c8c6c0b990b16**, 2026-11-21T11:41:19Z UTC |
| Post-merge develop | [44900291312 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44900291312); complete CI/server regression and persistent staging smoke |
| [Promotion #43](https://github.com/smalvik/biocad-workspace/pull/43) | [44900329820 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44900329820); same-SHA complete nine-image manifests exactly equal |
| Main merge | **fb0d3428e3631e94e13f3bd2c0f8ddc15c01269d**, 2026-11-21T11:59:47Z UTC |
| Main | [44901696653 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44901696653); full CI/server/staging/production, exact digest promotion, aliases, release and Allure |

Reviews explicitly state **agent self-review**, not independent human approval.
Clean real develop server **20261121T114809Z-c8616b**, **248 checks /35 commands exit0 /
223 raw Allure** including staging smoke. Clean main server **20261121T121710Z-d1ed12**,
**248 /35exit0 /224 raw Allure** (222 regression + stage/prod2; Vitest26 separate).
[Develop metadata](../../artifacts/WB-18-develop-delivery/server/9c30d7a096b3b1ad104a4413b21c8c6c0b990b16/20261121T114809Z-c8616b/run.json),
[main metadata](../../artifacts/WB-18-main-delivery/server/fb0d3428e3631e94e13f3bd2c0f8ddc15c01269d/20261121T121710Z-d1ed12/run.json),
[build-once proof](../../artifacts/WB-18-build-once-proof.json).
Raw expected child failures remain real attachments of the passing sensitivity gate;
Allure UI can group phase/history identities and does not promise 224 visible rows.

Published **[v1.4.3](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.3)**, **2026-11-21T12:27:48Z UTC**,
non-draft/non-prerelease, exact source **fb0d3428e3631e94e13f3bd2c0f8ddc15c01269d**. Same complete nine-image/schema2
main manifest in staging and production, four runtime version/latest aliases after smoke.

### Preserved first failure and capacity recovery

Main attempt1 passed check/package, then refused before starting server regression:
the diagnostic inventory after the refusal measured **4,134,772 KiB available RAM**
(about3.94 GiB), below the unchanged
**4,194,304 KiB /4 GiB** preflight minimum; disk had about31.3 GiB free.
No main server test ran and no production deployment occurred in that attempt.
[Actual first-attempt jobs](../../artifacts/WB-18-main-attempt1.json),
[original failure log](../../artifacts/WB-18-main-failed-attempt1.log).
An explicit scoped operational recovery checked ownership marker/project labels,
acquired the existing deploy lock and temporarily stopped only seven **private
biocad-staging** containers, retaining volumes. Production remained v1.4.2 and foreign
projects were not stopped. Available RAM became **4,502,268 KiB** (about4.29 GiB).
[Actual recovery](../../artifacts/WB-18-capacity-recovery.json).
`gh run rerun 44901696653 --failed` reran only delivery as **attempt2**, using
the already built immutable main candidate; check/package were not rebuilt.
Attempt2 passed full regression/staging/production and restored all seven staging
services. The resource guard was not weakened. Automated capacity recovery is not
implemented; future heavy gates still require the documented resource budget.

## Independent public proof and final preservation

Public application **4 desktop/mobile PASS**, no booking writes/inference.
Allure latest + original v1.3.0 live report **4 PASS**, downloads0; HTTP
inline/content-type/source/checksum PASS. Additionally the documented path
Behaviors → race-red-green → Race sensitivity → red.log/green.log was exercised
in **2 desktop/mobile checks PASS**, real NONOVERLAP_INVARIANT/2failed and 3passed
visible, downloads0. This validates the new interview instructions.
[App result](../../artifacts/WB-18-production-browser/run.json),
[report UI result](../../artifacts/WB-18-allure-production-browser/run.json),
[actual expanded race logs](../../artifacts/WB-18-race-production-browser/run.json).
[Open app](https://biocad.smalvik.dev),
[versioned Allure](https://biocad.smalvik.dev/allure/v1.4.3/).

All **14 own containers healthy/running**; **23 unrelated
container IDs/images/start times/restart counts unchanged**. Original staging
**7 bookings /12 accounts**,
production **9 bookings /12 accounts**
preserved, changed/missing0. Current counts can grow through legitimate user activity;
individual identifiers/fingerprints remain server-only, root0600.
[Final aggregate data check](../../artifacts/WB-18-data-final.json),
[container comparison](../../artifacts/WB-18-preservation-proof.json),
[filtered server state](../../artifacts/WB-18-final-server-state.json).
Sampled foreign HTTP results are recorded separately and not claimed healthy merely
because they match baseline. Worker healthy both, outbox/jobs/queues drained;
sent/captured counts are actual values in [notification audit](../../artifacts/WB-18-final-notifications.json).

Previous production **v1.4.2 /4a40e18** and validated backups retained:
staging **20261121T122535-3afd24.dump /29722 bytes**,
production **20261121T122604-dc6c82.dump /32238 bytes**.
No raw snapshots/backups in public assets, proxy/DNS/daemon change, DB migration,
foreign-project mutation, external SMTP or new task LLM call.

Personal-hours estimate remains a separate ignored illustrative draft pending owner
review, not published accounting or a claim of human code review. Next planned P1:
**WB-12 free-model failover**, still subject to the free-only/$0 constraint. Remaining
comfort/quiz/feedback/timeline/release-history UI are not claimed implemented.
