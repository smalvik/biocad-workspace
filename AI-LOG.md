# AI-LOG — работа 14–16 ноября; продолжение 21 и 23 ноября 2026 (МСК)

Пользователь задавал приоритеты, предоставил доступы в ignored env, разрешил
push/PR/merge/deploy, выбрал **только бесплатную модель / бюджет $0** и сообщил,
что браузерный доступ восстановился. Codex подготовил код, тесты, документы и
выполнил зафиксированные проверки. Личные code review/тесты пользователя не
подтверждены. Review в PR — явная самопроверка агента, не независимое human approval.
Активные часы разработчика/агента не измерялись; календарные даты их не заменяют.
Точная модель/стоимость агента неизвестны. Не заявляем сэкономленные часы.

23 ноября начата WB-12 #44, отдельная `feat/wb-12-llm-failover` от develop;
финальные доказательства WB-18 перенесены commit1219797. Агент реализовал ограниченное
переключение между явно настроенными free-моделями, свежую проверку каталога,
общие лимиты и статусы React. Только бесплатные модели/$0; paid fallback исключён.
Реально выполнены сборка React и 43 unit-теста Assistant, PASS. Полная локальная
регрессия 20261123T075832Z-5fd8c1: **277 проверок /35 команд exit0 /251 raw Allure**,
включая настоящие MCP/RabbitMQ/PostgreSQL и desktop/mobile. Тест общего лимита
усилен после полного прогона, 43 unit повторно PASS. Реальная приёмка не пройдена:
Docker catalog403; Nvidia/Liquid отвергнуты по policy404; Ling/Gemma вернули429.
Gemma4 оставлена кандидатом без включения на сервере. Политика данных не ослаблена;
платные модели/кредиты не использованы, успешная inference/cost0 не выдумана.
Кодcommit19313a4 запушен, создан draft [PR #45](https://github.com/smalvik/biocad-workspace/pull/45)
в develop; CI проверяется отдельно, слияния/выпуска/деплоя WB-12 нет.
Staged secret scan25/path170/policy/whitespace PASS. SSH22 недоступен с Windows/Docker,
HTTPS443 доступен; прежний VPN отсутствует, пользователю отправлен запрос маршрута.
Первый Ruff check обнаружил порядок импортов; исправление и повторный check успешны.
Команды: Docker Compose build assistant-tests/web-tests; Docker ruff check/format;
pytest tests/unit. [Область и решение](docs/adr/003-free-model-failover.md).

| Конкретное решение | Инициатор / изменение | Фактическая проверка и след |
|---|---|---|
| Booking + PostgreSQL — единственный владелец записи; GiST `[start,end)` и idempotency | PRD/пользователь; агент реализовал. WB-08 обнаружил реальный 40P01/500; retry-only не выдержал full20, агент изменил решение на native ON CONFLICT + bounded residual retry | [ADR-001](docs/adr/001-booking-consistency.md), [исходные FAIL/PASS](docs/evidence/WB-11-booking-deadlock.md), [PR #35](https://github.com/smalvik/biocad-workspace/pull/35), [неизменный oracle RED/GREEN](docs/evidence/WB-08-remote.md) |
| Модель только предлагает; read/propose через настоящий MCP STDIO/RabbitMQ; отдельное подтверждение | PRD/пользователь; agent выбрал free Ling после реального Gemma 429. Пользователь ограничил деньги $0, платный fallback исключён; planning limit исправлен отдельным PR | [protocol/code refs](docs/architecture/ASSISTANT.md), [PR #25](https://github.com/smalvik/biocad-workspace/pull/25), [real-free 3 API + 2 browser cost=0](docs/evidence/WB-06-remote.md); initial mobile 429 сохранён |
| Изоляция delivery и честные гарантии уведомлений | Пользователь потребовал сохранить чужие приложения; agent адаптировал deployment к существующему Traefik, отдельным projects и restricted SSH. При review убрал лишнюю миграцию; SQLite inbox отделён от Booking DB, SMTP exactly-once не обещан | [ADR-002](docs/adr/002-broker-and-outbox.md), [PR #31](https://github.com/smalvik/biocad-workspace/pull/31), [реальный rollback/recovery](docs/evidence/WB-07-local.md), [23 чужих контейнера и данные сохранены](docs/evidence/WB-08-remote.md) |

Разногласие по доступу: auto-review отклонил экспорт production IDs/fingerprints;
agent заменил его серверным root-only сравнением и экспортом только агрегатов.
Пользователь не заявлял проверку изменённого кода; автоматические результаты не
выдаются за неё. Секреты не помещались в Git/argv/публичные логи; персональные
данные в LLM не отправлялись. Новых LLM calls после v1.3.0 для WB-07/08/10 не требуется.

WB-10 v1.4.2: C1/C2/README/ADR/evidence; [проверки/доставка](docs/evidence/WB-10-remote.md).
WB-18 продолжен **21 ноября**, issue #41: сохранены исходные черновики, 18/72
сверены с кодом, исправлены speculative ACL/types/trace/SMTP/deploy и walkthrough.
PR#42 → develop9c30d7a, promotion#43 → mainfb0d342.
[Main CI/server 44901696653 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44901696653):
248 checks /35 commands exit0 /224 raw Allure. Public app4/report4/race logs2 PASS,
downloads0; исходные данные и 23 чужих контейнера сохранены.
[Полное evidence](docs/evidence/WB-18-remote.md). Runtime/schema не менялись, новых
LLM calls нет. Main1 отказал на RAM preflight; только private staging временно
остановлен, delivery2 с тем же candidate прошёл и восстановил staging, порог сохранён.
По просьбе пользователя отдельно создан игнорируемый иллюстративный
черновик часов для его проверки; он не опубликован и не стал фактическим учётом.
Остальные P1/P2 и весь PRD не объявляются готовыми; следующий P1 — WB-12 free-only.
