# WB-02 — real PostgreSQL regression, 2026-11-14

Branch: `feat/wb-02-booking-core`, created from integrated develop
`e5bb0b5ce4980074f40e682a8beac072f73ba06f` (WB-01 PR #2).
Run ID: `20261114T133549Z-a1866f` (UTC; 16:35:49 Europe/Moscow).
The tested working tree was dirty; this is local evidence, not a WB-02 remote CI pass.

```powershell
python scripts/check.py --run-type regression
```

The runner created a separate project with separate volumes and no host ports.
All 20 recorded Docker commands exited 0, including build, health gates,
real dependency tests, re-seeding, service/database restarts and cleanup.

| Check | Actual result |
|---|---|
| Booking pytest | 41 passed in 8.10s |
| Assistant pytest | 2 passed in 0.10s |
| Persistence before restart | 1 passed in 0.31s |
| Persistence after PostgreSQL + Booking restart | 1 passed in 0.46s |
| Vitest | 2 passed |
| Playwright Chromium desktop/mobile | 5 passed in 9.1s |
| Ruff check/format, web build/typecheck, E2E typecheck | exit 0 |
| Total | 52 passed; 50 pytest/Playwright Allure results, all passed |

The 20-request exclusion test uses two authenticated demo users and a barrier;
one request returns 201 and nineteen return 409. The same-key race returns one
201 and nineteen 200 with the same booking ID; SQL checks one booking/outbox event.
Direct SQL bypassing the API still gets SQLSTATE 23P01 for overlap and 23514 for
reversed bounds. Adjacent timestamps succeed. Direct test writes are rolled back.

Atomicity is tested by a unique temporary outbox CHECK, only in the isolated
database: an expected 500 leaves no booking, the CHECK is removed in finally,
and a retry succeeds. No overlap constraint is disabled by these tests;
the dedicated red/green mutation demonstration remains WB-08.

Other checks: canonical D-03 windows/D-07 assignment, UTC equivalence,
changed idempotency payload, replay after cancellation, per-user key scope,
cancel-own-only, scoped list, signed/HttpOnly session, CSRF and revoked logout.

Persistence is not simulated: the runner stops Booking, restarts PostgreSQL,
waits for DB health, starts Booking with migration/idempotent seed, logs in again,
verifies the prior row and replays the same key (200, same payload/ID).
The persistence marker contains fictional booking data, no credentials/cookies/CSRF.

- [Machine-readable run.json](../../artifacts/20261114T133549Z-a1866f/run.json)
- [Full commands/output](../../artifacts/20261114T133549Z-a1866f/commands.log)
- [Standalone Allure HTML](../../artifacts/20261114T133549Z-a1866f/allure-report/index.html)
- [Playwright HTML](../../artifacts/20261114T133549Z-a1866f/playwright-report/index.html)

Allure HTML was generated successfully with the already installed Docker-volume
CLI `allure-commandline@2.32.0` and Java 17:

```powershell
docker run --rm -v "C:/projects/biocad-workspace/artifacts:/reports" -v biocad-allure-cli:/tools:ro eclipse-temurin:17-jre-jammy /tools/node_modules/allure-commandline/dist/bin/allure generate /reports/20261114T133549Z-a1866f/allure-results --single-file --clean -o /reports/20261114T133549Z-a1866f/allure-report
```

Allure metadata: `run_type=regression`, `environment=local`,
`git_sha=e5bb0b5...`, `working_tree=dirty`, `release_version=unreleased`.
Artifacts are ignored by Git; these links refer to this workstation.

Earlier failed runs are retained: `20261114T132956Z-ea26db` (fixture/test loop
scope mismatch, inherited from bootstrap) and `20261114T133303Z-f6168e`
(one HTTPX test rejected its own whitespace-only header before reaching the API).
Both harness defects were fixed before the passing run. They are not concurrency
mutation evidence and are not claimed as product defects.

WB-01 remote evidence: [PR #2](https://github.com/smalvik/biocad-workspace/pull/2),
[head CI passed](https://github.com/smalvik/biocad-workspace/actions/runs/43598925846),
[full post-merge regression passed](https://github.com/smalvik/biocad-workspace/actions/runs/43599195552).
WB-02 is tracked in [issue #3](https://github.com/smalvik/biocad-workspace/issues/3);
its branch/PR/CI/release has not been published by this run.

After the isolated regression, the local developer Booking container was rebuilt
and started with `.env.example` (existing PostgreSQL volume preserved). Live smoke
through localhost:8080 verified readiness, new OpenAPI paths with Idempotency-Key
and X-CSRF-Token inputs, login e01, 2 floors / 27 resources, D-03 free 12–14 Moscow,
D-07 DEDICATED, and server-side logout. Cookies/CSRF were kept in memory and not
printed. This smoke created no user booking. Ruff/format, actionlint, handoff
verification and `git diff --check` also passed after the documentation updates.
