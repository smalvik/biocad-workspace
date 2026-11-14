# WB-05 local verification — 2026-11-15 MSK

Command: `python artifacts/run_logged.py artifacts/WB-05-regression-complete.log python scripts/check.py --run-type regression`.
Run **20261114T210618Z-566c12**, base **7f5e82a5aecd26b9b1085e6269526f19548ad113**,
working tree **dirty**, result **PASS**, all commands exit 0.

- **157 passed** = 76 Booking/delivery pytest + 2 Assistant + 2 persistence +
  25 Vitest + 52 desktop/mobile Playwright.
- **132 passed Allure results**, Vitest separately. [Results](../../artifacts/20261114T210618Z-566c12/allure-results/),
  [standalone HTML](../../artifacts/20261114T210618Z-566c12/allure-report/index.html),
  [commands](../../artifacts/20261114T210618Z-566c12/commands.log),
  [metadata](../../artifacts/20261114T210618Z-566c12/run.json).
- Real PostgreSQL: concurrent exclusion/idempotency/adjacent intervals/outbox/ownership
  tests still pass; new own-list safe location, both floors and cancellation state tests.
  Persistence checks compare every original booking field and idempotent replay after
  service/PostgreSQL restart; added list location does not change the original fields.
- Browser: FreeDesk D-15 and meeting room M-03, no write at selection/Continue/back,
  exact confirmation/CSRF/key, own list, keep/cancel, immediate map refresh, lost committed
  response plus reload/replay, real competing employee 409, pending click guard,
  lost cancellation retry, list empty/error/retry, keyboard focus/Escape, dedicated/past
  action guard and visible 422. Mutation cases refuse public production hosts.
- Actual [mobile cancellation / M-03](../../artifacts/20261114T210618Z-566c12/test-results/bookings-explicit-M-03-con-6440a-e-the-real-map-smoke-mobile-mobile/booking-cancelled-M-03-mobile.png)
  and local confirmation preview screenshots were visually inspected. Map controls sit
  below the canvas so the mobile room remains clickable without `force`.
- [Existing dev-volume upgrade](../../artifacts/WB-05-dev-upgrade/run.json): all **7**
  complete booking records and account password rows identical before/after; live
  login/own-list/location/logout PASS. Repeated after the final map CSS change.
- [Independent local preview](../../artifacts/WB-05-local-preview/run.json): desktop/mobile
  confirmation/own-list checks, **2 passed, exit 0, 0 attempted booking writes**.
  [Actual confirmation](../../artifacts/WB-05-local-preview/confirmation-desktop.png).

Earlier runs retained, never counted as passing:

| Run | Actual outcome / correction |
|---|---|
| 20261114T204616Z-d12679 | 75 Booking checks passed, one new test selected D-31 (DEDICATED); corrected to FreeDesk D-32 |
| 20261114T204809Z-70319b | Booking 76 passed; persistence DTO equality failed after new `resource` field. Kept original JSON date serialization and strictly compare all original booking fields |
| 20261114T205108Z-6de608 | Intentionally aborted obsolete image using conceptual D-14 (actual DEDICATED). Booking was stopped, then its own E2E container stopped; resulting service errors are cancellation artifacts, not claimed application regressions. Fixed test resource to D-15 |
| 20261114T205326Z-4e304d | New browser flows exposed HTTP-origin `crypto.randomUUID` absence and native-dialog unmount focus restoration. Runtime probe confirmed false secure context, absent randomUUID, available getRandomValues; implemented 128-bit random operation keys and explicit focus restoration |
| 20261114T210039Z-7898f6 | 51/52 E2E passed; mobile zoom control intercepted M-03 pointer click. Moved controls under SVG, kept normal click assertion |

API choice checked against the [Web Crypto interface](https://w3c.github.io/webcrypto/#crypto-interface).
First local HTML renderer attempt used a GH-only tool image without `npx`; test results
were unaffected. A separate ignored Node/Java/Allure tooling image supplies report rendering.
Final command `docker run --rm -v ...:/data biocad-allure:local generate /data/allure-results --single-file --clean -o /data/allure-report` exited 0.
No secrets, session cookies or authenticated network traces were written into these artifacts.
Production is still v1.1.0 at this local verification stage; remote evidence is recorded separately.
