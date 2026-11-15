# WB-05 remote delivery evidence

Feature [PR #19](https://github.com/smalvik/biocad-workspace/pull/19), exact head
`6554fc447cd8bf80c15ea65d26a2cf678bb882e0`, passed
[checks and immutable image publication](https://github.com/smalvik/biocad-workspace/actions/runs/43641919071).
Merged develop at **b98a9a327fcf142b1f616f2b6287fc199f34fbb0**.
Review explicitly identifies agent self-review, not independent human approval.

- [Develop post-merge workflow](https://github.com/smalvik/biocad-workspace/actions/runs/43642523912):
  all jobs PASS, including complete server regression and persistent staging smoke.
  Actual server run `20261114T212803Z-2b10a1`, clean source b98a9a3;
  **133 passed Allure results** (132 regression + staging smoke), Vitest 25 separately.
  [Downloaded evidence](../../artifacts/WB-05-develop-server-retry/).
  First artifact download ended with a transport `unexpected EOF`; a fresh-directory
  retry completed and the actual result files were parsed. No CI failure is implied.
- [Main promotion PR #20](https://github.com/smalvik/biocad-workspace/pull/20) passed
  [PR checks/publication](https://github.com/smalvik/biocad-workspace/actions/runs/43642562977)
  and merged main at **bddba674f9966164016d4f6102702074dab41b5e** after green develop staging.
- [Main workflow](https://github.com/smalvik/biocad-workspace/actions/runs/43690831879)
  **all jobs PASS**. Published [v1.2.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.2.0)
  at **2026-11-15 07:49:07 UTC / 10:49:07 MSK**, source bddba67.
  Seven immutable source/digest candidates; version/latest aliases for the three
  runtime services verified without rebuilding after staging.
- Fresh read-only server inventory before main delivery: **23** unrelated containers;
  persistent staging is 1.2.0, production 1.1.0 at source `16826d4`.
  [Baseline](../../artifacts/WB-05-server-baseline.json),
  [own-environment metadata](../../artifacts/WB-05-server-before-state.json).

## Published version / actual server checks

Production: **https://biocad.smalvik.dev**, fictional `e01`–`e12` / `demo-workspace`.

- Main server run **20261115T074307Z-84214e**, clean source
  `bddba674f9966164016d4f6102702074dab41b5e`: **157 passed** = 76 Booking/delivery,
  2 Assistant, 2 persistence, 25 Vitest, 52 desktop/mobile Playwright. All 20 commands
  exited 0; real PostgreSQL/RabbitMQ/Mailpit and prebuilt digests, no builds on host.
- Stage and production HTTPS/session/source smoke PASS. **134 passed Allure results**
  = 132 regression + stage/prod smoke; 25 Vitest separately.
  [Standalone Allure HTML](https://github.com/smalvik/biocad-workspace/releases/download/v1.2.0/index.html),
  [exact published image manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.2.0/candidate.json),
  [downloaded main evidence](../../artifacts/WB-05-main-delivery/).
- Both persistent environments match the complete main candidate; all **12 BIOCAD
  containers** running/healthy. Production backup **20261115T074756-aeaa01.dump**
  exists (23,877 bytes); previous production manifest **v1.1.0** retained.
  [State proof](../../artifacts/WB-05-server-state.json) contains only manifests,
  backup file metadata and container status, no secrets or dump contents.
- [Preservation proof](../../artifacts/WB-05-server-preservation-proof.json): all
  **23 unrelated containers** retain IDs, images and start/restart timestamps against
  both the fresh pre-main baseline and original WB-09 inventory. Sample HTTP statuses
  remain unchanged (the baseline already contained URLError/401/404; healthy unrelated
  URLs are not claimed).

## Independent public browser checks

- Exact published E2E image, actual HTTPS, desktop/mobile login/map and employee lookup:
  **4 passed, exit 0**. [Final metadata](../../artifacts/WB-05-production-browser-final/run.json),
  [log](../../artifacts/WB-05-production-browser-final.log), screenshots/Allure alongside.
- Independent new confirmation preview and own confirmed/cancelled list on desktop/mobile:
  **2 passed, exit 0, zero attempted booking writes**. Exact resource/office/floor/Moscow
  interval, opening/back, list states and focus restoration checked. Creation POST was
  explicitly blocked by the read-only probe; no production create/cancel action used.
  [Final metadata](../../artifacts/WB-05-production-preview-final/run.json),
  [log](../../artifacts/WB-05-production-preview-final.log),
  [desktop confirmation](../../artifacts/WB-05-production-preview-final/confirmation-desktop.png).
- Initial parallel external executions are retained: baseline browser **3 failed / 1 passed**,
  preview exited 1 at `page.goto` timeout. Host curl/Node and an initial Python TLS handshake
  also timed out. DNS was correct; TCP connected. Without any server/runtime/network
  configuration change, subsequent [TLS probe](../../artifacts/WB-05-local-tls-probe.json)
  received TLS 1.3 / HTTP 200 with exact bddba67 / 1.2.0, and the existing other domain
  retained 401. [Server connectivity](../../artifacts/WB-05-server-connectivity.json) also
  returned 200/source match. Sequential independent repeats above passed completely.
  The first attempts are not counted green; a specific root cause for the transient
  external TLS timeouts is not asserted.

Actual commands: `gh pr review --comment`, `gh pr merge --merge --match-head-commit`,
`gh run view/download`, `gh release view/edit`; workflow `check.py --manifest ...`,
`remote_delivery.py stage/production/report`, `promote_images.py`, `publish_release.py`.
Independent commands through `artifacts/run_logged.py`: `wb05_public_smoke.py`,
`wb05_preview_driver.py production`; read-only server inventory via `server_ops.py
run-script`, then `wb05_preservation.py`. No server changes were made during connectivity diagnosis.

Local verification: [157 passed / actual failure history](WB-05-local.md).
No schema changes, server ingress/tooling changes or production mutation tests.
