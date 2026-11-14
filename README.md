# BIOCAD Workspace Booking — Codex handoff kit

> IMPORTANT: This repository currently contains **requirements, demo data and reference mockups**. It **does not** yet contain the working React/FastAPI service, successful CI, deployed site, official BIOCAD UI kit or valid releases. The user asked for a three-day full-stack interview assignment; all demonstrations must be backed by real code, testing and deploy evidence.

## Begin here (VS Code + Codex)
1. Unzip the handoff; open **`biocad-workspace`** as the VS Code workspace folder (`File → Open Folder`).
2. Install/open the official **Codex IDE extension**, sign in using your ChatGPT account; or use Codex CLI from the workspace terminal.
3. Open `START_HERE.md` and paste the text from `CODEX_FIRST_PROMPT.md` into Codex. The root `AGENTS.md` is its recurring task contract.
4. Run `python scripts/verify_handoff.py` to confirm files and asset counts. This does not test a product.
5. Let Codex perform a **read-only inventory and plan first**, then start WB-01 on its own branch. Continue task-by-task, not by pasting the full PRD into every chat.
6. Configure API keys and tokens **locally** using env files ignored by Git and GitHub Actions Secrets, never in chats or committed files.

## Canonical project contents
- `docs/requirements/PRD_v1.2.md` — full PRD v1.2, the canonical scope and acceptance rules.
- `docs/context/CHAT_HANDOFF.md` — human-readable distilled history of decisions across this ChatGPT thread.
- `docs/context/CURRENT_STATE.md` — evidence-based status; no code falsely marked shipped.
- `docs/tasks/` — branch-by-task backlog WB-01…WB-18.
- `docs/design/UI_CONTRACT.md` — map/avatars/calendar/drawer/responsiveness/UI tokens.
- `references/desktop`, `tablet`, `mobile` — 54 latest PNGs covering 18 WB steps.
- `references/calendar_scenarios` — 12 scenarios + overview for four time ranges.
- `references/legacy` — early prototypes/reference PNGs, not requirements.
- `references/viewer_standalone.html` — static interactive viewer, **not** React/MCP production code.
- `docs/interview/INTERVIEW_GUIDE.md` — 72 practice questions/answers.
- `docs/changes` and `docs/releases` — task/release notes templates. Historic release UI is **demo only**.
- `docs/process/DEVELOPMENT_PROCESS.md` — required Git, test, staging and release procedure.
- `CODEX_FIRST_PROMPT.md` and `docs/codex/PROMPTS.md` — prompts for startup and one task at a time.

## Primary rules
The real product must implement the original test assignment faithfully, including PostgreSQL concurrent booking, adjacent timestamps, idempotency, persistence, working React booking form, live MCP + real LLM assistant, RabbitMQ services, Mailpit, Playwright / pytest / Allure, C1/C2/ADR/AI-LOG and a public deploy. P1 comfort features, quiz and feedback follow working P0.

Do not count these PNGs, copied markdown documents or HTML prototypes as completed product development. See `docs/context/CURRENT_STATE.md`.
