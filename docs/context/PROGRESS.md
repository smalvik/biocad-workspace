# Development progress (fill with actual evidence)

**2026-11-14:** WB-01 continued from existing uncommitted React/FastAPI scaffolding.
Local implementation passed verification; product booking features remain TODO.

| WB | Branch | PR | Tests / Allure | Release | State |
|---|---|---|---|---|---|
| WB-01 | `chore/wb-01-bootstrap` | [#2](https://github.com/smalvik/biocad-workspace/pull/2) | [17 passed locally](../evidence/WB-01-local.md), Allure 15 passed | Unreleased | Pushed; PR CI running; merge pending |
| WB-02 … WB-18 | See backlog | — | — | — | TODO; WB-11 conditional |

For each completed task, add the real branch, SHA, PR URL, command output summary, Allure run/report URL, merge SHA, staging verification and release (if any). Keep unfinished items TODO, never fabricate completed results.

Local smoke was run before the first WB-01 commit: base HEAD `4b005dd`,
`working_tree=dirty`. On 2026-11-14 the user authorized publishing main/develop/WB-01
and continuing WB-02. Code commit `bc283c7` was pushed to
`https://github.com/smalvik/biocad-workspace`; remote main/develop/task branches verified.
Issue #1 and PR #2 were created; CI run `43598608460` started. No CI pass/merge is claimed here.
No staging or release was performed. Next: WB-01 review/integration, then WB-02.
