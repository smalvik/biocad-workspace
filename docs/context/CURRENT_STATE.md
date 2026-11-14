# Actual implementation status — 2026-11-14

| Item | Observed state |
|---|---|
| Product requirements | PRD v1.2 written (Markdown/Word), with WB-01…WB-18 backlog |
| Visuals | 54 current responsive PNGs (18 WB steps × desktop/tablet/mobile), 12 time-window PNGs + comparison, older conceptual PNGs |
| Static demos | HTML employee-map demo, release-history mock and visual viewer; **not deployed React application** |
| Interview preparation | 72 draft Q&A, technical architecture decisions and sample release-note templates |
| Demo employee data | Fictional employees and calendar scenario; see `docs/data/demo_fixture.json` |
| React application | v1.0.0 map live; WB-04 employee search/avatars/timeline/fallback locally tested (131 cases), not released yet; no booking form |
| FastAPI services | Booking Core plus locally tested authenticated employee directory/location and batch public occupancy profiles; Assistant remains health/OpenAPI skeleton |
| PostgreSQL schema/tests | Alembic core schema, GiST [start,end), per-user idempotency, atomic outbox and fictional seed; real concurrency + restart regression passed locally |
| RabbitMQ/MCP/real LLM | Compose RabbitMQ + AMQP smoke implemented; application RPC/MCP/LLM not implemented |
| Mailpit/email sending | Compose Mailpit + fictional SMTP smoke implemented; Notification Worker not implemented |
| GitHub repository/branches/PRs | WB-09 #11 / CI fix #14 / main promotion #12 merged; v1.0.0 source e7ba97b; WB-04 issue #15 started from develop f5336c8 |
| Docker Hub image/release | Three runtime images with verified v1.0.0/latest aliases; seven immutable runtime/test SHA candidates and exact published digest manifest |
| Staging/production | Both live, isolated on existing Ubuntu 24.04 / Traefik host; production HTTPS, restricted CI key, backups/rollback; 23 preexisting containers preserved |
| Allure report/evidence | Main CI 92 passed; server Allure 84 (regression + stage/prod smoke), Vitest 10 separately; independent public desktop/mobile smoke 2 passed |
| GitHub Actions | Main 43626386129 passed checks, publication, server regression/staging/prod and release/Allure publishing; real same-SHA serialization proof passed |
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
Docker Hub namespace and server access/deployment are verified; see [remote evidence](../evidence/WB-09-remote.md).
Still unverified: official BIOCAD UI Kit and approved/funded OpenRouter model/budget. Do not ask for raw credentials in chat;
use local env and CI secrets.
