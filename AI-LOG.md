# AI-LOG — фактическая работа Codex, 14–16 ноября 2026 (МСК)

Пользователь определял порядок задач, разрешил push/PR/merge/deploy и **только
бесплатные модели, бюджет $0**. Codex продолжил найденный каркас, реализовал код,
тесты и delivery. В PR явно записана самопроверка агента; независимое человеческое
ревью не заявляется. Точный model id агента, его стоимость и затраченные часы неизвестны.

- **WB-01/02/03:** Compose, CI/Allure; Booking/FastAPI/PostgreSQL с GiST `[start,end)`,
  демо-сессиями/CSRF, идемпотентностью и outbox; React SVG-карта. Реальные проверки
  параллельной записи и restart. Ошибка повторного HTTP-соединения аварийного outbox
  probe исправлена отдельным WB-11, а не выдана за дефект бронирования.
- **WB-09/v1.0.0:** по запросу пользователя до WB-04 настроены build-once SHA/digest
  Docker Hub, restricted SSH dispatcher, staging/production, backup/rollback и релизы.
  Реальная проверка сериализации публикации одинакового SHA после WB-11 #13.
- **WB-04/v1.1.0, WB-05/v1.2.0:** поиск сотрудников, собственные вымышленные SVG-аватары,
  таймлайн выбранного периода, отдельное подтверждение, свои брони/отмена и retry/reload.
  Соответственно 131 и 157 regression checks; реальные desktop/mobile screenshots.
- **WB-06/v1.3.0:** MCP 2.3.0 STDIO, RabbitMQ RPC, лимиты, user-bound proposal и
  явное подтверждение. Ling 3.2 Flash `:free`, catalog/zero-price caps, без paid fallback;
  CI явно scripted. Исправлены MCP schema/event loop, mobile occlusion и staging #24
  через PR #25. После пользовательской паузы и явного resume: main 43737645275 PASS,
  189 checks / server Allure 165; production real free 3 API + 2 browser PASS, cost=0,
  без booking writes. Первый mobile 429 сохранён. [Evidence](docs/evidence/WB-06-remote.md).
- **WB-09 follow-up/v1.3.1:** Nginx inline/read-only mount, атомарная публикация
  проверенного release Allure. PR #28 → fd81f82, #29 → 8d8cf08; main 43745466108 PASS,
  209 checks / server Allure 185, public HTTP + 4 report UI PASS, download=0.
  [Evidence](docs/evidence/WB-09-allure-web.md). Новых LLM-вызовов не было.
- **WB-07/v1.4.0:** outbox publisher, отдельный SQLite inbox Worker, Jinja2/Mailpit,
  девять образов/schema 2 с legacy rollback. При review добавлены ФИО/контакт помощи,
  убрана лишняя миграция. Реальный v1.3.1 upgrade/rollback/resume и повторный full 237 PASS;
  первый import-path FAIL вспомогательного probe сохранён. PR #31 → develop 82d14a4,
  #32 → main **5decd64**, main **43763748048 PASS**: 237 checks, 35 команд exit 0,
  server Allure 213. Published 15.11 21:43:49 UTC / 16.11 00:43:49 МСК.
  Public app 4/report UI 4 PASS, download=0; по 7 настоящих Mailpit писем в каждой среде,
  очереди пусты. Исходные 7 броней/12 аккаунтов на среду и 23 других контейнера сохранены;
  14 своих контейнеров healthy. SMTP ambiguous-commit window описан, exactly-once не обещан.
  Новых inference calls не было. [Evidence](docs/evidence/WB-07-remote.md).
- **WB-08 / WB-11 #34:** настоящий red/green probe обнаружил PostgreSQL deadlock
  `40P01` и HTTP 500 при сохранённом constraint. Retry-only прошёл probe, но full20
  выявил каскад deadlock; fix-ветка добавляет native ON CONFLICT и максимум три полных
  попытки с тем же ключом. Финальная локальная регрессия 240 PASS / Allure 214.
  [Реальные FAIL/PASS](docs/evidence/WB-11-booking-deadlock.md). PR #35 CI PASS, develop 75f661f.
- **WB-08 + WB-11 #34 / v1.4.1:** отдельный child DB, два HTTP-процесса, настоящий
  pytest RED 2 failed / восстановленный GREEN 3 passed, одинаковый source hash oracle,
  исходные логи/результаты в Allure. Guards/cleanup и физическое отсутствие probe/pytest
  в опубликованном runtime проверены. PR #35 → 75f661f, #36 → 05e08e6, #37 → main
  **5364c9e05505041e0035ea1b28adef99c6f61346**. Feature/post-merge/promotion/main CI PASS;
  main **43779639648 PASS**: 248 checks, 35 команд exit 0, server Allure 224 raw
  (222 regression + stage/prod smoke; Vitest отдельно). Published 16.11 **00:35:01 UTC /
  03:35:01 МСК**. Обе среды v1.4.1; public app 4/report 4/race attachments 2 PASS,
  download=0. 7 броней/12 аккаунтов на среду и 23 других контейнера сохранены,
  14 своих healthy, Mailpit 7/7 на среду. Предыдущая v1.4.0 и backup сохранены.
  Реальные первоначальные FAIL не скрыты. Новых LLM-вызовов и миграций не было.
  Итоговые docs: policy и staged secret scan (15 файлов) PASS, 147 локальных ссылок
  без пропусков, `git diff --cached --check` PASS после удаления пустой строки в конце.
  [Финальные доказательства](docs/evidence/WB-08-remote.md).

Реальные команды: `scripts/check.py --run-type regression`, pytest/Ruff/Vitest/
Playwright/Allure в Docker; `gh issue/pr/run/release`, `remote_delivery.py`,
`promote_images.py`, `publish_release.py`, `check_live_assistant.py`;
safe SSH inventory и server-only сравнение данных. Секреты в ignored env/CI Secrets,
не в Git/argv/логах; реальные персональные данные в LLM не отправлялись.
Auto-review отклонил экспорт production IDs/fingerprints; заменено сравнением
только на сервере, наружу только агрегаты. Неподтверждённые ключи не использовались.

Подробные команды, исходные FAIL и ограничения: [PROGRESS](docs/context/PROGRESS.md),
[WB-09](docs/evidence/WB-09-remote.md), [WB-04](docs/evidence/WB-04-remote.md),
[WB-05](docs/evidence/WB-05-remote.md), [WB-06](docs/evidence/WB-06-remote.md),
[WB-07](docs/evidence/WB-07-local.md), [WB-08](docs/evidence/WB-08-remote.md).
Следующая P0 — WB-10, документация поставки; остальные PRD-возможности не объявляются готовыми.
