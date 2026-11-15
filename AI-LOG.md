# AI-LOG — фактическая работа Codex, 14–15 ноября 2026

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
- **WB-06/v1.3.0:** official MCP 2.3.0 STDIO, durable RabbitMQ RPC к тем же Booking
  handlers, миграция лимитов, user-bound proposal/explicit confirm, React чат/карта.
  После согласования free-only настроены Ling 3.2 Flash `:free`, проверка catalog,
  нулевые price caps и отсутствие paid fallback. CI провайдер явно scripted;
  настоящий LLM проверяется отдельно. Исправлены ошибки MCP schema/event loop,
  mobile occlusion и реальный staging planning-round дефект #24 отдельным PR #25.
  PR #23 → c85b8dc, #25 → 887bcc1; main #26 → **19a8388**.
- Пользователь поставил работу на паузу; первый post-merge run отменён до deploy.
  После явного «продолжай» полный rerun прошёл, затем main **43737645275 PASS**:
  189 checks, 20 команд exit 0, server Allure 165. v1.3.0 опубликована 15.11 в
  17:04:06 UTC. Production real free: 3 API + 2 browser cases passed, все успешные
  ответы cost=0, без booking writes; первый mobile 429 сохранён отдельно.
  7 броней/12 аккаунтов каждого окружения и 23 других контейнера сохранены.
- **WB-09 follow-up #27:** пользователь запросил просмотр Allure в браузере.
  От develop создана `ci/wb-09-allure-web`; перенесены WB-06 evidence.
  Добавлены Nginx inline route, отдельный read-only public mount, проверяемая
  атомарная публикация из stable GitHub release и CI smoke. Локальный фактический
  download/checksum v1.3.0 прошёл; local full 209 checks / Allure 183, все команды exit 0.
  Реальный Nginx + HTTP smoke и 4 desktop/mobile report UI checks прошли без download.
  Remote CI/выкладка ещё не выполнены.

Реальные команды: `scripts/check.py --run-type regression`, pytest/Ruff/Vitest/
Playwright/Allure в Docker; `gh issue/pr/run/release`, `remote_delivery.py`,
`promote_images.py`, `publish_release.py`, `check_live_assistant.py`;
safe SSH inventory и server-only сравнение данных. Секреты в ignored env/CI Secrets,
не в Git/argv/логах; реальные персональные данные в LLM не отправлялись.
Auto-review отклонил экспорт production IDs/fingerprints; заменено сравнением
только на сервере, наружу только агрегаты. Неподтверждённые ключи не использовались.

Подробные команды, исходные FAIL и ограничения: [PROGRESS](docs/context/PROGRESS.md),
[WB-09](docs/evidence/WB-09-remote.md), [WB-04](docs/evidence/WB-04-remote.md),
[WB-05](docs/evidence/WB-05-remote.md), [WB-06](docs/evidence/WB-06-remote.md).
Следующая P0 — WB-07 Notification Worker; остальные PRD-возможности не объявляются готовыми.
