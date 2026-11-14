# Actual status at handoff — 2026-11-14

| Item | Observed state |
|---|---|
| Product requirements | PRD v1.2 written (Markdown/Word), with WB-01…WB-18 backlog |
| Visuals | 54 current responsive PNGs (18 WB steps × desktop/tablet/mobile), 12 time-window PNGs + comparison, older conceptual PNGs |
| Static demos | HTML employee-map demo, release-history mock and visual viewer; **not deployed React application** |
| Interview preparation | 72 draft Q&A, technical architecture decisions and sample release-note templates |
| Demo employee data | Fictional employees and calendar scenario; see `docs/data/demo_fixture.json` |
| React application | NOT IMPLEMENTED in this handoff |
| FastAPI services | NOT IMPLEMENTED in this handoff |
| PostgreSQL schema/tests | NOT IMPLEMENTED in this handoff |
| RabbitMQ/MCP/real LLM | NOT IMPLEMENTED in this handoff |
| Mailpit/email sending | NOT IMPLEMENTED in this handoff |
| GitHub repository/branches/PRs | NOT CREATED by this package |
| Docker Hub image/release | NOT BUILT/UPLOADED by this package |
| Ubuntu 22.04 staging/production | NOT DEPLOYED by this package |
| Allure report/evidence | NOT EXECUTED by this package |
| Official BIOCAD UI Kit | NOT PROVIDED / not verified; approximate reference styling only |

Source of truth for requirements: `docs/requirements/PRD_v1.2.md`. Source of truth for implementation state: actual git tree, code, test command results and links; update this status as work progresses.

Open questions (do not invent answers): GitHub repo name/organization, Docker Hub namespace, server hostname/IP + SSH access, availability of actual BIOCAD UI Kit, which OpenRouter model is funded/allowed, secrets and budget. Do not ask for raw credentials in chats; use local env and CI secrets.
