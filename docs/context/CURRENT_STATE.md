# Actual implementation status — 2026-11-14

| Item | Observed state |
|---|---|
| Product requirements | PRD v1.2 written (Markdown/Word), with WB-01…WB-18 backlog |
| Visuals | 54 current responsive PNGs (18 WB steps × desktop/tablet/mobile), 12 time-window PNGs + comparison, older conceptual PNGs |
| Static demos | HTML employee-map demo, release-history mock and visual viewer; **not deployed React application** |
| Interview preparation | 72 draft Q&A, technical architecture decisions and sample release-note templates |
| Demo employee data | Fictional employees and calendar scenario; see `docs/data/demo_fixture.json` |
| React application | Vite/TypeScript service-status page with unit/browser smoke; no booking UI |
| FastAPI services | Independent Booking + Assistant health/OpenAPI; Booking PostgreSQL readiness |
| PostgreSQL schema/tests | Real PostgreSQL readiness smoke; no domain schema, migration or exclusion constraint yet |
| RabbitMQ/MCP/real LLM | Compose RabbitMQ + AMQP smoke implemented; application RPC/MCP/LLM not implemented |
| Mailpit/email sending | Compose Mailpit + fictional SMTP smoke implemented; Notification Worker not implemented |
| GitHub repository/branches/PRs | Local main/develop exist; WB-01 branch created; no remote action in this session |
| Docker Hub image/release | NOT BUILT/UPLOADED by this package |
| Ubuntu 22.04 staging/production | NOT DEPLOYED by this package |
| Allure report/evidence | Per-run local results in artifacts; final WB-01 results in task note; no published report |
| GitHub Actions | CI workflow written; no remote run claimed |
| Official BIOCAD UI Kit | NOT PROVIDED / not verified; approximate reference styling only |

Source of truth for requirements: `docs/requirements/PRD_v1.2.md`. Source of truth for implementation state: actual git tree, code, test command results and links; update this status as work progresses.

WB-01 continues existing uncommitted scaffolding on `chore/wb-01-bootstrap`,
created from `develop` without discarding earlier work. Base HEAD: `4b005dd`;
the first smoke tested an uncommitted working tree. Actual outcomes and publication
status: [WB-01](../changes/WB-01.md), [PROGRESS](PROGRESS.md).
Next product task: WB-02 PostgreSQL domain schema, authentication, booking invariants
and concurrent tests after WB-01 review/integration.

Open questions (do not invent answers): GitHub repo name/organization, Docker Hub namespace, server hostname/IP + SSH access, availability of actual BIOCAD UI Kit, which OpenRouter model is funded/allowed, secrets and budget. Do not ask for raw credentials in chats; use local env and CI secrets.
