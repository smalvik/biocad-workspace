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
