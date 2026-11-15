# Actual implementation status — 2026-11-15

**WB-06 and WB-11 planning fix released as v1.3.0.**
Production: **https://biocad.smalvik.dev** ·
[published release](https://github.com/smalvik/biocad-workspace/releases/tag/v1.3.0) ·
[remote evidence](../evidence/WB-06-remote.md).
Main/source **19a838808e6e15d6daeb00be63688221071fb1fa**; develop **887bcc1**.
User pause was explicitly resumed; [historical handoff](PAUSE_HANDOFF.md).

| Capability | Observed state |
|---|---|
| Booking authority | Live Booking FastAPI + PostgreSQL; GiST `[start,end)`, real concurrent winner/adjacency tests, durable UTC data, authenticated fictional users, CSRF and idempotency |
| React manual flow | Two-floor SVG map, Moscow period/filtering, employee lookup, fictional portraits, selected-period occupancy/timeline; explicit confirmation, own list and cancel-own-only; retry/reload |
| Assistant | Independently deployed FastAPI; official MCP 2.3.0 STDIO tools; all Booking interservice calls via durable RabbitMQ RPC; no Assistant DB access or network HTTP to Booking |
| Real LLM | OpenRouter `inclusionai/ling-3.2-flash:free`; free-only consent, budget $0, catalog zero-price checks and per-request zero caps; no paid fallback |
| AI booking | User consent, live read/propose tools, map highlight, signed user-bound 10-minute proposal, separate exact confirmation; no automatic booking; AI failure leaves manual form available |
| Rate/limits | Durable 3 requests/user/minute, bounded tools/rounds/time/input, one bounded same-model 429 retry; provider capacity is not guaranteed |
| Mailpit/notifications | Mailpit and fictional SMTP smoke work; Notification Worker and booking event emails **not implemented (WB-07)** |
| CI/CD | GitHub Actions → immutable Docker Hub digests → complete isolated server regression → staging/smoke → exact production digests/HTTPS smoke → aliases/release/Allure |
| Deploy isolation | Separate `biocad-staging`/`biocad-production`; existing Traefik ingress; 23 unrelated containers preserved, backup/previous v1.2.0 retained |
| Requirements/visuals | PRD v1.2 + approved DECISIONS canonical; references/static HTML are concepts, not implementation evidence; official BIOCAD UI Kit/rights not provided |

Main [workflow 43737645275](https://github.com/smalvik/biocad-workspace/actions/runs/43737645275)
passed **189 checks** (79 Booking/delivery, 24 Assistant, 2 persistence, 26 Vitest
and 58 Playwright); server Allure **165** (163 regression + stage/prod smoke),
Vitest separately. CI provider is explicitly scripted; MCP/RabbitMQ/PostgreSQL real.
Independent production actual-free acceptance: **3 API + 2 desktop/mobile browser cases**,
all successful provider responses cost=0, no booking writes. Initial mobile provider
429 is retained separately; final sequential repeat passed without runtime/model changes.
Existing 7 bookings/12 accounts per environment and all 23 other containers preserved.

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
