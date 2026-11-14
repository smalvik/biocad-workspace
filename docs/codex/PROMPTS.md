# Reusable Codex prompts (one at a time)

## 1. Read-only project review
"Read `AGENTS.md`, `docs/context/CURRENT_STATE.md`, the canonical PRD and BACKLOG. Inspect the current repository. Do not edit or run external actions. Summarize implemented vs missing and risks, in ≤600 words, and propose next scoped task."

## 2. Start ONE task
"Implement only WB-XX following `docs/tasks/WB-XX.md` and `AGENTS.md`. First inspect existing code and current develop branch. Summarize plan and tests. Create the appropriate branch if git is configured and I have approved local branch changes. Implement minimal production-quality feature and tests, run relevant commands. Report real outcomes, update task note and progress. Do not push/deploy without approval."

## 3. Review and finishing the task
"Review all diffs on the current branch against WB-XX acceptance criteria. Run applicable unit, integration, Playwright E2E and static checks, save actual Allure output, explain failures and missing tests. Update `docs/changes/WB-XX.md`, progress and AI-LOG. Suggest commit message using Conventional Commits. Do not assert PR merge or release unless it actually happened."

## 4. Prepare merge & regression
"Check branch readiness, provide PR description, test commands and evidence. After I approve merge, run the full regression on `develop`; report real Allure artifact paths and any failures. No fictional reports."

## 5. Release preparation
"Given an approved and fully tested develop SHA, run staging validation, produce release notes only from actually merged tasks and actual passing checks; propose SemVer 1.MINOR.PATCH. Identify image digests and rollback plan. Ask explicit approval before GitHub release, Docker Hub publish, or deployment."

## 6. Resume after context/window reset
"Open `AGENTS.md`, `docs/context/PROGRESS.md`, `docs/tasks/BACKLOG.md`, the current WB task file, and `git status`. Do not rely on old chat history. Summarize current branch, last actual test evidence, next 3 concrete steps, and continue only this task. Avoid rereading entire PRD unless needed."

## 7. Reduce context cost
"Find smallest set of relevant docs and files for this task; do not paste large PRD or screenshots into chat. Use grep/ripgrep and concise summaries, share file paths. Test targeted behavior, then full regression before release."
