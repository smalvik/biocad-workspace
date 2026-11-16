# Development progress (fill with actual evidence)

**2026-11-16 Moscow: WB-08 #33 and WB-11 #34 released v1.4.1.**
`test/wb-08-regression-evidence`, PR #36 → develop 05e08e6; separate deadlock fix
`fix/wb-11-booking-deadlock`, PR #35 → 75f661f; promotion #37 → main **5364c9e05505041e0035ea1b28adef99c6f61346**.
Reviewed here means explicit agent self-review, not independent human approval.
Feature PRs, both post-merge develop workflows, promotion PR and
[main 43779639648](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648) **all PASS**.
Clean main/server **248 checks**, **35 commands exit 0**, server **224 raw Allure**
(222 regression + stage/prod smoke; Vitest separate). Actual child RED **2 failed**,
restored GREEN **3 passed**, same oracle hash; runtime probe/pytest absent.
Public app **4**, report UI **4**, expanded race attachments **2** passed, downloads=0.
Both environments v1.4.1, 14 own containers healthy; original 7 bookings/12 accounts
per environment and 23 other containers preserved. No new LLM calls.
[Release](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.1), [Allure](https://biocad.smalvik.dev/allure/v1.4.1/),
[evidence](../evidence/WB-08-remote.md). Next unfinished P0: **WB-10 delivery docs**.
Post-release evidence stays on the WB-08 branch; start WB-10 from `develop` and carry
its documentation commit, leaving the immutable released application source unchanged.

**2026-11-16 Moscow: WB-07 released v1.4.0**, issue #30 / `feat/wb-07-email-notifications`.
Reviewed PR #31 merged develop 82d14a4, promotion #32 merged main 5decd64.
Local/committed full 237 passed; real broker/SMTP recovery and old-image rollback passed.
Develop/server/staging 43762105830 PASS; [main 43763748048 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43763748048),
server 237 checks / Allure 213 raw. [Release](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.0)
published 15 November 21:43:49 UTC; public app 4/report UI 4 passed, zero downloads.
Original data and 23 other containers preserved; 14 own containers healthy, seven actual
Mailpit messages in each environment. [Evidence](../evidence/WB-07-remote.md). At that checkpoint next P0 was WB-08;
its branch carried the final WB-07 post-release documentation commit.

**2026-11-15: browser Allure #27 released v1.3.1.** PR #28 → develop fd81f82,
promotion #29 → main 8d8cf08; [main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43745466108),
209 regression / 185 raw Allure results; public HTTP smoke + 4 desktop/mobile report cases
passed, zero downloads. [Open report](https://biocad.smalvik.dev/allure/),
[evidence](../evidence/WB-09-allure-web.md). 23 other containers and all original data preserved.
At that checkpoint the next unfinished P0 was WB-07.

**2026-11-15: WB-06 + WB-11 planning fix released v1.3.0.**
PRs #23/#25 merged develop 887bcc1; promotion #26 merged main 19a8388.
[Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43737645275):
189 regression / server Allure 165; actual free production API 3 + browser 2 passed,
cost=0, no booking writes. Both environments updated; 23 other containers and existing
7 bookings/12 accounts per environment preserved. [Evidence](../evidence/WB-06-remote.md).
Historical pause/resume: [handoff](PAUSE_HANDOFF.md). Next P0 at that checkpoint: WB-07.

**2026-11-14:** WB-01 continued from existing uncommitted React/FastAPI scaffolding.
WB-01 is merged; WB-02 Booking API is implemented and verified locally.
Historical checkpoint before WB-06: WB-03 map, WB-04 employee lookup/portraits and
WB-05 booking/cancellation were live; AI was still TODO at that checkpoint.
WB-09 was delivered before WB-04 by explicit user instruction.
WB-09 merged through PR #11 at `f3a6e8f`; PR CI/publication passed runs
`43612515436` and `43613064726`. Actual local prebuilt-digest regression passed
`20261114T160232Z-24d3b1` (92 cases, no builds). Server staging and production are complete.
Conditional WB-11 #13 fixed package concurrency; real two-event proof passed.
Published [v1.0.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.0.0),
[main workflow PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43626386129),
[remote evidence](../evidence/WB-09-remote.md). Public desktop/mobile smoke 2 passed;
23 preexisting container IDs/start times unchanged. WB-04 starts from develop `f5336c8`, issue #15.

| WB | Branch | PR | Tests / Allure | Release | State |
|---|---|---|---|---|---|
| WB-08 | `test/wb-08-regression-evidence` | [#36 develop](https://github.com/smalvik/biocad-workspace/pull/36), [#37 main](https://github.com/smalvik/biocad-workspace/pull/37), issue #33 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648), 248 regression / 224 raw Allure; public app 4/report 4/race attachments 2 passed | v1.4.1 | Genuine red 2 failed / restored green 3 passed; test-only owned DB; [evidence](../evidence/WB-08-remote.md) |
| WB-11 deadlock | `fix/wb-11-booking-deadlock` | [#35 develop](https://github.com/smalvik/biocad-workspace/pull/35), issue #34 | Standalone 240 passed, combined 248 passed, native arbitration + bounded retry tested | v1.4.1 | Actual 40P01/500 fixed; [evidence](../evidence/WB-11-booking-deadlock.md) |
| WB-07 | `feat/wb-07-email-notifications` | [#31 develop](https://github.com/smalvik/biocad-workspace/pull/31), [#32 main](https://github.com/smalvik/biocad-workspace/pull/32), issue #30 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43763748048), 237 regression / Allure 213; public app 4/report UI 4 passed | v1.4.0 | Live outbox/RabbitMQ/Worker/Mailpit; durable dedup/retry, real rollback proof; [evidence](../evidence/WB-07-remote.md) |
| WB-09 browser Allure | `ci/wb-09-allure-web` | [#28 merged](https://github.com/smalvik/biocad-workspace/pull/28), [main #29](https://github.com/smalvik/biocad-workspace/pull/29), issue #27 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43745466108), 209 regression / 185 raw Allure; public HTTP + 4 browser passed | v1.3.1 | [Inline Allure](https://biocad.smalvik.dev/allure/), version archive and original live LLM report; [evidence](../evidence/WB-09-allure-web.md) |
| WB-01 | `chore/wb-01-bootstrap` | [#2 merged](https://github.com/smalvik/biocad-workspace/pull/2) | [PR CI passed](https://github.com/smalvik/biocad-workspace/actions/runs/43598925846), [post-merge regression passed](https://github.com/smalvik/biocad-workspace/actions/runs/43599195552) | v1.0.0 | Merged; task branch retained |
| WB-02 | `feat/wb-02-booking-core` | [#4 merged](https://github.com/smalvik/biocad-workspace/pull/4), [main #6 merged](https://github.com/smalvik/biocad-workspace/pull/6) | [develop regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604565825), [main regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604855360) | v1.0.0 | In develop and main per user instruction |
| WB-11 | `fix/wb-11-outbox-probe` | [#8 merged](https://github.com/smalvik/biocad-workspace/pull/8) | [PR CI PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604235478), full post-merge regression PASS | v1.0.0 | Test harness defect fixed; no application race claimed |
| WB-03 | `feat/wb-03-interactive-map` | [#9 merged](https://github.com/smalvik/biocad-workspace/pull/9) | [PR PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608443234), [post-merge PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608755923) | v1.0.0 | In develop at af00fa1 |
| WB-09 | `ci/wb-09-release-deploy` | [#11](https://github.com/smalvik/biocad-workspace/pull/11), [main #12](https://github.com/smalvik/biocad-workspace/pull/12) | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43626386129), [remote evidence](../evidence/WB-09-remote.md) | v1.0.0 | Released, existing apps preserved |
| WB-11 delivery | `fix/wb-11-candidate-serialization` | [#14 merged](https://github.com/smalvik/biocad-workspace/pull/14) | 92-case CI + actual two-event serialization/digest equality proof | v1.0.0 | Released |
| WB-04 | `feat/wb-04-employee-locations` | [#16 merged develop](https://github.com/smalvik/biocad-workspace/pull/16), [#17 merged main](https://github.com/smalvik/biocad-workspace/pull/17), issue #15 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43636402995), 131 regression, Allure 116, public smoke 4 | v1.1.0 | Released; 23 previous containers preserved; [evidence](../evidence/WB-04-remote.md) |
| WB-05 | `feat/wb-05-booking-flow` | [#19 merged develop](https://github.com/smalvik/biocad-workspace/pull/19), [#20 merged main](https://github.com/smalvik/biocad-workspace/pull/20), issue #18 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43690831879), 157 regression, Allure 134, final public smoke 4 + preview 2 | v1.2.0 | Released; 23 previous containers preserved; [evidence](../evidence/WB-05-remote.md) |
| WB-06 | `feat/wb-06-assistant-mcp` | [#23 merged](https://github.com/smalvik/biocad-workspace/pull/23), [main #26](https://github.com/smalvik/biocad-workspace/pull/26), issue #22 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43737645275), 189 regression / Allure 165; real free 3 API + 2 browser passed | v1.3.0 | Released, free-only $0; [evidence](../evidence/WB-06-remote.md) |
| WB-11 free planning | `fix/wb-11-free-assistant-planning` | [#25 merged](https://github.com/smalvik/biocad-workspace/pull/25), issue #24 | Local/committed/server full regression and real free staging/production passed | v1.3.0 | Fixed before main promotion; no separate patch release |
| WB-10 … WB-18 (except conditional WB-11 records) | See backlog | — | — | — | TODO; next P0 WB-10 |
| WB-11 browser access | `fix/wb-11-browser-access` | [issue #21 open](https://github.com/smalvik/biocad-workspace/issues/21) | Earlier direct/VPN difference retained; user now reports browser opens | None | Monitoring; no infrastructure fix applied; [evidence](../evidence/WB-11-browser-access.md) |

For each completed task, add the real branch, SHA, PR URL, command output summary, Allure run/report URL, merge SHA, staging verification and release (if any). Keep unfinished items TODO, never fabricate completed results.

Local smoke was run before the first WB-01 commit: base HEAD `4b005dd`,
`working_tree=dirty`. On 2026-11-14 the user authorized publishing main/develop/WB-01
and continuing WB-02. Code commit `bc283c7` was pushed to
`https://github.com/smalvik/biocad-workspace`; remote main/develop/task branches verified.
PR #2 passed head CI `43598925846` and agent self-review, then was merged on
2026-11-14 at `e5bb0b5ce4980074f40e682a8beac072f73ba06f`. The review explicitly
identified itself as agent self-review, not human approval. Full post-merge regression
`43599195552` passed. No staging or release was performed. WB-02 local regression
`20261114T133549Z-a1866f` passed. The user subsequently authorized WB-02 push,
develop/main merges and WB-03. WB-02 PR #4 passed CI and merged to develop at
`523c116d8f2af3c818b9f25282158231a2c623aa`. Main promotion PR #6 is open.
Post-merge run `43602959863` failed in the outbox probe's HTTP connection reuse;
52 tests passed locally after the separate WB-11 harness fix. PR #8 merged as
`34d4f7cf140e15eca25246211f8906d0a5384292`; its CI and develop regression passed.
Main promotion PR #6 passed run `43604569715`, merged as
`59e4883e46c67bc1f35d032cbcb708cf117f5236`; post-merge main regression `43604855360` passed.
WB-03 was created from develop `34d4f7c` after both requested merges. No release/deploy.
WB-03 implementation commit: `a02a488634b226c1ba69c86aa22b15b20d2df688` (local).
Implementation commit: `5f3f66174ab8ab9d1155a0331ea8abe880706690`; later task-note
updates only record evidence. Working tree is clean after committing task documentation.
