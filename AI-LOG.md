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
