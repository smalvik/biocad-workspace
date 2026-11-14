# Codex repository instructions — BIOCAD Workspace Booking

Read this file automatically at the start of every task. Keep it short; load other documents only when needed.

## Source of truth
1. `docs/requirements/PRD_v1.2.md` — **canonical** product requirements. Newer approved amendments, if any, go in `docs/requirements/DECISIONS.md` and then PRD.
2. `docs/context/CURRENT_STATE.md` — which artifacts exist and which product capabilities are *not* implemented.
3. `docs/tasks/BACKLOG.md` — task order, priorities and branch names. Read only the currently assigned task's `docs/tasks/WB-XX.md` and relevant PRD sections.
4. `docs/design/UI_CONTRACT.md` and `references/` — UI specifications and **concept screenshots**, not source code or proof of implementation.
5. `docs/process/DEVELOPMENT_PROCESS.md` — Git/CI/CD/release rules. `docs/interview/INTERVIEW_GUIDE.md` supports explaining decisions, not blindly copying answers.

## Non-negotiable architecture
- React frontend; Python FastAPI Booking Service and independently deployable Assistant Service; Notification Worker; PostgreSQL; RabbitMQ; MCP and real LLM via OpenRouter; Mailpit for demo email; Docker Compose; GitHub Actions; Allure + pytest/Playwright.
- Booking Service + PostgreSQL are the only authority for confirmed bookings. Enforce nonoverlap at DB layer with PostgreSQL GiST exclusion on `[start,end)` and test concurrently against **real PostgreSQL**. Adjacent intervals allowed.
- Idempotent confirmations, server-side validation, durable data, cancel-own-only, authenticated demo users. Display Europe/Moscow; store aware UTC timestamps.
- AI uses up-to-date tools through MCP and may only **propose** a booking; user explicitly confirms exact resource/date/time. AI failure must never prevent manual form bookings.
- A face on a FreeDesk means reservation occupant **for the selected time**, NOT real physical presence. Dedicated desk face means assigned owner, not presence. For multiple bookings in selected interval, show occupant count and full timeline; do not present one as occupant of entire interval.
- UI uses approximated BIOCAD green/navy tokens **until official UI Kit/rights are provided**; mark mock profiles, photos and releases as fictional.

## Task and test protocol
- Exactly one issue → one purpose-specific branch (`feat/wb-04-...`, `fix/wb-11-...`, `ci/...`, `docs/...`, `test/...`) → one reviewed PR into `develop`; Conventional Commits **messages** (`feat:`, `fix:`, etc.). Never claim Conventional Commits specifies branch names.
- Create/update unit and integration tests, and Playwright E2E for any frontend flow. Infrastructure changes need applicable integration/smoke. Collect Allure `smoke` or `regression` metadata.
- Before PR report real commands and results; no fabricated logs, CI passes, screenshots, releases, remote URLs or test counts. After merge run entire regression, then staging, smoke, publish approved immutable Docker images and release. Task notes in `docs/changes/WB-XX.md` after each completed task; release page from **published** releases only.
- Do not commit `.env`, API keys, GitHub PAT, Docker Hub token, server credentials. Do not echo tokens in logs. Do not use personal data in LLM calls without authorization.
- Follow priority P0 then P1/P2 under the 3-calendar-day deadline. Deliver working minimum over elaborate unfinished features.

## Work discipline
- Read relevant files; summarize requirements, test plan, affected services, and assumptions briefly. Make small verifiable changes with migrations, docs and tests. Check repository status and never overwrite unrelated work. Ask approval before remote pushes, creating cloud resources or deploying; never infer credentials are available.
- On finishing any task: update `docs/context/PROGRESS.md`, task changelog, evidence links, and `AI-LOG.md` with what actually happened and commands. Clarify blockers; do not mark planned capabilities as shipped.
- Do not load the whole reference image library into context at once: inspect specific PNGs for the current task only.
