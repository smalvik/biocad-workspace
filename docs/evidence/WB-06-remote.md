# WB-06 / WB-11 — actual remote delivery, 2026-11-15

Released **[v1.3.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.3.0)**
at **17:04:06 UTC / 20:04:06 MSK**. Application: **https://biocad.smalvik.dev**.
Only fictional demo profiles are used; user authorization is **free models only / $0**.

## Reviewed source and promotion

- WB-06 issue [#22](https://github.com/smalvik/biocad-workspace/issues/22), feature
  [PR #23](https://github.com/smalvik/biocad-workspace/pull/23), final source
  `49389daa0339ac2a4d10f32f34cae0599292d046`; merged develop
  `c85b8dc8beb0e97197d2bf8b9dfd3c7a9cdda7ba`.
  [Feature CI](https://github.com/smalvik/biocad-workspace/actions/runs/43718787030)
  and [develop/server](https://github.com/smalvik/biocad-workspace/actions/runs/43719293194) passed.
- Real staging exposed a planning-round defect: room lookup passed, near-Anna
  exhausted four model rounds before signing a proposal. Failed live evidence
  `20261115T134519Z-84d1f2` is retained; cost stayed zero, no booking writes.
- Separate WB-11 issue [#24](https://github.com/smalvik/biocad-workspace/issues/24),
  [fix PR #25](https://github.com/smalvik/biocad-workspace/pull/25), source
  `993ddbed4f73b1c80e3ca2674dbdc966862c6b05`, merged develop
  `887bcc18f430974fc7231ed6726a1cd037df0de1` after
  [PR CI](https://github.com/smalvik/biocad-workspace/actions/runs/43722095606).
  After validated/ranked availability, the controller immediately invokes real MCP
  `propose_booking` to recheck/sign the first candidate, preserving the tool bound
  and explicit confirmation. A regression reproduces availability on the final round.
- User pause intentionally cancelled attempt 1 of
  [43722878517](https://github.com/smalvik/biocad-workspace/actions/runs/43722878517).
  On explicit resume, full attempt 2 passed CI/publication/server/staging;
  clean run `20261115T163354Z-8c1a5c`, Allure **164** (163 regression + staging smoke).
  Real staging `20261115T164200Z-d5a377` then passed **3 cases / 4 provider responses**,
  all `cost=0`, source exactly `887bcc1`, no booking writes.
- [Main PR #26](https://github.com/smalvik/biocad-workspace/pull/26) passed
  [checks/publication](https://github.com/smalvik/biocad-workspace/actions/runs/43737134497)
  and merged **19a838808e6e15d6daeb00be63688221071fb1fa**.
  Reviews explicitly identify agent self-review; independent human approval is not claimed.

## Exact main images and server regression

[Main workflow 43737645275](https://github.com/smalvik/biocad-workspace/actions/runs/43737645275)
completed **success**, including all checks, immutable candidate publication,
full server regression, staging, production HTTPS smoke, digest alias verification
and published release/Allure. Images are promoted by digest without rebuilding.

- Clean server run **20261115T165547Z-600564**, exact main SHA above;
  **189 passed** = 79 Booking/delivery + 24 Assistant + 2 persistence + 26 Vitest
  + 58 desktop/mobile Playwright. All **20 commands exited 0**.
- **165 passed Allure results** = 163 regression + stage/prod smoke;
  Vitest 26 is counted separately. Deterministic CI uses a labelled scripted HTTP
  provider with real PostgreSQL, RabbitMQ and official STDIO MCP; it is distinct
  from actual LLM acceptance below.
- [Standalone server Allure](https://github.com/smalvik/biocad-workspace/releases/download/v1.3.0/index.html),
  [published seven-image manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.3.0/candidate.json),
  [downloaded server artifacts](../../artifacts/WB-06-main-delivery/).
- Persistent staging and production `current.json` equal the complete main candidate;
  all **12 BIOCAD containers running/healthy**. Production previous manifest **v1.2.0**
  retained; backup **20261115T170248-9f3978.dump**, **24,577 bytes**.
  [Safe state metadata](../../artifacts/WB-06-server-state.json).

## Actual free-model production acceptance

Real OpenRouter model **`inclusionai/ling-3.2-flash:free`**, provider Ant Digital;
fresh catalog price checks and per-request zero price caps, no paid fallback.
Runtime budget is **0 USD**, rate limit 3 requests/user/minute.

- Production HTTPS run **20261115T170352Z-c40544**, clean exact main SHA:
  **3 cases passed** — room for six (M-01), FreeDesk near fictional Anna (D-13),
  clarification of missing date/time. **4 real provider responses, every cost=0**.
  Same selected period, real MCP → RabbitMQ → Booking/PostgreSQL.
  **0 attempted booking writes**; this probe never confirms/cancels a booking.
  [Sanitized metadata](../../artifacts/WB-06-server-production-WB-06-live-20261115T170352Z-c40544/run.json),
  [actual command log](../../artifacts/WB-06-production-free-live.log).
- Independent public HTTPS browser acceptance, exact published E2E image/source:
  **2 passed, launcher exit 0** — desktop and Pixel 7/mobile; real free proposal,
  map highlight and exact confirmation screen. **2 provider responses, cost=0**,
  **0 attempted booking writes**, all booking/assistant-confirm POST routes blocked
  by the probe. [Final metadata](../../artifacts/WB-06-production-free-browser/run.json),
  [log](../../artifacts/WB-06-production-free-browser.log),
  [desktop confirmation](../../artifacts/WB-06-production-free-browser/confirmation-desktop.png),
  [mobile confirmation](../../artifacts/WB-06-production-free-browser/confirmation-mobile.png).
- First browser execution: desktop passed, mobile received provider **429**;
  UI displayed “Бесплатная модель занята. Повторите позже или используйте форму.”
  [Initial failure retained](../../artifacts/WB-06-production-free-browser-initial/run.json).
  The final independent repeat used a one-minute interval between device requests
  and passed without model/runtime/network changes. The first attempt is not counted green.
- Separate **actual-provider Allure: 5 passed** = 3 API + 2 browser; **6 successful
  model responses, total cost 0**, source exactly main. This does not reuse scripted
  regression results. [Standalone live LLM report](https://github.com/smalvik/biocad-workspace/releases/download/v1.3.0/live-llm-allure.html),
  [published sanitized acceptance](https://github.com/smalvik/biocad-workspace/releases/download/v1.3.0/live-llm-acceptance.json).

## Preservation and limits

- All **23 unrelated containers** retain IDs/images/start times/restart counts
  against both the initial WB-06 and fresh resume baselines. Sample HTTP statuses
  unchanged; baseline already contained URLError/401/404, so unrelated URL health
  is not claimed. [Comparison](../../artifacts/WB-06-server-preservation-proof.json).
- Each persistent environment retains **7 bookings / 12 accounts**, full original
  record fingerprints unchanged. Fingerprints/IDs remain only in root-owned mode-0600
  server backup files; only aggregate counts/changed counts were exported.
  [Aggregate verification](../../artifacts/WB-06-final-data-summary.json).
- Free providers can return 429/unavailability; one bounded same-model retry,
  then a clear failure and working manual form. Paid failover is disabled.
- AI only proposes; exact resource/date/time must be confirmed separately.
  Notifications/SMTP worker remain **WB-07**, not delivered by this release.

Actual commands: `gh run rerun/watch/view/download`, `gh pr create/review/merge`,
`remote_delivery.py stage/production/report`, `promote_images.py`, `publish_release.py`;
`python artifacts/wb06_free_server.py live staging|production EXPECTED_SHA`;
`python artifacts/wb06_production_browser.py`, `wb06_combine_live_evidence.py`,
Allure CLI in `biocad-allure:local` and `gh release upload/edit`;
server-only preservation comparison and safe container inventory through
`server_ops.py run-script`; `wb06_final_preservation.py`.
Local implementation/failure history: [WB-06](WB-06-local.md), [WB-11 notes](../changes/WB-11.md).
