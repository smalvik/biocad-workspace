# WB-07 local evidence — 2026-11-15

Issue [#30](https://github.com/smalvik/biocad-workspace/issues/30), branch
`feat/wb-07-email-notifications` from develop fd81f82. Carried Allure post-release
notes as d7e3b7651181fb2462c235cba26bfa9d513b6bc0.

`python scripts/check.py --run-type regression` through `artifacts/run_logged.py`:

- Initial **20261115T201831Z-5d530f** passed237 checks,211 raw Allure results,
  all35 commands exit0. Base d7e3b76 /tree dirty. This earlier snapshot still had
  unnecessary address-column migration code; it is not the final implementation.
- No-migration source **20261115T202930Z-01667a** passed **237 checks**:
  100 Booking/delivery (including real PostgreSQL locking/outbox tests),24 Assistant,
  20 Notification Worker,2 persistence,5 explicit real notification outage/recovery phases,
  26 Vitest and60 desktop/mobile Playwright. **211 raw Allure results**, Vitest separate.
  All35 commands exit0, same base/tree dirty. CI provider explicitly scripted;
  MCP/RabbitMQ/PostgreSQL real, no new LLM inference.
  [run.json](../../artifacts/20261115T202930Z-01667a/run.json),
  [commands](../../artifacts/20261115T202930Z-01667a/commands.log),
  [launcher log](../../artifacts/WB-07-regression-final.log).
- Final reviewed-source **20261115T205358Z-5ee75a** passed the same **237 checks**,
  all **35 commands exit 0**, **211 raw Allure results**, base d7e3b76/tree dirty.
  Both templates and real captured-message assertions now also include the PRD-required
  fictional employee full name and support contact; mobile email has a viewport declaration.
  [run.json](../../artifacts/20261115T205358Z-5ee75a/run.json),
  [commands](../../artifacts/20261115T205358Z-5ee75a/commands.log),
  [launcher log](../../artifacts/WB-07-regression-reviewed.log).

Real disposable-project phases stopped only that project's broker/worker/SMTP:
confirmed booking+pending outbox during RabbitMQ outage, recovery and one actual
Mailpit HTML/text confirmation; idempotent cancellation and one cancellation email;
worker restart plus repeated events without another message; SMTP outage committed
booking and pending delivery, worker restart, SMTP recovery and capture. Existing
desktop/mobile desk/room flows assert the actual Mailpit recipient, booking ID and
HTML/text parts; real email HTML is attached to their Allure results.

Worker's separate initial unit invocation passed20 tests: durable/concurrent admission,
restart deduplication, conflicting identity rejection, per-booking SMTP retry order,
Moscow HTML/text body, escaping, header injection/non-demo refusal and ACK-after-inbox.

## Real upgrade/rollback compatibility

`python artifacts/wb07_compat_driver.py artifacts/20261115T202930Z-01667a/run.json`:
all4 phases passed, launcher exit0. Own generated `biocad-wb07-compat-*` project,
private network, fake credentials, no published ports; unrelated projects untouched.
Starts real immutable v1.3.1 images at8d8cf08, creates one fictional confirmed booking,
then upgrades to the dirty local source, rolls back to v1.3.1, and resumes the new worker.
All original booking/account fingerprints remain unchanged; comparison stays inside
the disposable PostgreSQL instance and only counts are exported. Alembic stays at
**0003_assistant_limits** in every phase. The legacy outbox event reaches actual
Mailpit; two replayed copies after resume produce no second email, invalid DLQ empty.
Worker journal/volume persists while legacy processing is stopped.

[Proof metadata](../../artifacts/WB-07-upgrade-rollback/run.json),
[successful log](../../artifacts/WB-07-upgrade-rollback-final.log),
[actual captured HTML](../../artifacts/WB-07-upgrade-rollback/legacy-booking-notification.html),
[desktop](../../artifacts/WB-07-upgrade-rollback/email-desktop.png),
[mobile](../../artifacts/WB-07-upgrade-rollback/email-mobile.png).
Screenshots render the actual SMTP-captured message, not a conceptual mock.
The first helper attempt failed before application checks because its Python import path
was missing; [failure retained](../../artifacts/WB-07-upgrade-rollback.log), corrected
and rerun successfully. This local checkpoint preceded committed CI/server validation;
the completed [remote delivery evidence](WB-07-remote.md) is recorded separately.

Repeated with final reviewed-source images from **20261115T205358Z-5ee75a** using
`python artifacts/wb07_compat_driver.py artifacts/20261115T205358Z-5ee75a/run.json reviewed`:
all four phases passed again, including actual legacy-event full name/support fields,
unchanged original records/revision and one captured message after duplicate replay.
[Reviewed proof](../../artifacts/WB-07-upgrade-rollback-reviewed/run.json),
[reviewed log](../../artifacts/WB-07-upgrade-rollback-reviewed.log),
[final actual HTML](../../artifacts/WB-07-upgrade-rollback-reviewed/legacy-booking-notification.html).

Schema 2 complete nine-image manifests and old schema 1 seven-image rollback contracts
are unit-tested. Worker owns a private SQLite WAL inbox, never Booking PostgreSQL.
SMTP acceptance/local sent-state commit remains an explicit ambiguous duplicate window;
durable completed-event replay deduplication is verified, exactly-once SMTP is not claimed.
