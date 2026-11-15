# Actual implementation status — 2026-11-16 (Moscow)

**WB-08 in progress / discovered WB-11 #34:** a real synchronized two-process probe
found PostgreSQL deadlock `40P01` returning HTTP 500 in v1.4.0; exclusion still prevents
double booking. Separate `fix/wb-11-booking-deadlock` adds native conflict arbitration
and bounded complete-transaction retry. The retry-only probe passed but a 20-request
full run exposed a deadlock cascade; native-path full 240 checks passed. No production update yet.
[Actual bug evidence](../evidence/WB-11-booking-deadlock.md).

**WB-07 released v1.4.0:** PR #31 → develop 82d14a4, #32 → main 5decd64.
Outbox → RabbitMQ → independent durable Notification Worker → private Mailpit HTML/text
emails work in staging and production. Full local/committed/server regression **237 passed**;
real outage/recovery, replay deduplication and old-image upgrade/rollback passed.
[Actual evidence](../evidence/WB-07-remote.md).
Published 15 November 21:43:49 UTC / 16 November 00:43:49 Moscow.

**WB-09 follow-up #27 released v1.3.1:** [Allure opens in the browser](https://biocad.smalvik.dev/allure/),
with immutable version URLs and [actual free-model report](https://biocad.smalvik.dev/allure/v1.3.0/live/).
Main CI publishes after release and checks inline/type/source/checksum.
[Actual evidence](../evidence/WB-09-allure-web.md); 4 public desktop/mobile report cases passed,
zero downloads. Existing data and 23 unrelated containers preserved.

**WB-06 and WB-11 planning fix released as v1.3.0.**
Current production: **https://biocad.smalvik.dev** ·
[published v1.4.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.0) ·
[remote evidence](../evidence/WB-07-remote.md).
Production/staging source **5decd646785e8b9932dab7aa838ae2a3f1f74f7b**; develop **82d14a4**.
User pause was explicitly resumed; [historical handoff](PAUSE_HANDOFF.md).

| Capability | Observed state |
|---|---|
| Booking authority | Live Booking FastAPI + PostgreSQL; GiST `[start,end)`, real concurrent winner/adjacency tests, durable UTC data, authenticated fictional users, CSRF and idempotency |
| React manual flow | Two-floor SVG map, Moscow period/filtering, employee lookup, fictional portraits, selected-period occupancy/timeline; explicit confirmation, own list and cancel-own-only; retry/reload |
| Assistant | Independently deployed FastAPI; official MCP 2.3.0 STDIO tools; all Booking interservice calls via durable RabbitMQ RPC; no Assistant DB access or network HTTP to Booking |
| Real LLM | OpenRouter `inclusionai/ling-3.2-flash:free`; free-only consent, budget $0, catalog zero-price checks and per-request zero caps; no paid fallback |
| AI booking | User consent, live read/propose tools, map highlight, signed user-bound 10-minute proposal, separate exact confirmation; no automatic booking; AI failure leaves manual form available |
| Rate/limits | Durable 3 requests/user/minute, bounded tools/rounds/time/input, one bounded same-model 429 retry; provider capacity is not guaranteed |
| Mailpit/notifications | Live in both environments; seven legacy messages captured in each, durable Worker dedup/retry, zero pending jobs/queues. Fictional full name/address, resource/floor, Moscow interval, booking code/CTA. SMTP acceptance/commit crash duplicate window is explicit |
| CI/CD | GitHub Actions → immutable Docker Hub digests → complete isolated server regression → staging/smoke → exact production digests/HTTPS smoke → aliases/release/Allure |
| Deploy isolation | Separate `biocad-staging`/`biocad-production`; 14 own containers healthy, existing Traefik ingress; 23 unrelated containers preserved, backup/previous production v1.3.1 retained |
| Requirements/visuals | PRD v1.2 + approved DECISIONS canonical; references/static HTML are concepts, not implementation evidence; official BIOCAD UI Kit/rights not provided |

Main [workflow 43763748048](https://github.com/smalvik/biocad-workspace/actions/runs/43763748048)
passed **237 checks** (100 Booking/delivery, 24 Assistant, 20 Worker, 2 persistence,
5 outage/recovery phases, 26 Vitest and 60 Playwright); server Allure **213 raw results**
(211 regression + stage/prod smoke),
Vitest separately. CI provider is explicitly scripted; MCP/RabbitMQ/PostgreSQL real.
Original v1.3.0 production actual-free acceptance: **3 API + 2 desktop/mobile browser cases**,
all successful provider responses cost=0, no booking writes. Initial mobile provider
429 is retained separately; final sequential repeat passed without runtime/model changes.
Existing 7 bookings/12 accounts per environment and all 23 other containers preserved.
WB-07 made no new inference calls. Public application smoke 4 and report UI 4 passed;
Allure opens inline with zero downloads and retains those original live results.

Next unfinished P0: **WB-08 race/red-green evidence**, then remaining delivery docs.
P1 comfort/quiz/failover/feedback and the actual
in-product release-history page are not claimed delivered. See [backlog](../tasks/BACKLOG.md).

Browser access incident [#21](https://github.com/smalvik/biocad-workspace/issues/21)
remains monitoring: user reports access restored, current public browser checks pass;
no DNS/proxy/client route remediation was applied and the original direct/VPN cause
is not established. [Diagnosis](../evidence/WB-11-browser-access.md).

Earlier releases: [v1.0.0/WB-09](../evidence/WB-09-remote.md),
[v1.1.0/WB-04](../evidence/WB-04-remote.md), [v1.2.0/WB-05](../evidence/WB-05-remote.md).
All employee profiles/portraits/demo calendar data are fictional.
