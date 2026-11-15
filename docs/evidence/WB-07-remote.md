# WB-07 delivery evidence — 15 November UTC / 16 November Moscow 2026

Issue [#30](https://github.com/smalvik/biocad-workspace/issues/30).
Branch `feat/wb-07-email-notifications`, implementation
**4e39cc584631deca9236dcd89918fa886497acd9**. Agent self-review is recorded in both
PRs; no independent human approval is claimed.

| Gate | Observed result |
|---|---|
| Feature [PR #31](https://github.com/smalvik/biocad-workspace/pull/31) | [43761379185 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43761379185); merged develop **82d14a4c6c525faeaa8c85c8f6b3440b8837a786**, 21:09:33 UTC |
| Post-merge develop | [43762105830 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43762105830); complete CI, isolated server regression and persistent staging smoke |
| Promotion [PR #32](https://github.com/smalvik/biocad-workspace/pull/32) | [43762135867 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43762135867); merged main **5decd646785e8b9932dab7aa838ae2a3f1f74f7b**, 21:27:01 UTC |
| Main delivery | [43763748048 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43763748048); complete CI/server regression, staging/production HTTPS smoke, immutable aliases, release and public Allure publication |

Feature CI run **20261115T210224Z-e529c5**: source 4e39cc5, clean tree,
**237 checks**, all **35 commands exit 0**, **211 raw Allure results**.
100 Booking/delivery + 24 Assistant + 20 Worker + 2 PostgreSQL persistence +
5 explicit outage/recovery phases + 26 Vitest + 60 desktop/mobile Playwright.
CI explicitly uses a scripted provider; MCP/RabbitMQ/PostgreSQL/Mailpit are real.
No new real LLM inference or external SMTP delivery in WB-07.

Develop server run **20261115T211706Z-5cd68f**: exact source 82d14a4,
clean tree, same **237 checks**, all **35 commands exit 0**,
**212 raw Allure results** including staging smoke (Vitest separate).
Real recovery phases stop only their disposable broker/worker/SMTP; committed bookings
survive outages, restart resumes delivery, replay creates no second completed-event email.
Existing desk/room desktop/mobile E2E validates actual captured recipient/full name,
Moscow HTML/text body and support contact, with real HTML attachments.

Main CI run **20261115T212708Z-d067cc** also passed all **237 checks**,
all **35 commands exit 0**, **211 raw Allure results**, source 5decd64 / clean tree.
Main server regression **20261115T213418Z-8820ac** passed the same **237 checks**,
all **35 commands exit 0**, source 5decd64 / clean tree. **213 raw Allure results**
include 211 regression and two staging/production smoke results; Vitest is separate.
Exact nine-image schema 2 digests were promoted from validated staging to production.

Actual nine-image schema 2 manifests from push 43762105830 and PR 43762135867
are **identical in every field/digest** at the same source SHA.
[Build-once proof](../../artifacts/WB-07-build-once-proof.json).
Anonymous server pulls succeeded. Four runtime images include independently deployed
Notification; it owns a private SQLite WAL volume with no Booking DB credentials.
Schema 1 seven-image rollback stays valid; no Booking migration is added.
[Real old-image upgrade/rollback/resume proof](WB-07-local.md).

Server tooling was updated only in the owned BIOCAD area before delivery; no global
Docker/proxy configuration or existing app restart. Restricted CI SSH key still rejects
remote shell commands. Before deployment, original booking/account row checksums were
saved **only on the server**, root-only; no identifiers/digests were downloaded.

After persistent staging: Worker healthy at source 82d14a4 / version 1.4.0;
seven legacy events sent, zero pending outbox/jobs, zero ready/unacknowledged messages
in notification and invalid queues. Production remained v1.3.1 at this gate.
Private Mailpit API independently confirmed **7 captured messages**, matching all seven
sent journal entries before the main-image update; no message bodies/identifiers exported.
Both environments retain exactly **7 original bookings / 12 original accounts**,
changed/missing original rows **0**. Staging backup `20261115T212434-75e2bb.dump`.
[Worker audit](../../artifacts/WB-07-staging-notifications.json),
[aggregate-only preservation](../../artifacts/WB-07-data-after-staging.json),
[actual server artifacts](../../artifacts/WB-07-develop-delivery).

## Published production result

[v1.4.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.0), published
**2026-11-15 21:43:49 UTC / 2026-11-16 00:43:49 Moscow**, non-draft/non-prerelease,
source **5decd646785e8b9932dab7aa838ae2a3f1f74f7b**. Both persistent environments
run that exact manifest. All **14 own containers running/healthy**; Notification's
private heartbeat reports that source. Both have **7 sent / 7 actual captured messages**,
zero pending outbox/jobs and zero delivery/invalid ready/unacknowledged messages.
Staging journal and Mailpit counts stayed unchanged across its develop → main image update.
[Worker capture/preservation proof](../../artifacts/WB-07-notification-preservation-proof.json).

All original **7 bookings / 12 accounts per environment** remain unchanged, changed/missing
count **0**; comparisons and individual checksums remain server-side only.
All **23 unrelated containers** retain their IDs/images/start times/restart counts.
Sample unrelated HTTP responses are unchanged (URLError/401/404 are baseline observations,
not a claim that all those sites are healthy).
[Data aggregate](../../artifacts/WB-07-data-final.json),
[unrelated preservation](../../artifacts/WB-07-preservation-proof.json),
[current/previous manifests and container health](../../artifacts/WB-07-final-server-state.json).
Previous production **v1.3.1** and backup `20261115T214229-42e60e.dump` (29,866 bytes)
are retained; main staging backup `20261115T214159-737a89.dump` (29,212 bytes).
No database restore, global proxy edit, daemon restart or foreign volume deletion.

Public **https://biocad.smalvik.dev**: four desktop/mobile login/map/employee-lookup
cases passed using the immutable main E2E image, no booking writes or inference.
Public HTTP inline/type/exact-manifest/checksum smoke passed; four desktop/mobile
interactive report cases (latest regression + original v1.3.0 live archive) passed,
**zero download events**, HTTP 200. Actual email HTML is attached to booking E2E in
[latest Allure](https://biocad.smalvik.dev/allure/) and
[immutable v1.4.0 report](https://biocad.smalvik.dev/allure/v1.4.0/).
[Application browser run](../../artifacts/WB-07-production-browser/run.json),
[public report browser run](../../artifacts/WB-07-allure-production-browser/run.json),
[actual main delivery artifacts](../../artifacts/WB-07-main-delivery).

SMTP accepted-DATA/local sent-state commit ambiguity remains documented in
[ADR-002](../adr/002-broker-and-outbox.md); exactly-once SMTP is not claimed. Mailpit
stays internal on the server, local UI localhost:8025. No new paid/free inference calls.
Next P0 is WB-08 race/red-green evidence; all PRD capabilities are not claimed complete.
