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

## Initial preservation snapshot and pending remote gates

Fresh counts before delivery: staging **7 bookings /
12 accounts**; production **9
bookings /12 accounts**. These are the actual
21 November baseline, not copied from old seven-booking release notes.
Individual IDs/fingerprints stay root-only on the server; only aggregates exported.
[Actual counts](../../artifacts/WB-18-data-before.json).
**23 unrelated containers** recorded. Final preservation is not preclaimed.
PR, clean CI, post-merge server/staging, promotion/main and release remain pending;
results and published URLs will be recorded only after completion.
