# WB-03 — local interactive map regression, 2026-11-14

Branch `feat/wb-03-interactive-map`, created from develop
`34d4f7cf140e15eca25246211f8906d0a5384292` after the requested WB-02/main merges.
Run `20261114T143322Z-c7f947` (UTC; 17:33:22 Europe/Moscow), dirty working tree.
Implementation committed locally as `a02a488634b226c1ba69c86aa22b15b20d2df688`.
Only documentation changed after the passing regression/live smoke.

```powershell
python scripts/check.py --run-type regression
```

| Actual check | Result |
|---|---|
| Booking pytest, including new real geometry/API checks | 43 passed in 8.58s |
| Assistant pytest | 2 passed in 0.10s |
| Persistence prepare / PostgreSQL+Booking restart / verify | 1 + 1 passed |
| Vitest UI/domain/stale response tests | 10 passed |
| Playwright Chromium desktop/mobile | 22 passed in 20.8s |
| Total | 79 passed; 69 Allure results passed (10 Vitest separately) |
| Ruff check/format, web production build/typecheck, E2E typecheck | exit 0 |
| Compose startup / own-project cleanup | exit 0, run.json passed |

The map uses authenticated real Booking HTTP data and API coordinates. Tests
verify 24 desks/3 rooms on floor 2 and 12 desks/2 rooms on floor 3, valid geometry,
canonical D-03 time windows and D-07 dedicated state. The existing real PostgreSQL
20-way exclusion/idempotency/outbox/persistence suite also passed.

Browser tests cover login, keyboard selection, responsive details, both floors,
time/date changes, filters/empty state, invalid input, API failure/retry, delayed
responses, session expiry, logout, assistant outage, pointer pan/zoom/fit/Home.
API 503/401/outage and delayed responses are deliberately intercepted test cases,
not reported as actual production outages. The stale-response unit resolves an
old transport promise after abort and verifies it cannot replace the current data.

The browser run writes real screenshots, which were visually inspected:

- [Desktop selected resource](../../artifacts/20261114T143322Z-c7f947/test-results/smoke-login-keyboard-selection-and-real-map-smoke-mobile-desktop/office-map-desktop.png)
- [Mobile bottom sheet](../../artifacts/20261114T143322Z-c7f947/test-results/smoke-login-keyboard-selection-and-real-map-smoke-mobile-mobile/office-map-mobile.png)
- [Playwright HTML](../../artifacts/20261114T143322Z-c7f947/playwright-report/index.html)
- [Standalone Allure HTML](../../artifacts/20261114T143322Z-c7f947/allure-report/index.html)
- [Commands and output](../../artifacts/20261114T143322Z-c7f947/commands.log)
- [run.json](../../artifacts/20261114T143322Z-c7f947/run.json)

Allure HTML generated successfully using Docker-volume CLI
`allure-commandline@2.32.0` / Java 17, with
`allure generate /reports/20261114T143322Z-c7f947/allure-results --single-file --clean -o /reports/20261114T143322Z-c7f947/allure-report`.
Labels: run_type=regression, environment=local, git_sha=34d4f7c..., working_tree=dirty,
release_version=unreleased. Authenticated traces are disabled so network artifacts
do not retain session cookies/CSRF. Screenshots contain fictional demo data.

No booking is created by the new frontend. Confirmation form is WB-05; employee
search and avatars are WB-04. Approximate tokens and fictional plans are labeled.
No WB-03 remote push/PR/CI/merge, release or public deployment is claimed here.

Local developer stack was upgraded with
`docker compose --env-file .env.example -f infra/compose.yaml up -d --build --wait booking web`.
It preserved the existing PostgreSQL volume and migrated its plan metadata.
HTTP smoke verified the page, login/logout and both real API plans (1100/950 width).
An additional Playwright run against `BASE_URL=http://host.docker.internal:8080`
with `--grep "login, keyboard selection"` passed 2 tests (desktop/mobile, 8.7s).
[Live-stack browser report](../../artifacts/WB-03-live/playwright-report/index.html).
This is a separate smoke, not added to the 79-test regression/69-result report.
Actionlint, handoff verification, branch policy and git diff whitespace checks passed.

Completed remote prerequisites: [WB-02 PR #4](https://github.com/smalvik/biocad-workspace/pull/4),
[harness fix #8](https://github.com/smalvik/biocad-workspace/pull/8),
[main promotion #6](https://github.com/smalvik/biocad-workspace/pull/6),
[develop regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604565825),
[main regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604855360).
