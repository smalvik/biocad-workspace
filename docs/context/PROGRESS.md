# Development progress (fill with actual evidence)

**2026-11-14:** WB-01 continued from existing uncommitted React/FastAPI scaffolding.
WB-01 is merged; WB-02 Booking API is implemented and verified locally.
WB-03 map and WB-04 employee lookup/portraits are live; booking form and AI remain TODO.
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
| WB-01 | `chore/wb-01-bootstrap` | [#2 merged](https://github.com/smalvik/biocad-workspace/pull/2) | [PR CI passed](https://github.com/smalvik/biocad-workspace/actions/runs/43598925846), [post-merge regression passed](https://github.com/smalvik/biocad-workspace/actions/runs/43599195552) | v1.0.0 | Merged; task branch retained |
| WB-02 | `feat/wb-02-booking-core` | [#4 merged](https://github.com/smalvik/biocad-workspace/pull/4), [main #6 merged](https://github.com/smalvik/biocad-workspace/pull/6) | [develop regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604565825), [main regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604855360) | v1.0.0 | In develop and main per user instruction |
| WB-11 | `fix/wb-11-outbox-probe` | [#8 merged](https://github.com/smalvik/biocad-workspace/pull/8) | [PR CI PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43604235478), full post-merge regression PASS | v1.0.0 | Test harness defect fixed; no application race claimed |
| WB-03 | `feat/wb-03-interactive-map` | [#9 merged](https://github.com/smalvik/biocad-workspace/pull/9) | [PR PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608443234), [post-merge PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608755923) | v1.0.0 | In develop at af00fa1 |
| WB-09 | `ci/wb-09-release-deploy` | [#11](https://github.com/smalvik/biocad-workspace/pull/11), [main #12](https://github.com/smalvik/biocad-workspace/pull/12) | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43626386129), [remote evidence](../evidence/WB-09-remote.md) | v1.0.0 | Released, existing apps preserved |
| WB-11 delivery | `fix/wb-11-candidate-serialization` | [#14 merged](https://github.com/smalvik/biocad-workspace/pull/14) | 92-case CI + actual two-event serialization/digest equality proof | v1.0.0 | Released |
| WB-04 | `feat/wb-04-employee-locations` | [#16 merged develop](https://github.com/smalvik/biocad-workspace/pull/16), [#17 merged main](https://github.com/smalvik/biocad-workspace/pull/17), issue #15 | [Main/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43636402995), 131 regression, Allure 116, public smoke 4 | v1.1.0 | Released; 23 previous containers preserved; [evidence](../evidence/WB-04-remote.md) |
| WB-05 … WB-18 (except WB-09/WB-11) | See backlog | — | — | — | TODO |

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
