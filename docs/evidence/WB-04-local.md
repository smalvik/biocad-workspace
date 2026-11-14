# WB-04 local verification

Full command: `python artifacts/run_logged.py artifacts/WB-04-regression-final.log python scripts/check.py --run-type regression`.
Run **20261114T193248Z-b8b531**, base `0f20a58`, working tree **dirty**, result **PASS**.

- **131 passed**: 74 Booking/delivery pytest, 2 Assistant, 2 persistence, 17 Vitest, 36 Playwright.
- Allure **114 passed** (Vitest separately), [HTML](../../artifacts/20261114T193248Z-b8b531/allure-report/index.html).
- [Commands](../../artifacts/20261114T193248Z-b8b531/commands.log), [metadata](../../artifacts/20261114T193248Z-b8b531/run.json).
- PostgreSQL concurrency/idempotency/atomic outbox/restart tests remain passing; new directory/occupancy
  checks cover Unicode case, literal wildcard escaping, safe public fields, interval validity,
  four canonical D-03 windows, historical dedicated validity, two floors and cancellation.
- Desktop/mobile tests use actual API/DB; screenshots are browser-produced, not conceptual references.
- [Desktop timeline](../../artifacts/20261114T193248Z-b8b531/test-results/employees-avatar-changes-f-d2cea-plete-timeline-smoke-mobile-desktop/employee-timeline-desktop.png),
  [mobile cross-floor card](../../artifacts/20261114T193248Z-b8b531/test-results/employees-employee-lookup--f4c02-al-reservation-smoke-mobile-mobile/employee-location-mobile.png), visually inspected.
- Initial `20261114T192822Z-4a2f92`: 2 strict E2E selectors matched both selected time and booking time.
  Restricted to the booking timeline and repeated the complete suite successfully; failure artifacts retained.
- [Existing dev-volume upgrade](../../artifacts/WB-04-dev-upgrade/run.json): counts 7 before/after,
  account password rows identical, 12 fictional avatar URLs updated, live login/asset/logout PASS.

Allure labels include local environment/run type/source/dirty tree; authenticated traces remain disabled.
Runtime images and tests contain only fictional fixture data and original SVG portraits. No real personal data/LLM calls.
This is local evidence, not a claim of WB-04 remote merge/deployment. Production v1.0.0 evidence is separate.
