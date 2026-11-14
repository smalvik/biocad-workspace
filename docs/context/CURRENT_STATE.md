# Actual implementation status — 2026-11-14

| Item | Observed state |
|---|---|
| Product requirements | PRD v1.2 written (Markdown/Word), with WB-01…WB-18 backlog |
| Visuals | 54 current responsive PNGs (18 WB steps × desktop/tablet/mobile), 12 time-window PNGs + comparison, older conceptual PNGs |
| Static demos | HTML employee-map demo, release-history mock and visual viewer; **not deployed React application** |
| Interview preparation | 72 draft Q&A, technical architecture decisions and sample release-note templates |
| Demo employee data | Fictional employees and calendar scenario; see `docs/data/demo_fixture.json` |
| React application | Vite/TypeScript service-status page with unit/browser smoke; no booking UI |
| FastAPI services | Booking auth/resource/create/own-list/cancel API added in WB-02; Assistant remains health/OpenAPI skeleton |
| PostgreSQL schema/tests | Alembic core schema, GiST [start,end), per-user idempotency, atomic outbox and fictional seed; real concurrency + restart regression passed locally |
| RabbitMQ/MCP/real LLM | Compose RabbitMQ + AMQP smoke implemented; application RPC/MCP/LLM not implemented |
| Mailpit/email sending | Compose Mailpit + fictional SMTP smoke implemented; Notification Worker not implemented |
| GitHub repository/branches/PRs | main/develop/WB-01 pushed to smalvik/biocad-workspace; issue #1, PR #2 created |
| Docker Hub image/release | Local runtime/test images built; nothing published to Docker Hub |
| Ubuntu 22.04 staging/production | NOT DEPLOYED by this package |
| Allure report/evidence | WB-01 CI artifacts; WB-02 local report 50 passed (52 tests incl. Vitest); no public report hosting |
| GitHub Actions | WB-01 PR and full post-merge regression passed; WB-02 remote run not yet created |
| Official BIOCAD UI Kit | NOT PROVIDED / not verified; approximate reference styling only |

Source of truth for requirements: `docs/requirements/PRD_v1.2.md`. Source of truth for implementation state: actual git tree, code, test command results and links; update this status as work progresses.

WB-01 continues existing uncommitted scaffolding on `chore/wb-01-bootstrap`,
created from `develop` without discarding earlier work. Base HEAD: `4b005dd`;
the first smoke tested an uncommitted working tree. Actual outcomes and publication
status: [WB-01](../changes/WB-01.md), [PROGRESS](PROGRESS.md).
WB-01 merged through PR #2 at `e5bb0b5` after CI and explicit agent self-review;
post-merge regression passed. WB-02 passed locally on its own branch
`feat/wb-02-booking-core`, created from that develop; its branch is not published.
No new frontend flow yet. Next product work after review: WB-03 interactive map.

GitHub repo confirmed: https://github.com/smalvik/biocad-workspace.
Still unverified: Docker Hub namespace, deployment host/access, official BIOCAD UI Kit,
approved/funded OpenRouter model and budget. Do not ask for raw credentials in chat;
use local env and CI secrets.
