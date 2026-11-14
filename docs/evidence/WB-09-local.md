# WB-09 local evidence — 2026-11-14

- Base source `af00fa1e8e2e41f33d8d1150a73b27b55753562c`, working tree **dirty**.
- `python scripts/check.py --run-type regression`: run `20261114T153725Z-794475`, **PASS**.
- **55 Booking/delivery + 2 Assistant + 2 persistence + 10 Vitest + 22 Playwright = 91 passed**.
- Allure 81 passed; Vitest 10 separately. Ruff, frontend build, E2E typecheck passed.
- [Commands](../../artifacts/20261114T153725Z-794475/commands.log), [metadata](../../artifacts/20261114T153725Z-794475/run.json).
- An earlier full run `20261114T152546Z-61c92d` passed 90 cases before OCI-label guard was added.
- Focused final delivery unit suite: `docker run ... pytest -q -p no:cacheprovider /checks`, **13 passed**, including label mismatch refusal, manifest injection/mutable-tag rejection, exact staging gate, failed-smoke image rollback and first HTTPS certificate delay.
- `python artifacts/wb09_deploy_smoke.py`: **PASS**, project `biocad-deploy-proof-8907c8bf`;
  [result](../../artifacts/WB-09-deploy-smoke/result.json), [log](../../artifacts/WB-09-deploy-smoke.log).
- Real runtime images start without builds. Only Web publishes a loopback port.
  Source/version, PostgreSQL readiness, Secure/HttpOnly/SameSite cookie flags checked.
  Real PostgreSQL custom backup + `pg_restore --list`; wrong web image deliberately
  substituted, HTTP smoke rejected it, previous image restored and smoke passed.
  Two results came from actual dispatcher smoke code (HTTP/local execution).
- All temporary proof containers/volumes removed; persistent developer stack container IDs unchanged.
- Full-run failure/fix history is retained: focused collection initially used reserved pytest
  parameter `request`; corrected. First image-rollback proof could not start its intentionally
  wrong image because it wasn't cached; pulled the official image and repeated successfully.
- `actionlint`, delivery Ruff checks/format: PASS at last checked snapshot.

Remote preflight completed later: owner supplied password in ignored `.env`, Docker Hub
renewed token authenticated, admin key created/tested, limited CI user/dispatcher installed.
Read-only server inventory saved in ignored `artifacts/WB-09-server-inventory.txt`.
No unrelated app restart or proxy replacement. Actual remote app deployment/release is pending.
Credentials/private keys/DB backups are excluded from committed evidence and report bundles.
