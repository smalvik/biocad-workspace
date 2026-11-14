# Development progress (fill with actual evidence)

**2026-11-14:** WB-01 continued from existing uncommitted React/FastAPI scaffolding.
WB-01 is merged; WB-02 Booking API is implemented and verified locally.
The product map, form and AI remain TODO.

| WB | Branch | PR | Tests / Allure | Release | State |
|---|---|---|---|---|---|
| WB-01 | `chore/wb-01-bootstrap` | [#2 merged](https://github.com/smalvik/biocad-workspace/pull/2) | [PR CI passed](https://github.com/smalvik/biocad-workspace/actions/runs/43598925846), [post-merge regression passed](https://github.com/smalvik/biocad-workspace/actions/runs/43599195552) | Unreleased | Merged; task branch retained |
| WB-02 | `feat/wb-02-booking-core` | [#4 merged](https://github.com/smalvik/biocad-workspace/pull/4), [main PR #6](https://github.com/smalvik/biocad-workspace/pull/6) | [PR CI passed](https://github.com/smalvik/biocad-workspace/actions/runs/43602548303); post-merge harness defect tracked in WB-11 | Unreleased | In develop; main promotion waits for fixed regression |
| WB-11 | `fix/wb-11-outbox-probe` | [Issue #7](https://github.com/smalvik/biocad-workspace/issues/7) | [52 passed locally](../changes/WB-11.md) | Unreleased | Fault-probe connection fix, PR pending |
| WB-03 … WB-18 | See backlog | — | — | — | TODO; WB-11 conditional |

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
52 tests pass locally after the separate WB-11 harness fix. No main merge yet.
Implementation commit: `5f3f66174ab8ab9d1155a0331ea8abe880706690`; later task-note
updates only record evidence. Working tree is clean after committing task documentation.
