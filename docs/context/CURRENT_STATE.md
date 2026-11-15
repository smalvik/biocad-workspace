# Actual implementation status — 2026-11-15

**WB-07 in progress:** issue #30, `feat/wb-07-email-notifications` from develop fd81f82.
Outbox publisher, private durable notification inbox and branded Mailpit emails implemented
locally; final reviewed-source regression passed 237 checks / 211 raw Allure results.
Real upgrade/rollback passed; final committed-head CI and delivery remain pending.
Production remains v1.3.1 until checked delivery; no notifications release claimed yet.

**WB-09 follow-up #27 released v1.3.1:** [Allure opens in the browser](https://biocad.smalvik.dev/allure/),
with immutable version URLs and [actual free-model report](https://biocad.smalvik.dev/allure/v1.3.0/live/).
Main CI publishes after release and checks inline/type/source/checksum.
[Actual evidence](../evidence/WB-09-allure-web.md); 4 public desktop/mobile report cases passed,
zero downloads. Existing data and 23 unrelated containers preserved.

**WB-06 and WB-11 planning fix released as v1.3.0.**
Current production: **https://biocad.smalvik.dev** ·
[published v1.3.1](https://github.com/smalvik/biocad-workspace/releases/tag/v1.3.1) ·
[remote evidence](../evidence/WB-06-remote.md).
Main/source **8d8cf08f9f43c3568c6bd737053101bf8c80ac7d**; develop **fd81f82**.
User pause was explicitly resumed; [historical handoff](PAUSE_HANDOFF.md).

| Capability | Observed state |
|---|---|
| Booking authority | Live Booking FastAPI + PostgreSQL; GiST `[start,end)`, real concurrent winner/adjacency tests, durable UTC data, authenticated fictional users, CSRF and idempotency |
| React manual flow | Two-floor SVG map, Moscow period/filtering, employee lookup, fictional portraits, selected-period occupancy/timeline; explicit confirmation, own list and cancel-own-only; retry/reload |
| Assistant | Independently deployed FastAPI; official MCP 2.3.0 STDIO tools; all Booking interservice calls via durable RabbitMQ RPC; no Assistant DB access or network HTTP to Booking |
| Real LLM | OpenRouter `inclusionai/ling-3.2-flash:free`; free-only consent, budget $0, catalog zero-price checks and per-request zero caps; no paid fallback |
| AI booking | User consent, live read/propose tools, map highlight, signed user-bound 10-minute proposal, separate exact confirmation; no automatic booking; AI failure leaves manual form available |
| Rate/limits | Durable 3 requests/user/minute, bounded tools/rounds/time/input, one bounded same-model 429 retry; provider capacity is not guaranteed |
| Mailpit/notifications | WB-07 implemented/tested locally: outbox → RabbitMQ → independent durable Worker → HTML/text Mailpit emails. PR/release pending; production remains v1.3.1 |
| CI/CD | GitHub Actions → immutable Docker Hub digests → complete isolated server regression → staging/smoke → exact production digests/HTTPS smoke → aliases/release/Allure |
| Deploy isolation | Separate `biocad-staging`/`biocad-production`; existing Traefik ingress; 23 unrelated containers preserved, backup/previous v1.3.0 retained |
| Requirements/visuals | PRD v1.2 + approved DECISIONS canonical; references/static HTML are concepts, not implementation evidence; official BIOCAD UI Kit/rights not provided |

Main [workflow 43745466108](https://github.com/smalvik/biocad-workspace/actions/runs/43745466108)
passed **209 checks** (97 Booking/delivery, 24 Assistant, 2 persistence, 26 Vitest
and 60 Playwright); server Allure **185 raw results** (183 regression + stage/prod smoke),
Vitest separately. CI provider is explicitly scripted; MCP/RabbitMQ/PostgreSQL real.
Original v1.3.0 production actual-free acceptance: **3 API + 2 desktop/mobile browser cases**,
all successful provider responses cost=0, no booking writes. Initial mobile provider
429 is retained separately; final sequential repeat passed without runtime/model changes.
Existing 7 bookings/12 accounts per environment and all 23 other containers preserved.
The v1.3.1 follow-up made no new inference calls; it hosts those original live results.

Next unfinished P0: **WB-07 email Notification Worker**, then WB-08 race/red-green
evidence and remaining delivery docs. P1 comfort/quiz/failover/feedback and the actual
in-product release-history page are not claimed delivered. See [backlog](../tasks/BACKLOG.md).

Browser access incident [#21](https://github.com/smalvik/biocad-workspace/issues/21)
remains monitoring: user reports access restored, current public browser checks pass;
no DNS/proxy/client route remediation was applied and the original direct/VPN cause
is not established. [Diagnosis](../evidence/WB-11-browser-access.md).

Earlier releases: [v1.0.0/WB-09](../evidence/WB-09-remote.md),
[v1.1.0/WB-04](../evidence/WB-04-remote.md), [v1.2.0/WB-05](../evidence/WB-05-remote.md).
All employee profiles/portraits/demo calendar data are fictional.
