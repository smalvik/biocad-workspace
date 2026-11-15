# Conversation handoff — BIOCAD Workspace Booking

**Current release on 2026-11-15:** v1.3.1, main 8d8cf08 / develop fd81f82.
WB-06 + fix #24 shipped v1.3.0; browser Allure follow-up #27 now also released.
Read CURRENT_STATE and [actual remote proof](../evidence/WB-09-allure-web.md).
Public report: https://biocad.smalvik.dev/allure/. Free models only / $0.
Next P0 is WB-07. Post-release evidence is committed on retained `ci/wb-09-allure-web`;
carry those documentation changes onto the next branch from develop before new work.
The [pause record](PAUSE_HANDOFF.md) is historical, not an active stop instruction.

This is an authored, curated summary of the **visible user requirements and created artifacts**, not a verbatim transcript or automatic transfer of ChatGPT private context. Resolve any conflict using the newest PRD v1.2 and explicit human updates.

## Original interview assignment
Three-day deadline; Git repo and live deployed React/FastAPI app with bookings of desks and meeting rooms on self-made floor plans, controls for floor/date/time/zoom, legend and card; booking from form or LLM chat only after explicit confirmation; up-to-date MCP data; Moscow time; no overlapping bookings; adjacent intervals allowed; one winner on concurrent requests; idempotent repeated confirmations; invalid data rejected; persisted across restart; app usable without AI; tests including intentionally disabled protection demonstrating a detectable race; README, C1/C2, ADR ×2, <=1-page AI-LOG. Real LLM API required.

## Product design history
- Early screens: 13 standalone desktop visuals for plan, desk, form, success, meeting room, AI suggestions/confirmation, bookings/cancel, empty, conflict, AI outage/loading.
- Enhanced employee map: named mock staff (FIO, job title, department and avatar); differentiate permanently assigned `DEDICATED` vs bookable FreeDesk vs FreeDesk temporarily reserved; on selecting occupied place show occupant and exact date/time; employee search focuses map; right drawer; after a booking ends, slot is free unless another overlaps.
- PRD 1.0 enterprise delivery workflow; PRD 1.1 added AI primary→free OpenRouter model fallback, personalized comfort search (`floor<=2`, near window, away from AC), quiz, ratings/feedback and repeat suggestions; PRD 1.2 added on-map avatars tied to selected time/calendar, multiple bookings and timeline; task change notes, release-history page and 72 interview Q&As.
- 54 responsive visual mocks for WB-01…WB-18 (desktop/tablet/mobile). Latest ones include avatars and period-driven occupancy. These images are visual intentions, not implementation code.

## UX/data invariants
- Dates: Europe/Moscow in the UI; aware UTC in DB; booking periods are half-open `[start, end)`.
- Desk D-03 on 2026-11-16: Maria Sokolova 10–12; free 12–14; Pavel Gromov 14–16; across a whole-day view show two occupants/timeline not one misleading avatar. Dedicated owner avatars indicate assignment, not physical presence. FreeDesk occupant avatars indicate booking for selected time, not physical presence.
- Dedicated desks cannot be booked even if owner absent; time-window FreeDesk occupancy uses server-derived overlapping bookings.
- On frontend conflict reload occupancy and display changed occupant/period; server is definitive authority.
- LLM search proposes and highlights real available candidate; only Booking Service writes after explicit confirmation. AI fallback/unavailable clearly identified; form always works.
- Comfort constraints must distinguish hard verified facts from unverified/subjective noise, draft and temperature comments. Prior feedback private, no auto booking without confirmation.

## Enterprise process requested by user
- Task tracker → one issue / one appropriately named feature/bug/docs/CI branch → tests → PR into `develop` → full regression → staging mock data and regression → SemVer `1.MINOR.PATCH` release on verified source → Docker Hub immutable version + latest tags → hook/webhook to deploy on Ubuntu 22.04 Docker; document rollout/rollback.
- Conventional Commits applies to commit messages; project naming convention applies to branches.
- pytest, Playwright and Allure smoke/regression evidence. Email notifications into Mailpit using BIOCAD-style branded templates. Release notes per completed task and in-product `/releases` page with real public releases only.
- Interview book of technical Q&A per task, explain why choice was made, alternatives and tests; when code exists link real paths/PRs/evidence.

## User context that matters (non-sensitive)
- Developing in Visual Studio Code with Codex; git remote will be GitHub, registry Docker Hub, server Ubuntu 22.04 with Docker installed. Tokens/credentials not supplied here; never request them in prompt/chat. User has strict 3-day and token budget.

## Visual source priority
1. `references/{desktop,tablet,mobile}/WB-XX_*.png` — current v1.2 (54)
2. `references/calendar_scenarios/` — WB-16 precise time views
3. `references/legacy/` — previous iterations for history only
The latest PRD takes precedence over inconsistent text that a generative screenshot might contain.
