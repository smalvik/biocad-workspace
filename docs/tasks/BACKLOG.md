# Task backlog — current v1.2

Each task corresponds to an issue and isolated branch; may be deferred if P1/P2. WB-11 only exists when an actual bug occurs. Infrastructure process requirements (Allure, release notes, documentation) start in WB-01 even when their dedicated WB task appears later.

| ID | Priority | Branch | Goal |
|---|---|---|---|
| WB-01 | P0 | `chore/wb-01-bootstrap` | Repo/Compose/CI skeleton |
| WB-02 | P0 | `feat/wb-02-booking-core` | Booking Core / PostgreSQL |
| WB-03 | P0 | `feat/wb-03-interactive-map` | React SVG floor map |
| WB-04 | P0 | `feat/wb-04-employee-locations` | Employee lookup + avatar occupancy |
| WB-05 | P0 | `feat/wb-05-booking-flow` | Form/bookings/cancel |
| WB-06 | P0 | `feat/wb-06-assistant-mcp` | Assistant with real LLM + MCP |
| WB-07 | P0 | `feat/wb-07-email-notifications` | Mailpit notifications |
| WB-08 | P0 | `test/wb-08-regression-evidence` | Allure + race red-green evidence |
| WB-09 | P0 | `ci/wb-09-release-deploy` | Staging/prod CI/CD |
| WB-10 | P0 | `docs/wb-10-delivery-evidence` | README/ADR/C1-C2/AI-LOG |
| WB-11 | Conditional | `fix/wb-11-booking-race` | Bug-fix branch (only if found) |
| WB-12 | P1 | `feat/wb-12-llm-failover` | Primary/redundant LLM |
| WB-13 | P1 | `feat/wb-13-comfort-search` | Comfort NLP search |
| WB-14 | P1 | `feat/wb-14-comfort-quiz` | Preference quiz |
| WB-15 | P2 | `feat/wb-15-comfort-feedback` | Feedback/rebooking |
| WB-16 | P1 | `feat/wb-16-occupancy-timeline` | Multi-occupant calendar timeline |
| WB-17 | P0 process/P1 UI | `feat/wb-17-release-history` | Release notes and history page |
| WB-18 | P0 docs | `docs/wb-18-interview-playbook` | Interview playbook |

See `WB-XX.md` for scoped task instructions. Canonical product requirements remain in `docs/requirements/PRD_v1.2.md`.
