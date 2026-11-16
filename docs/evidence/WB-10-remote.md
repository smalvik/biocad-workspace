# WB-10 — local reproducibility and delivery evidence

Issue [#38](https://github.com/smalvik/biocad-workspace/issues/38), branch
`docs/wb-10-delivery-evidence` from develop05e08e6; WB-08 final notes carried as e301cb3.
The implementation changes Markdown only, with no runtime/schema/API/frontend-flow change.

## Actual fresh local launch

`python artifacts/run_logged.py artifacts/WB-10-local-docs.log python artifacts/wb10_local_docs.py`
executes the README Compose command shape with a unique `-p biocad-wb10-docs-30b665ee95`
and free loopback ports instead of occupying existing localhost development ports.
`docker compose --env-file .env.example -f infra/compose.yaml up -d --build --wait`
really builds/starts **7 services, all healthy**; no private `.env` or external LLM is used.
The existing two read-only map/employee scenarios run on desktop/mobile: **4 PASS**.
Tests use the immutable v1.4.1 E2E image (source5364c9e); the launched app is built
from base **e301cb3291ea86e6aab669b56d8bed8a7842c0fe**, tree **dirty** (documentation changes).
The test project and only its own volumes/network are removed, cleanup exit0.
[Run metadata](../../artifacts/biocad-wb10-docs-30b665ee95/run.json),
[actual log](../../artifacts/WB-10-local-docs.log),
[actual Allure smoke](../../artifacts/biocad-wb10-docs-30b665ee95/allure-results).

## Architecture and static checks

Real Mermaid parse and Chromium SVG rendering, tooling version11.4.1:
**3 PASS**, C1 **7 nodes**, C2 **15**, Assistant **7**. Inspected C2 screenshot and
shortened two wrapping cluster headings, then rendered the final diagrams again.
[Tool result](../../artifacts/WB-10-mermaid/run.json),
[C1 SVG](../../artifacts/WB-10-mermaid/C1.svg), [C2 SVG](../../artifacts/WB-10-mermaid/C2.svg).
Relative Markdown/code links and configured-secret checks are run against staged files;
policy checks use the actual WB-10 branch and Conventional Commit title.
No unit tests mirroring prose or new product browser flow tests were added.
README states active hours are unmeasured; user was asked, no numbers are invented.
The AI-LOG distinguishes user decisions, agent implementation and explicit agent self-review.

## Complete real-service regression before PR

`python artifacts/run_logged.py artifacts/WB-10-regression.log python scripts/check.py --run-type regression`
**PASS**, run **20261116T012006Z-46c1a7**, base **e301cb3291ea86e6aab669b56d8bed8a7842c0fe**, tree **dirty**:
**248 checks**, **35 commands exit0**, **222 raw Allure** + **26 Vitest separately**.
111 Booking/delivery +24 Assistant +20 Worker +2 persistence +5 recovery phases
+26 Vitest +60 desktop/mobile Playwright. True child RED 2 failed / restored GREEN
3 passed remain attachments of the outer sensitivity gate, not extra headline checks.
PostgreSQL/RabbitMQ/MCP/Mailpit real; LLM provider explicitly scripted, no inference calls.
[Metadata](../../artifacts/20261116T012006Z-46c1a7/run.json),
[actual full log](../../artifacts/WB-10-regression.log).

## Actual remote gates and release

| Gate | Result |
|---|---|
| Feature [PR #39](https://github.com/smalvik/biocad-workspace/pull/39), head 54547a9 | [CI 43786259227 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43786259227); check/package succeed, delivery correctly skipped for a PR |
| Feature merge | develop **e8e29cfb433649ce0f01cfeb726b91d241f5fbaf**, **2026-11-16T01:35:32Z UTC** |
| Develop post-merge | [43787157854 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43787157854); full CI, nine images, real server regression and persistent staging smoke |
| Promotion [PR #40](https://github.com/smalvik/biocad-workspace/pull/40) | [43787178364 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43787178364); same-SHA push/PR manifests identical across all nine fields/digests |
| Main merge | **4a40e18099d98b275f768489a10f8a010003cd33**, **2026-11-16T01:51:10Z UTC** |
| Main | [43788663155 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43788663155); full CI/server/staging/production, exact digests, version/latest aliases, release and inline Allure |

All reviews explicitly identify **agent self-review**, not independent human approval.
[Actual build-once comparison](../../artifacts/WB-10-build-once-proof.json).
Clean real server develop run **20261116T014152Z-fa66da**, sourcee8e29cf:
**248 checks /35 commands exit0 /223 raw Allure**, including staging smoke.
Clean main server **20261116T015805Z-747e4b**, source4a40e18:
**248 checks /35 commands exit0 /224 raw Allure** (222 regression + stage/prod2,
26 Vitest separate; raw counts are not Allure UI row-count claims).
[Develop run](../../artifacts/WB-10-develop-delivery/server/e8e29cfb433649ce0f01cfeb726b91d241f5fbaf/20261116T014152Z-fa66da/run.json),
[main run](../../artifacts/WB-10-main-delivery/server/4a40e18099d98b275f768489a10f8a010003cd33/20261116T015805Z-747e4b/run.json).
Runtime code/tests are unchanged by this documentation task; the real regression
still includes the genuine child RED/GREEN and 20-caller contention gate.

Published **[v1.4.2](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.2)**, **2026-11-16T02:07:37Z UTC**,
non-draft/non-prerelease, exact product source **4a40e18099d98b275f768489a10f8a010003cd33**.
Both persistent environments use the same complete **schema2 / nine-image manifest**,
four runtime version/latest aliases published only after production smoke.
[Actual candidate](../../artifacts/WB-10-main-candidate/candidate.json).

## Independent public acceptance and preservation

- Public application desktop/mobile: **4 PASS**, no booking writes or new inference.
  [Actual metadata](../../artifacts/WB-10-production-browser/run.json).
- Public Allure latest + original v1.3.0 free-model report desktop/mobile: **4 PASS**,
  **downloads=0**. HTTP inline/content-type/source/checksum check also PASS.
  [Actual metadata](../../artifacts/WB-10-allure-production-browser/run.json).
- [Open application](https://biocad.smalvik.dev),
  [versioned Allure](https://biocad.smalvik.dev/allure/v1.4.2/),
  [original live proof](https://biocad.smalvik.dev/allure/v1.3.0/live/).

**14 own containers healthy/running**; **23 unrelated container IDs/images/start
times/restart counts unchanged**. Sampled pre-existing HTTP responses are recorded,
not claimed healthy merely because they match.
[Container comparison](../../artifacts/WB-10-preservation-proof.json),
[filtered own server state](../../artifacts/WB-10-final-server-state.json).
Each environment retains **7 original bookings /12 original accounts**, changed/missing0.
Individual identifiers/fingerprints remain only in the root-only server snapshot;
only aggregate counts leave the server. [Final counts](../../artifacts/WB-10-data-final.json).
Worker healthy both, **7 sent /7 actually captured Mailpit** messages each,
outbox/jobs/ready/unack queues empty. [Actual audit](../../artifacts/WB-10-final-notifications.json).

Previous production **v1.4.1 /5364c9e** retained. Validated pre-deploy backups:
staging **20261116T020543-a6bfab.dump /29567 bytes**,
production **20261116T020613-d9ec16.dump /30470 bytes**.
Backups and raw data snapshots are not public assets. No proxy/DNS/daemon change,
foreign-project mutation, DB migration, external SMTP or new LLM call.

## Scope limits and next task

Active personal hours were requested but not supplied; documentation explicitly
states **unmeasured**, with no invented agent model/cost or human approval.
Actual C1/C2 and two ADRs reflect implemented code. P1 comfort/failover/quiz/feedback,
separate WB-16 and in-product WB-17 release-history remain outside this task.
Release notes/process already exist; next unfinished **P0 docs: WB-18 interview
playbook verification** before optional P1 work. This release does not complete the PRD.
