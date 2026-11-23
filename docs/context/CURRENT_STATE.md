# Actual implementation status — 2026-11-23 (Moscow)

**WB-12 #44: feature branch tested, draft [PR #45](https://github.com/smalvik/biocad-workspace/pull/45).**
Request-local free fallback, shared attempt/time limits and React status implemented.
Local277/35exit0/raw251, focused43 passed. Real-free acceptance failed
(Docker catalog403; Nvidia/Liquid policy404; Ling/Gemma429). Gemma4 candidate only;
no server fallback enabled. SSH22 times out; prior VPN absent. No merge/release/deploy.
Production remains the published WB-18 v1.4.3 below.
[Evidence](../evidence/WB-12-local.md), [resume steps](WB-12_HANDOFF.md).

**WB-18 #41 released v1.4.3, 21 November 2026 Moscow:** 18-task/72-Q&A
guide verified against code, evidence table and safe local walkthrough. PR #42
→ develop9c30d7a, promotion #43 → main **fb0d3428e3631e94e13f3bd2c0f8ddc15c01269d**.
[Main CI/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44901696653): **248 /35exit0 /224 raw Allure**,
public app4/report4/expanded race logs2 PASS, downloads0. Original staging
7 bookings and production 9 bookings,
12 accounts per environment and 23 unrelated containers preserved;
14 own healthy. Documentation only, no new LLM calls. Separate personal-hours draft
is not verified accounting. [Actual evidence](../evidence/WB-18-remote.md).
Current P1: **WB-12 free-model failover**, draft PR, free-only/$0; other P1 scope remains TODO.

**WB-10 #38 released v1.4.2:** actual C1/C2, reviewed ADRs, reproducible README,
evidence index and concise AI-LOG; documentation only. PR #39 → develope8e29cf,
promotion #40 → main4a40e18. [Main CI/server](https://github.com/smalvik/biocad-workspace/actions/runs/43788663155)
**248 checks /35 commands exit0 /224 raw Allure PASS**. Fresh local start7 healthy,
browser smoke4 and Mermaid render3 PASS; independent public app4/report4 PASS, no downloads.
Both environments updated, original data and 23 unrelated containers preserved.
[Actual task evidence](../evidence/WB-10-remote.md). Active personal hours unmeasured.

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
[published v1.4.3](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.3) ·
[remote evidence](../evidence/WB-18-remote.md).
Production/staging source **fb0d3428e3631e94e13f3bd2c0f8ddc15c01269d**; develop **9c30d7a**.
User pause was explicitly resumed; [historical handoff](PAUSE_HANDOFF.md).

| Capability | Observed state |
|---|---|
| Booking authority | Live Booking FastAPI + PostgreSQL; GiST `[start,end)`, native conflict arbitration and bounded deadlock retry; real concurrent winner/adjacency and RED/GREEN tests, durable UTC data, authenticated fictional users, CSRF and idempotency |
| React manual flow | Two-floor SVG map, Moscow period/filtering, employee lookup, fictional portraits, selected-period occupancy/timeline; explicit confirmation, own list and cancel-own-only; retry/reload |
| Assistant | Independently deployed FastAPI; official MCP 2.3.0 STDIO tools; all Booking interservice calls via durable RabbitMQ RPC; no Assistant DB access or network HTTP to Booking |
| Real LLM | OpenRouter `inclusionai/ling-3.2-flash:free`; free-only consent, budget $0, catalog zero-price checks and per-request zero caps; no paid fallback |
| AI booking | User consent, live read/propose tools, map highlight, signed user-bound 10-minute proposal, separate exact confirmation; no automatic booking; AI failure leaves manual form available |
| Rate/limits | Durable 3 requests/user/minute, bounded tools/rounds/time/input, one bounded same-model 429 retry; provider capacity is not guaranteed |
| Mailpit/notifications | Live in both environments; actual sent/captured counts recorded in WB-18 audit, durable Worker dedup/retry, zero pending jobs/queues. Fictional notification fields only; SMTP acceptance/commit duplicate window explicit |
| CI/CD | GitHub Actions → immutable Docker Hub digests → complete isolated server regression → staging/smoke → exact production digests/HTTPS smoke → aliases/release/Allure |
| Deploy isolation | Separate `biocad-staging`/`biocad-production`; 14 own containers healthy, existing Traefik ingress; 23 unrelated containers preserved, backup/previous production v1.4.2 retained |
| Requirements/visuals | PRD v1.2 + approved DECISIONS canonical; references/static HTML are concepts, not implementation evidence; official BIOCAD UI Kit/rights not provided |

Main [workflow 44901696653](https://github.com/smalvik/biocad-workspace/actions/runs/44901696653)
passed **248 checks** (111 Booking/delivery, 24 Assistant, 20 Worker, 2 persistence,
5 outage/recovery phases, 26 Vitest and 60 Playwright); server Allure **224 raw results**
(222 regression + stage/prod smoke; UI may group history/phase identities),
Vitest separately. CI provider is explicitly scripted; MCP/RabbitMQ/PostgreSQL real.
Original v1.3.0 production actual-free acceptance: **3 API + 2 desktop/mobile browser cases**,
all successful provider responses cost=0, no booking writes. Initial mobile provider
429 is retained separately; final sequential repeat passed without runtime/model changes.
Current preservation audit: staging7/production9 original bookings,
12 accounts per environment and 23 other containers preserved.
WB-07/WB-08/WB-10/WB-18/WB-11 #34 made no new task inference calls. Current public application
smoke4, report UI4 and expanded race log UI2 passed; Allure opens inline with zero downloads and retains
those original live results. Published Booking runtime physically excludes probe/pytest.

WB-12 free-model failover is now **in progress on its feature branch**; current
production above still uses the released single-model implementation. WB-17 process notes/releases exist,
its in-product UI remains P1. This does not claim completion of the entire PRD.
P1 comfort/quiz/failover/feedback and the actual
in-product release-history page are not claimed delivered. See [backlog](../tasks/BACKLOG.md).

Browser access incident [#21](https://github.com/smalvik/biocad-workspace/issues/21)
remains monitoring: user reports access restored, current public browser checks pass;
no DNS/proxy/client route remediation was applied and the original direct/VPN cause
is not established. [Diagnosis](../evidence/WB-11-browser-access.md).

Earlier releases: [v1.0.0/WB-09](../evidence/WB-09-remote.md),
[v1.1.0/WB-04](../evidence/WB-04-remote.md), [v1.2.0/WB-05](../evidence/WB-05-remote.md).
All employee profiles/portraits/demo calendar data are fictional.
