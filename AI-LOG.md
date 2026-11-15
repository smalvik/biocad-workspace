# AI-LOG — фактическая работа, 2026-11-14

Codex продолжил найденный незакоммиченный React/FastAPI-каркас на
`chore/st-00-bootstrap`; исходное авторство неизвестно. Новые изменения и тесты
ниже выполнены агентом. Пользователь задавал порядок задач и явно разрешал push
и продвижение WB-02 в develop/main. В PR отмечена самопроверка агента;
человеческое approval/ревью не заявляется. Точный model id, стоимость и часы неизвестны.

- **WB-01:** ветка от develop, Compose/PostgreSQL/RabbitMQ/Mailpit, независимые
  образы, runner/CI/Allure. Исправлены cp1251 и Erlang-cookie healthcheck race.
  17 локальных тестов; commit `bc283c7`, PR #2 -> `e5bb0b5`.
  PR CI `43598925846` и post-merge `43599195552` прошли.
- **WB-02:** Alembic/GiST `[start,end)`, signed DB sessions/CSRF/scrypt,
  UTC/idempotent create/cancel, atomic outbox, seed. Несоответствия D-07/ролей
  приведены к PRD. Commit `5f3f661`, 52 локальных теста, Allure 50; исправлены
  loop-scope/invalid-header ошибки harness. PR #4 прошёл CI `43602548303` и
  вошёл в develop `523c116`. Согласованное main-исключение записано в DECISIONS/PRD.
- **WB-11:** реальный post-merge FAIL `43602959863` — HTTPX reuse закрывающегося
  соединения после ожидаемого outbox 500, а не двойная бронь. Issue #7,
  отдельная fix-ветка, `Connection: close` только у fault probe, проверки rollback/201
  сохранены. 52 локальных теста, PR #8 (`bba451e` -> `34d4f7c`), CI `43604235478`
  и полный regression develop `43604565825` прошли. Main PR #6 -> `59e4883`,
  post-merge main `43604855360` прошёл. Ветки задач сохранены, релиз/deploy не создавался.
- **WB-03:** issue #5, отдельная ветка от develop `34d4f7c` после main promotion.
  Реализованы React SVG карта/логин/фильтры/панель, API geometry + Alembic 0002,
  два этажа/41 ресурс, request cancellation и защита от stale snapshot,
  keyboard/pan/zoom/fit, mobile bottom sheet и error/empty/retry/session states.
  Локальный regression `20261114T143322Z-c7f947`: 79 passed = 43 Booking + 2 Assistant
  + 2 persistence + 10 Vitest + 22 Playwright; Allure 69. Настоящие screenshots
  desktop/mobile просмотрены. Traces отключены для защиты cookies/CSRF.
  WB-03 пока локальна; профили/аватары и booking form оставлены WB-04/WB-05.
  Dev-стек обновлён с сохранением volume; дополнительный desktop/mobile smoke — 2 passed.
  Реализация сохранена локальным `a02a488`; SHA записан отдельным docs-коммитом той же задачи.

Ключевые решения агента: реальный PostgreSQL constraint вместо SELECT/локального
lock ([ADR-001](docs/adr/001-booking-consistency.md)); отдельный Compose-проект и
volumes для проверок; SVG из API вместо bitmap и атомарная смена calendar snapshot.
Альтернативы/ограничения и фактические evidence: [PROGRESS](docs/context/PROGRESS.md),
[WB-01](docs/changes/WB-01.md), [WB-02](docs/changes/WB-02.md),
[WB-11](docs/changes/WB-11.md), [WB-03](docs/evidence/WB-03-local.md).

Реальные команды: git status/branch/diff/commit/fetch/push; gh issue/pr/run
через Docker; uv lock/npm ci, Ruff, TypeScript/Vite/Vitest, actionlint,
`python scripts/check.py --run-type regression`, Allure CLI в Docker/Java,
локальный compose up с сохранением volumes. Секреты не коммитились/не выводились;
GitHub token читался в память и передавался через environment, не argv/URL.
Реальные персональные данные в OpenRouter не отправлялись; MCP/LLM ещё не реализованы.

- **WB-09, 2026-11-14:** по явному запросу владельца настроить delivery до WB-04.
  WB-03 опубликована, PR #9 self-reviewed и слита в develop `af00fa1`; CI
  `43608443234` и post-merge `43608755923` прошли. Новая отдельная WB-09 / issue #10.
  Реализованы manifest guards, build-once SHA/digest images, CI/staging/prod/Allure,
  ограниченный root-owned SSH dispatcher, backup и image rollback. Полный локальный
  run `20261114T153725Z-794475`: 91 passed; финальные focused delivery unit: 13 passed.
  Отдельный реальный runtime proof проверил backup, намеренно неверный web image и
  восстановление предыдущего, dev IDs не изменились. Ошибки начального pytest параметра
  и отсутствующего fault-образа зафиксированы и исправлены.
  Ключ в Cygwin home не найден; auto-review отклонил неподтверждённый другой-project key.
  Владелец затем явно предоставил root/password в `.env` и поручил создать новый ключ;
  создан BIOCAD admin key, сохранён путь, проверен вход, существующие authorized_keys
  сохранены. Отдельный restricted CI key, forced-command user и `/opt/biocad` bootstrap
  установлены. Старый Docker Hub PAT оказался expired, обновлён владельцем; новый login PASS,
  Secrets безопасно обновлены stdin. Фактически сервер Ubuntu 24.04/8 GiB/4 CPU с
  Traefik: адаптировано подключение только Web к существующему ingress. Существующие
  контейнеры/proxy не перезапускались. Первый реальный CI delivery/release ещё ожидается.

- WB-09 PR #11 passed CI and seven-image registry publication (`43612515436`,
  `43613064726`), merged develop `f3a6e8f`. Prebuilt-digest local runner also passed
  92 cases without builds (`20261114T160232Z-24d3b1`). Promotion PR #12 opened.
  Observed push run `43624173958` and PR run `43624230115` for identical source SHA;
  package jobs were not serialized across refs. Cancelled duplicate promotion run,
  created separate conditional bug issue #13 and `fix/wb-11-candidate-serialization`.
  Adds a non-cancelling source-SHA package lock; no actual corrupt/overwritten registry
  artifact or production defect is claimed. Staging flow remains independent and gated.

- **Delivery completed / WB-04 start:** #14 passed and merged `f5336c8`.
  Real push/PR publication intervals do not overlap; all seven digests identical
  (`artifacts/WB-11-serialization-proof.json`). Main #12 -> `e7ba97b`;
  workflow `43626386129` PASS, published v1.0.0, actual stage/prod HTTPS smoke,
  server Allure 84 passed + Vitest separately. Independent public desktop/mobile
  smoke 2 passed, final launcher exit 0; initial PowerShell NativeCommandError
  was Docker pull stderr transport, not failed browser cases. All 23 previous
  container IDs/start times and sample HTTP statuses preserved. Shipped issues closed.
  WB-04 issue #15, separate feature branch from develop `f5336c8`; scope employee
  lookup, safe public profiles, selected-period avatars/timeline and responsive details.

- **WB-04 local:** authenticated directory/location API, safe person projection and
  batch occupancy profiles; React lookup/floor jump, portraits/initials, full timeline,
  stale/cancel protection and responsive drawer. Created 12 original fictional SVG
  portraits by deterministic code (not real employee photos). No migration required.
  Run `20261114T193248Z-b8b531`, base `0f20a58` dirty: 131 passed, Allure 114.
  Earlier `192822Z-4a2f92` had two ambiguous E2E time selectors; narrowed to actual
  reservation region and reran the whole suite successfully. Visually inspected real
  desktop/mobile screenshots. Existing dev volume: 7 bookings before/after, account
  password rows unchanged, 12 avatar URLs refreshed; live login/asset/logout PASS.
  Generated SSH/Docker-auth directories now have restricted Windows ACLs; no key data logged.

- **WB-04 released:** final PR #16 check/publication `43634407373` PASS, merged
  develop `a00f590`; post-merge `43635049967` passed full server regression and staging
  (115 Allure, Vitest separately). Main PR #17 CI `43635067010` PASS, self-reviewed
  explicitly as agent review, merged `16826d4`. Main workflow `43636402995` PASS;
  server `20261114T201924Z-e69216`: 131 passed, all 20 commands exit 0, prebuilt
  digests, clean source. Stage/prod smoke passed; published v1.1.0 at 20:24:26 UTC,
  server Allure 116 and exact digest/release assets. Independent public HTTPS
  desktop/mobile smoke 4 passed, exit 0; no booking writes.
  Current stage/prod manifests match the released main candidate, 12 BIOCAD containers
  healthy. All 23 original container IDs/images/start times and baseline sample HTTP
  statuses preserved. Production backup file exists, previous v1.0.0 manifest retained.
  An empty local DACL from an earlier ACL edit initially blocked SSH snapshot reads;
  granted only current owner/SYSTEM/Administrators on the five newly generated BIOCAD
  key/auth files, then real snapshots succeeded. Existing keys and server SSH settings
  untouched. Actual commands and evidence: `docs/evidence/WB-04-remote.md`.
  WB-05 form/own bookings/cancel remains the next unimplemented product task.

- **WB-05 implementation, 2026-11-14/15:** issue #18, separate branch from develop
  `a00f590`, carried only post-release WB-04 documentation (`7f5e82a`). Added frozen
  explicit confirmation, CSRF/stable retry identity, persisted uncertain intent per
  demo user, request guards, own-list and confirmed idempotent cancellation.
  Own list adds safe joined resource location; no schema/write transaction changes.
  Early tests exposed incorrect dedicated test resources, persistence DTO comparison,
  HTTP-origin randomUUID unavailability, unmount focus restoration and a mobile
  M-03 hit target obscured by zoom controls. Corrected each; obsolete test run was
  intentionally aborted, failure artifacts retained. getRandomValues choice checked
  against https://w3c.github.io/webcrypto/#crypto-interface and actual browser probe.
  Existing dev upgrade preserved all seven booking records and account password rows;
  live own-list/login/logout passed. Independent local form preview/own-list on
  desktop/mobile passed with zero attempted booking writes. Final full regression
  and remote delivery are pending; production remains v1.1.0.

- **WB-05 local verified:** `20261114T210618Z-566c12`, base `7f5e82a` dirty,
  full runner exit 0, every command exit 0. 157 passed: 76 Booking/delivery,
  2 Assistant, 2 persistence, 25 Vitest, 52 Playwright; Allure 132.
  Actual desktop confirmation and mobile M-03 cancellation screenshots inspected.
  Existing-volume upgrade repeated after the map change: 7 complete booking records
  and account password rows unchanged, live own-list/login/logout passed.
  Command: `python artifacts/run_logged.py artifacts/WB-05-regression-complete.log python scripts/check.py --run-type regression`.
  Local HTML tooling initially lacked npx; separate ignored Node/Java/Allure image
  prepared. This did not change test results or runtime images. Remote delivery pending.
  Implementation committed as `7a28ec836562133ea8b540744858e99ed4b77fac`.
  Final standalone Allure generation with `biocad-allure:local` exited 0.

- **WB-05 released, 2026-11-15:** final feature head `6554fc4`, PR #19 checks and
  publication `43641919071` PASS; merged develop `b98a9a3`. Post-merge
  `43642523912` PASS, server `20261114T212803Z-2b10a1` clean, Allure 133.
  Artifact first download had transport unexpected EOF; fresh-directory retry succeeded.
  Main PR #20 CI/publication `43642562977` PASS, explicitly agent self-reviewed,
  merged `bddba67` after green server staging. Main `43690831879` all jobs PASS;
  server `20261115T074307Z-84214e` clean: 157 regression cases, all 20 commands exit 0,
  Allure 134 plus Vitest 25 separately. Published real v1.2.0 at 07:49:07 UTC / 10:49:07 MSK.
  Both environments match the full main digest manifest, 12 BIOCAD containers healthy;
  production backup 23,877 bytes and previous v1.1.0 retained. Fresh pre-main inventory
  and original WB-09 inventory both confirm all 23 unrelated container IDs/images/start
  timestamps unchanged, sample HTTP statuses preserved.
  Initial external browser/host TLS connections timed out (browser 3 failed / 1 passed,
  preview exit 1); preserved failure artifacts, inspected DNS/TCP/TLS and server listeners
  read-only. Subsequent strict TLS probe returned 200 with expected source/version.
  No server/runtime/network configuration changed during diagnosis. Final sequential
  HTTPS browser repeats: 4 Playwright passed, plus 2 form/list previews passed,
  both launchers exit 0, zero attempted booking writes in preview. Root cause of the
  transient TLS timeouts is not asserted. Real release notes enhanced with delivered
  capabilities; actual commands and links in `docs/evidence/WB-05-remote.md`.
  Next unimplemented task: WB-06 real Assistant/MCP/LLM; SMTP worker remains WB-07.

- **WB-11 access incident #21:** user reported ERR_CONNECTION_RESET after v1.2.0.
  Reproduced direct TCP success followed by TLS timeout, including another host name
  on the same IP; SSH banner succeeds but key exchange EOFs/times out. Read-only
  routing inspection showed active AmneziaVPN with the server IP taking Wi-Fi.
  A simultaneous strict-TLS comparison to the same endpoint failed direct and passed
  via per-socket VPN selection in 0.78 s (200 / bddba67 / 1.2.0). VPN-routed SSH retained
  original host-key pinning and dedicated admin key; server read-only health check
  showed 200 and no sampled resource exhaustion. Ephemeral loopback-only single-site
  CONNECT relay kept TLS end to end; actual browser form/list preview passed on
  desktop/mobile, exit 0, zero attempted booking writes. Diagnostic relay stopped
  after verification. No global client route/browser setting or server/DNS changed.
  Created separate branch from develop and carried WB-05 evidence (dc8bd17).
  Exact direct-path cause is not asserted. User now requests requirements for a separate
  public HTTPS ingress; resource/provider/DNS access is still missing. Issue remains open,
  no fix/release claimed. Evidence: docs/evidence/WB-11-browser-access.md.

- **WB-06 started, issue #22:** user reports the site opens again and requests the
  next planned task; alternate ingress is deferred, incident #21 remains monitoring.
  Created `feat/wb-06-assistant-mcp` from develop b98a9a3, carried post-release and
  incident evidence as 2c2e6f7 / 04a0da2. Read task/PRD/UI/process; no subagents used.
  Added Booking RabbitMQ RPC reusing in-process authenticated handlers, additive
  migration 0003 for durable rate/budget limits, official mcp==2.3.0 STDIO discovery
  and read/propose tools, bounded OpenRouter tool-calling client, signed user-bound
  proposal/explicit confirmation/replay and React chat/map integration. Real MCP
  rejects plain dict structured output; corrected annotations to dict[str, Any]
  and explicit structured_output=True after inspecting installed SDK and actual calls.
  First `python scripts/check.py --run-type regression` failed MCP output / test
  event-loop scope. Second: backend 78, Assistant 13, persistence 2, Vitest 26 passed;
  Playwright 57 passed / 1 mobile button occlusion failure. Corrected AI selection
  to use its own proposal card while retaining map highlight. Third run
  20261115T112714Z-54bd2c passed 179 checks (78 + 15 + 2 + 26 + 58), exit 0;
  latest expanded cross-user/conflict/tool checks are still running. No fabricated
  live-model pass: regression uses a labelled scripted HTTP provider with real
  PostgreSQL/RabbitMQ/STDIO MCP. Read-only provider key validation succeeded,
  `inference_requests_made=0`; pending async question asks model/spending limit.
  Ruff and TypeScript/Vitest executed in local containers. Removed only accidental
  formatter changes to unrelated scripts/verify_handoff.py; no unrelated work kept.
  No server/DNS/proxy change, paid inference, WB-06 deploy or release yet.
  Expanded full run 20261115T113244Z-e7d765 passed **180** checks / Allure **154**,
  all 20 commands exit 0. Generated standalone Allure with biocad-allure:local.
  Final review tightened known-key/explicit-ISO validation and hidden error inputs;
  mounted current-source Assistant unit tests passed **11**, exit 0. Evidence
  explicitly distinguishes the dirty full run from later review changes; final
  committed CI is still required. See docs/evidence/WB-06-local.md.
  Implementation 89ad3d5 pushed, draft PR #23 opened. Actual run 43710246930 check
  job succeeded; immutable publication is still in progress at this entry. Prepared
  proposal-only live acceptance CLI with an explicit paid-call flag; its no-flag
  refusal and Ruff were checked. No paid/live invocation occurred. PR remains draft
  until real model/budget choice and live proof; no server deployment/merge claimed.
  Run 43710246930 then completed **success**: clean committed 89ad3d5 passed
  181 checks (78 + 17 + 2 + 26 + 58), Allure 155; all seven immutable candidates
  published. Staging/production job skipped for draft feature PR, as intended.
  Checked live acceptance CLI guard (refuses before any request without paid flag)
  and Ruff; actual live acceptance still not executed.
  User then explicitly selected **only a free model**. Added fail-closed :free
  settings/catalog checks and zero provider price caps; no paid route/fallback.
  Runtime Booking rejects paid reservations but allows zero-price calls under the
  durable user rate limit with budget 0. Free Gemma probe returned 429; Ling 3.2
  Flash free returned tool calls and cost 0. First end-to-end live run failed on
  provider 429; retained evidence, diagnosed safely in an isolated test process.
  Added one bounded same-model retry respecting short Retry-After, enum clarification
  schema and model/provider/cost metadata. Current Assistant unit 17 passed.
  Full local free regression 20261115T130029Z-ef921e passed 186 checks / Allure 160.
  Real live run 20261115T131327Z-20b777 passed 3 scenarios, 8 successful model
  responses all cost=0, zero booking writes; source base 01c0bf5 / dirty recorded.
  Read-only server baseline captured; no server runtime change at this point.
  WB-06 final PR CI 43718787030 passed 188 checks / Allure 162 and publication.
  PR #23 merged develop c85b8dc; post-merge/server/staging run 43719293194 succeeded,
  server run 20261115T133603Z-d1c880 passed including 58 browser cases. Refreshed only
  root-owned BIOCAD tooling and free-model config with budget 0; original DB/session/
  broker/demo credentials preserved, no proxy/DNS/other-app change. Automatic review
  rejected exporting production row IDs/digests to the workstation; no rejected command
  executed. Replaced with server-only 0600 preservation snapshot in existing BIOCAD
  backup area and exported only counts (7 bookings / 12 accounts per environment).
  Real staging live run 20261115T134519Z-84d1f2: room passed, near-Anna failed because
  repeated employee searches used the 4 model rounds before proposal. Costs stayed 0,
  no booking writes. Preserved failure, created issue #24 and separate fix branch
  from develop. Deterministic rechecked MCP proposal after availability, temperature 0
  and clearer search/clarification instructions; added exact final-round regression.
  Full local regression is now running. Main promotion/release remains pending.
  WB-11 planning local run 20261115T135319Z-f781d9 completed **189 passed**,
  Allure 163, all commands exit 0. Real free run 20261115T135746Z-0e5c21 passed
  all 3 cases using exactly 4 successful provider responses, all cost=0 and
  no booking writes. Recorded base c85b8dc/dirty; final-head CI remains required.
