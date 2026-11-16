# Actual implementation status — 2026-11-16 (Moscow)

**WB-08 and conditional WB-11 #34 released v1.4.1:** genuine two-process PostgreSQL
race evidence (RED 2 failed / restored GREEN 3 passed) and the discovered deadlock fix.
Separate reviewed PRs #35/#36 → develop 05e08e6, promotion #37 → main5364c9e;
[main CI/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648), **248 checks**, all 35 commands exit 0.
Both persistent environments updated; no new LLM calls or Booking migration.
[Actual delivery evidence](../evidence/WB-08-remote.md),
[actual bug history](../evidence/WB-11-booking-deadlock.md).

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
[published v1.4.1](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.1) ·
[remote evidence](../evidence/WB-08-remote.md).
Production/staging source **5364c9e05505041e0035ea1b28adef99c6f61346**; develop **05e08e6**.
User pause was explicitly resumed; [historical handoff](PAUSE_HANDOFF.md).

| Capability | Observed state |
|---|---|
| Booking authority | Live Booking FastAPI + PostgreSQL; GiST `[start,end)`, native conflict arbitration and bounded deadlock retry; real concurrent winner/adjacency and RED/GREEN tests, durable UTC data, authenticated fictional users, CSRF and idempotency |
| React manual flow | Two-floor SVG map, Moscow period/filtering, employee lookup, fictional portraits, selected-period occupancy/timeline; explicit confirmation, own list and cancel-own-only; retry/reload |
| Assistant | Independently deployed FastAPI; official MCP 2.3.0 STDIO tools; all Booking interservice calls via durable RabbitMQ RPC; no Assistant DB access or network HTTP to Booking |
| Real LLM | OpenRouter `inclusionai/ling-3.2-flash:free`; free-only consent, budget $0, catalog zero-price checks and per-request zero caps; no paid fallback |
| AI booking | User consent, live read/propose tools, map highlight, signed user-bound 10-minute proposal, separate exact confirmation; no automatic booking; AI failure leaves manual form available |
| Rate/limits | Durable 3 requests/user/minute, bounded tools/rounds/time/input, one bounded same-model 429 retry; provider capacity is not guaranteed |
| Mailpit/notifications | Live in both environments; seven legacy messages captured in each, durable Worker dedup/retry, zero pending jobs/queues. Fictional full name/address, resource/floor, Moscow interval, booking code/CTA. SMTP acceptance/commit crash duplicate window is explicit |
| CI/CD | GitHub Actions → immutable Docker Hub digests → complete isolated server regression → staging/smoke → exact production digests/HTTPS smoke → aliases/release/Allure |
| Deploy isolation | Separate `biocad-staging`/`biocad-production`; 14 own containers healthy, existing Traefik ingress; 23 unrelated containers preserved, backup/previous production v1.4.0 retained |
| Requirements/visuals | PRD v1.2 + approved DECISIONS canonical; references/static HTML are concepts, not implementation evidence; official BIOCAD UI Kit/rights not provided |

Main [workflow 43779639648](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648)
passed **248 checks** (111 Booking/delivery, 24 Assistant, 20 Worker, 2 persistence,
5 outage/recovery phases, 26 Vitest and 60 Playwright); server Allure **224 raw results**
(222 regression + stage/prod smoke; UI may group history/phase identities),
Vitest separately. CI provider is explicitly scripted; MCP/RabbitMQ/PostgreSQL real.
Original v1.3.0 production actual-free acceptance: **3 API + 2 desktop/mobile browser cases**,
all successful provider responses cost=0, no booking writes. Initial mobile provider
429 is retained separately; final sequential repeat passed without runtime/model changes.
Existing 7 bookings/12 accounts per environment and all 23 other containers preserved.
WB-07/WB-08/WB-11 #34 made no new inference calls. Public application smoke 4, report UI 4
and race log attachment UI 2 passed; Allure opens inline with zero downloads and retains
those original live results. Published Booking runtime physically excludes probe/pytest.

Next unfinished P0: **WB-10 delivery documentation** (WB-09 already shipped).
P1 comfort/quiz/failover/feedback and the actual
in-product release-history page are not claimed delivered. See [backlog](../tasks/BACKLOG.md).

Browser access incident [#21](https://github.com/smalvik/biocad-workspace/issues/21)
remains monitoring: user reports access restored, current public browser checks pass;
no DNS/proxy/client route remediation was applied and the original direct/VPN cause
is not established. [Diagnosis](../evidence/WB-11-browser-access.md).

Earlier releases: [v1.0.0/WB-09](../evidence/WB-09-remote.md),
[v1.1.0/WB-04](../evidence/WB-04-remote.md), [v1.2.0/WB-05](../evidence/WB-05-remote.md).
All employee profiles/portraits/demo calendar data are fictional.
