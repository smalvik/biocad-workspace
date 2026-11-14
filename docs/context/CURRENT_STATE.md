# Actual implementation status — 2026-11-14

| Item | Observed state |
|---|---|
| Product requirements | PRD v1.2 written (Markdown/Word), with WB-01…WB-18 backlog |
| Visuals | 54 current responsive PNGs (18 WB steps × desktop/tablet/mobile), 12 time-window PNGs + comparison, older conceptual PNGs |
| Static demos | HTML employee-map demo, release-history mock and visual viewer; **not deployed React application** |
| Interview preparation | 72 draft Q&A, technical architecture decisions and sample release-note templates |
| Demo employee data | Fictional employees and calendar scenario; see `docs/data/demo_fixture.json` |
| React application | Local authenticated React SVG map, 2 floors/41 resources, calendar/type filters, pan/zoom/fit, responsive details; no booking form yet |
| FastAPI services | Booking auth/resource/create/own-list/cancel API added in WB-02; Assistant remains health/OpenAPI skeleton |
| PostgreSQL schema/tests | Alembic core schema, GiST [start,end), per-user idempotency, atomic outbox and fictional seed; real concurrency + restart regression passed locally |
| RabbitMQ/MCP/real LLM | Compose RabbitMQ + AMQP smoke implemented; application RPC/MCP/LLM not implemented |
| Mailpit/email sending | Compose Mailpit + fictional SMTP smoke implemented; Notification Worker not implemented |
| GitHub repository/branches/PRs | WB-01/02/WB-11 pushed; PR #4/#8 into develop, PR #6 into main merged; WB-03 local branch from develop |
| Docker Hub image/release | Local runtime/test images built; nothing published to Docker Hub |
| Ubuntu 22.04 staging/production | NOT DEPLOYED by this package |
| Allure report/evidence | WB-03 local: 79 passed, Allure 69 results + 10 Vitest; actual desktop/mobile screenshots; CI artifacts for integrated tasks |
| GitHub Actions | WB-02/WB-11 PRs plus full develop/main regression passed; WB-03 remote run not created |
| Official BIOCAD UI Kit | NOT PROVIDED / not verified; approximate reference styling only |

Source of truth for requirements: `docs/requirements/PRD_v1.2.md`. Source of truth for implementation state: actual git tree, code, test command results and links; update this status as work progresses.

WB-01 continues existing uncommitted scaffolding on `chore/wb-01-bootstrap`,
created from `develop` without discarding earlier work. Base HEAD: `4b005dd`;
the first smoke tested an uncommitted working tree. Actual outcomes and publication
status: [WB-01](../changes/WB-01.md), [PROGRESS](PROGRESS.md).
WB-01 merged through PR #2 at `e5bb0b5` after CI and explicit agent self-review;
post-merge regression passed. WB-02 and WB-11 were integrated into develop and,
by explicit user instruction, main (snapshot, no release/deploy). WB-03 is locally
tested on `feat/wb-03-interactive-map`, created from develop `34d4f7c` after those merges.
Next product work after WB-03 review: WB-04 employee lookup/avatars, then WB-05 form.

GitHub repo confirmed: https://github.com/smalvik/biocad-workspace.
Still unverified: Docker Hub namespace, deployment host/access, official BIOCAD UI Kit,
approved/funded OpenRouter model and budget. Do not ask for raw credentials in chat;
use local env and CI secrets.
