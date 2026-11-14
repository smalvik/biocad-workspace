# WB-04 actual remote verification

Feature [PR #16](https://github.com/smalvik/biocad-workspace/pull/16) merged
into develop at `a00f590a45cb88db5e05bd1147a5bbb3e5f55bf4`.
Main promotion [PR #17](https://github.com/smalvik/biocad-workspace/pull/17)
merged at `16826d4edc08acc21b0f4122e7a4976bbdecd79d`.
Reviews explicitly identify agent self-review; independent human approval is not claimed.

- [Final feature PR checks/publication](https://github.com/smalvik/biocad-workspace/actions/runs/43634407373): PASS.
- [Develop post-merge regression, publication and server staging](https://github.com/smalvik/biocad-workspace/actions/runs/43635049967): PASS.
- [Main PR checks/publication](https://github.com/smalvik/biocad-workspace/actions/runs/43635067010): PASS.
- Develop server run `20261114T200438Z-cf26d0`: full isolated prebuilt-image regression,
  real PostgreSQL/RabbitMQ/Mailpit, 131 passed (114 Allure + 17 Vitest), clean source.
  Persistent staging smoke also passed: **115 passed Allure results** in the downloaded artifact.
- [Develop artifact](../../artifacts/WB-04-develop-server/), including commands,
  actual run metadata, screenshots and standalone Allure.
- [Main workflow](https://github.com/smalvik/biocad-workspace/actions/runs/43636402995):
  all jobs PASS; published [v1.1.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.1.0)
  at 2026-11-14 20:24:26 UTC, source `16826d4edc08acc21b0f4122e7a4976bbdecd79d`.
- Main server run **20261114T201924Z-e69216**: **131 passed** = 74 Booking/delivery,
  2 Assistant, 2 persistence, 17 Vitest, 36 Playwright. All 20 commands exit 0,
  clean source and prebuilt digests, without builds on the host.
- Staging and production HTTPS/session/source smoke PASS. Server Allure:
  **116 passed** = 114 regression + staging/production smoke; Vitest 17 separately.
  [Standalone Allure](https://github.com/smalvik/biocad-workspace/releases/download/v1.1.0/index.html)
  (download/open locally), [exact digest manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.1.0/candidate.json).
- [Downloaded main evidence](../../artifacts/WB-04-main-delivery/), including actual
  run metadata, commands, screenshots, stage/production results and release metadata.
- Both persistent environments match the complete main candidate manifest; all
  12 BIOCAD containers are running/healthy. Production backup
  `20261114T202321-dc070c.dump` exists (23,465 bytes); previous production manifest
  is v1.0.0. [State proof](../../artifacts/WB-04-server-state.json) contains only
  manifests, backup file metadata and container status, not secrets or backup contents.
- Independent public HTTPS desktop/mobile smoke: **4 passed, exit 0** using the exact
  main E2E image; login/map and case-insensitive employee lookup/permanent owner/filter.
  No booking writes. [Metadata](../../artifacts/WB-04-production-browser/run.json),
  [log](../../artifacts/WB-04-production-browser.log), screenshots/Allure alongside.
- [Preservation proof](../../artifacts/WB-04-server-preservation-proof.json): all
  **23 preexisting containers** retain their IDs, image references and start/restart
  timestamps. Sample HTTP statuses match the original baseline, which already
  included URLError/401/404; this is not a claim that those URLs were healthy.

Actual commands: `gh pr review --comment`, `gh pr merge --merge --match-head-commit`,
`gh run view/download`, `gh release view`; the workflow invokes
`scripts/check.py --manifest ... --environment staging --run-type regression`,
`remote_delivery.py stage/production/report`, `promote_images.py` and `publish_release.py`.
Independent check: `python artifacts/run_logged.py artifacts/WB-04-production-browser.log python artifacts/wb04_production_browser.py`.
Read-only server snapshots: `server_ops.py run-script` with reviewed inventory scripts,
then `python artifacts/wb04_preservation.py`. First local SSH snapshot was blocked by
empty file DACLs after an earlier ACL edit; restored access only to the current owner,
SYSTEM and Administrators on the five newly generated BIOCAD key/auth files, then
both real SSH snapshots succeeded. No SSH service, server authorization or existing key changed.

No schema changes or modifications to the existing host ingress/deployment tooling.
Fictional employee lookup and portraits describe bookings/assignments for the selected
period, never physical presence. Booking form, real MCP/LLM and business notifications
are subsequent tasks.
