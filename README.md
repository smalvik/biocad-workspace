# BIOCAD Workspace Booking

Рабочее демо бронирования мест и переговорных: React, независимые Python FastAPI
Booking/Assistant, PostgreSQL, RabbitMQ, Notification Worker и Mailpit.
Booking Service и PostgreSQL — единственный источник подтверждённых броней.

**[Открыть приложение](https://biocad.smalvik.dev)** ·
[Репозиторий](https://github.com/smalvik/biocad-workspace) ·
[Опубликованный v1.4.3](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.3) ·
[Allure в браузере](https://biocad.smalvik.dev/allure/)

Вымышленные демо-пользователи: **e01 … e12**, пароль **demo-workspace**.
Официальный BIOCAD UI Kit и права на фотографии не предоставлены; цвета приближённые,
аватары — собственные иллюстрации. Лица обозначают закрепление или бронь на выбранный
период, а не физическое присутствие.

## Запуск локально

Нужны Docker с Linux containers и Docker Compose **2.24.4+**, свободные порты из
таблицы ниже. Node, uv и Python на хосте для самого приложения не требуются.
Из корня клонированного репозитория выполните одну команду:

```powershell
docker compose --env-file .env.example -f infra/compose.yaml up -d --build --wait
```

Compose собирает приложение, ожидает healthchecks и создаёт persistent volumes.
Booking при старте выполняет Alembic `upgrade head`, затем идемпотентный fictional seed:
два этажа, минимум 12 сотрудников, места и демонстрационные брони. Повторный seed
обновляет геометрию, сохраняя брони, аккаунты и пароли. Фиксированные примеры D-03:
16.11.2026 МСК 10–12 Мария, 12–14 свободно, 14–16 Павел; для новой брони выберите
будущую дату относительно времени сервера. D-07 закреплён за Анной и не бронируется.

| Адрес на этом компьютере | Назначение | Env для смены порта |
|---|---|---|
| http://localhost:8080 | React и проксирование API | `WEB_HOST_PORT` |
| http://localhost:8080/api/docs | Booking Swagger | Через Web |
| http://localhost:8080/api/v1/assistant/docs | Assistant Swagger | Через Web |
| http://localhost:8025 | Mailpit: демонстрационные письма | `MAILPIT_HOST_PORT` |
| http://localhost:8000/healthz | Booking напрямую | `BOOKING_HOST_PORT` |
| http://localhost:8001/healthz | Assistant напрямую | `ASSISTANT_HOST_PORT` |
| localhost:55432 | PostgreSQL для локальной разработки | `POSTGRES_HOST_PORT` |

Все host-порты привязаны к `127.0.0.1`. RabbitMQ доступен внутри Compose-сети.
`/api/v1/healthz` — процесс Booking; `/api/v1/readyz` — доступность PostgreSQL.
Assistant healthcheck проверяет процесс, а не способность внешнего LLM ответить.
Worker имеет собственный heartbeat/storage healthcheck.

Остановка с сохранением данных:

```powershell
docker compose --env-file .env.example -f infra/compose.yaml down
```

Для собственных настроек скопируйте `.env.example` в игнорируемый `.env` и замените
`--env-file .env.example` на `--env-file .env`. Пример и локальные fallback-пароли
подходят только для демо. Изменение env-пароля PostgreSQL не меняет пароль роли
в уже существующем volume; повторный seed также не сбрасывает пароль пользователя.
Перечень env-имён и значений по умолчанию: [.env.example](.env.example),
[local Compose](infra/compose.yaml). Настоящие значения не помещайте в Git или чат.

## Что работает и как проверить

1. Войдите как e01, выберите этаж, будущую дату и интервал МСК. Карта показывает
   постоянные места, свободные/занятые FreeDesk и переговорные. Поиск сотрудника
   выбирает его закрепление/бронь для выбранного времени; несколько броней дают
   счётчик и полный таймлайн, а не одного «владельца» на всё окно.
2. Выберите свободный ресурс → «Продолжить» → проверьте точный ресурс/время →
   «Подтвердить бронирование». До подтверждения записи нет. В «Мои бронирования»
   можно отменить свою бронь; повтор операции сохраняет тот же idempotency key.
3. Откройте Mailpit: создание/отмена проходят через PostgreSQL outbox → RabbitMQ →
   отдельный Worker → HTML/text SMTP. Отказ брокера/почты не откатывает бронь.
4. Для AI настройте серверный ключ по инструкции ниже. Чат читает актуальные данные
   через MCP и RabbitMQ и предлагает вариант. Отдельное точное подтверждение вызывает
   Booking; модель не имеет инструмента записи. При отказе AI ручная форма доступна.

GiST exclusion защищает `[start,end)` в БД, смежные интервалы разрешены. Даты хранятся
как aware UTC, UI показывает Europe/Moscow. Повтор того же ключа/payload возвращает
ту же бронь, изменённый payload или пересечение — 409. После исчерпания ограниченных
повторов deadlock возвращается 503 `BOOKING_RETRY`; повторите с прежним ключом.
Отмена чужой брони запрещена. [Код и доказательства](docs/architecture/EVIDENCE.md).

## Реальный AI и границы расходов

Без ключа OpenRouter приложение и ручная форма работают, AI вернёт понятную ошибку.
В ignored `.env` задайте серверные `OPENROUTER_API_KEY`, `OPENROUTER_PRIMARY_MODEL`,
`ASSISTANT_PROPOSAL_SECRET`, `ASSISTANT_FREE_ONLY` и `ASSISTANT_BUDGET_USD`.
Настроенная модель — **inclusionai/ling-3.2-flash:free**; допускаются только проверенные
бесплатные `:free`. Обязательны **ASSISTANT_FREE_ONLY=true**, **ASSISTANT_BUDGET_USD=0**;
отдельный signing secret вне local — не менее 32 символов.
Платный fallback и покупка кредитов не разрешены.

Каждый чат проверяет актуальный каталог и нулевые цены; каждый provider request имеет
нулевые price caps. Бесплатная модель может быть недоступна или вернуть 429; гарантии
capacity нет. Лимит — 3 запроса/пользователь/минуту, до 4 model rounds/8 tools и 60 секунд.
В браузере требуется согласие; в LLM отправляются текст и минимальные вымышленные
данные, без cookies/ключей. [MCP/RPC, токены предложений и настройки](docs/architecture/ASSISTANT.md).

## Тесты и настоящие отчёты

Для runner нужен Python **3.12+** и Docker; npm/pytest/Playwright исполняются в образах.

```powershell
python scripts/check.py --run-type smoke
python scripts/check.py --run-type regression
python scripts/check_policy.py
```

Оба режима сейчас запускают полный доступный набор; `run-type` меняет Allure metadata,
а не объём проверок. Runner не читает локальный `.env`, создаёт уникальный Compose-проект
без host-портов и удаляет только свои контейнеры/volumes. PostgreSQL, RabbitMQ, MCP
и Mailpit настоящие; **LLM в CI явно scripted**, платных/реальных provider calls нет.
Получаем Ruff, TypeScript/build, pytest, Vitest, desktop/mobile Playwright, проверку
перезапуска/сохранности и настоящие broker/SMTP outage/recovery. Authenticated traces отключены.

Результаты сохраняются в ignored `artifacts/<UTC-run-id>/`: `run.json`, `commands.log`,
`allure-results`, `test-results`, `playwright-report`. SHA и `working_tree=dirty|clean`
описывают фактический snapshot. Actions генерирует HTML и прикрепляет artifacts;
просто наличие файлов не означает PASS.

- [v1.4.3 regression Allure](https://biocad.smalvik.dev/allure/v1.4.3/), просмотр inline.
- [Исторический реальный бесплатный LLM smoke](https://biocad.smalvik.dev/allure/v1.3.0/live/):
  3 API + 2 browser cases, cost=0, без booking writes. Это отдельное live-доказательство.
- [Полный CI/CD v1.4.3 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/44901696653):
  248 regression checks, 35 команд exit 0; server 224 raw Allure (222 + stage/prod 2,
  Vitest отдельно). UI Allure может группировать phase/history.
- [Подлинный RED](docs/evidence/concurrency-red.md) / [GREEN](docs/evidence/concurrency-green.md):
  две реальные HTTP-службы и disposable child DB. С отсутствующим constraint —
  2 настоящих падения, с восстановленным — 3 passed. В отчёте: Behaviors →
  race-red-green → Race sensitivity → `red.log` / `green.log`.
  Мутация запрещена для persistent БД, probe/pytest отсутствуют в runtime-образе.
- [Доставка WB-08 и сохранность данных](docs/evidence/WB-08-remote.md),
  [WB-10: воспроизводимость и финальная доставка](docs/evidence/WB-10-remote.md).

## Архитектура, решения и API

- [C1: контекст и внешние системы](docs/architecture/C1.md).
- [C2: контейнеры, протоколы и владение данными](docs/architecture/C2.md).
- [ADR-001: PostgreSQL, GiST, идемпотентность и deadlock](docs/adr/001-booking-consistency.md).
- [ADR-002: RabbitMQ, outbox и отдельный notification inbox](docs/adr/002-broker-and-outbox.md).
- [Evidence index: требование → код → тест → отчёт](docs/architecture/EVIDENCE.md).

REST использует префикс `/api/v1`: auth `/auth/login`, `/auth/me`, `/auth/logout`;
карта `/floors`, `/spaces?floor_id&from&to`, `/employees?q=&from=&to=`;
брони `/bookings`, `/bookings/me`, `/bookings/{id}/cancel`. Swagger выше — точный контракт.
Запись требует session cookie, `X-CSRF-Token` и для создания `Idempotency-Key`;
владелец берётся из сессии. Передавайте ISO 8601 с offset. HTTP 401 — нет сессии,
403 — CSRF/чужая отмена, 409 — конфликт, 422 — некорректный или прошлый интервал.
Точный RabbitMQ envelope/operation allowlist — в [Assistant protocol](docs/architecture/ASSISTANT.md).

## Staging, production и образы

[CI/CD runbook](docs/process/DELIVERY.md) описывает реальные команды и bootstrap.
Feature issue → отдельная ветка → локальные проверки → reviewed PR в develop →
полная regression/server/staging smoke → promotion PR в main → полный main/server
gate → те же immutable digests в production → HTTPS smoke → version/latest/release/Allure.
Review в текущих PR — явная самопроверка агента; независимое человеческое approval не заявлено.

На общем сервере два отдельных Compose-проекта: `biocad-staging`, `biocad-production`.
Только production Web присоединён к существующему Traefik ingress; API/БД/broker/Mailpit
внутренние. Порты стендов — loopback 18081/18080. Внешний Mailpit route отсутствует.
Ограниченный SSH dispatcher не даёт произвольный shell. Перед обновлением — проверенный
`pg_dump`; image rollback использует предыдущий manifest и повторяет smoke. **Восстановление
БД не автоматическое**: оно может потерять новые брони. Не выполняйте host-wide prune,
удаление volume или перезапуск чужого proxy/daemon.

| Runtime repository | Отдельный test image |
|---|---|
| [smalvik/biocad-web](https://hub.docker.com/r/smalvik/biocad-web) | [web-tests](https://hub.docker.com/r/smalvik/biocad-web-tests) |
| [smalvik/biocad-booking](https://hub.docker.com/r/smalvik/biocad-booking) | [booking-tests](https://hub.docker.com/r/smalvik/biocad-booking-tests) |
| [smalvik/biocad-assistant](https://hub.docker.com/r/smalvik/biocad-assistant) | [assistant-tests](https://hub.docker.com/r/smalvik/biocad-assistant-tests) |
| [smalvik/biocad-notification](https://hub.docker.com/r/smalvik/biocad-notification) | [notification-tests](https://hub.docker.com/r/smalvik/biocad-notification-tests) |
| — | [e2e](https://hub.docker.com/r/smalvik/biocad-e2e) |

Девять образов/schema 2, четыре runtime. `sha-<40-character-SHA>` — candidate,
`v1.MINOR.PATCH` и `latest` — aliases после успешной доставки. Для воспроизведения
используйте [опубликованный точный manifest v1.4.3](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.3/candidate.json),
а не подвижный latest. Один SHA собирается один раз; staging → production без rebuild.

## Объём, долги и время

Реализованы карта, поиск/аватары по выбранному времени, ручная форма/свои брони/отмена,
AI read/propose/confirm, уведомления, защита БД, CI/CD и Allure. Это incremental demo,
не утверждение о завершении всего PRD. Нет настоящего SSO/HR/CAD, HA-кластера или
внешнего SMTP. Отложены model failover WB-12, расширенный comfort NLP/quiz/feedback
WB-13–15, отдельный scope WB-16 и in-product release-history WB-17. Последняя страница
ещё не реализована; опубликованные релизы доступны на GitHub. WB-18 — отдельная
проверка interview playbook. [Актуальный статус](docs/context/CURRENT_STATE.md),
[backlog](docs/tasks/BACKLOG.md), [progress](docs/context/PROGRESS.md).

Основная реализация в журнале относится к 14–16 ноября 2026 МСК; документация WB-18
продолжена 21 ноября. **Активные часы разработчика и
агента не измерялись**; календарные timestamp CI/коммитов не выдаются за трудозатраты.
Пользователь задавал приоритеты, предоставил доступы и сообщил о восстановлении
браузерного доступа. Агент подготовил код/документы/тесты и выполнил описанные проверки.
Личная проверка пользователем и точная модель/стоимость агента не подтверждены.
[AI-LOG с конкретными решениями и изменениями](AI-LOG.md).

Практические выводы: SELECT перед записью не заменяет exclusion в БД; настоящий
конкурентный тест выявляет ошибки, которых не видно в scripted provider tests;
подтверждение SMTP и commit inbox не атомарны; deployment evidence и rollback надо
проектировать вместе с фичей. Подробные альтернативы и ограничения — в двух ADR.

## Демонстрация и подготовка к интервью

[PLAYBOOK](docs/interview/PLAYBOOK.md) связывает 18 задач с реальным кодом/тестами,
показывает безопасный локальный walkthrough и отличает планы P1 от работающего демо.
WB-18 выпущен в v1.4.3; [фактическая доставка](docs/evidence/WB-18-remote.md).
[72 вопроса](docs/interview/INTERVIEW_GUIDE.md),
[PR/SHA/evidence по задачам](docs/interview/evidence-links.md).
Проверка документации продолжена 21 ноября 2026: первоначальный трёхдневный план
не выдаётся за фактическую длительность всего проекта. Отдельный черновик личной
оценки часов подготовлен для пользователя; подтверждённого почасового учёта пока нет.

## Навигация по репозиторию

`apps/web` — React/Nginx; `services/booking` — API/Alembic/RPC/outbox;
`services/assistant` — FastAPI/MCP/LLM; `services/notification` — Worker/Jinja2/SQLite;
`tests/e2e` — Playwright; `infra` — Compose/ingress; `scripts` — проверки/delivery.
[PRD v1.2](docs/requirements/PRD_v1.2.md) и [approved decisions](docs/requirements/DECISIONS.md)
канонические. `references/` и static HTML — концепты, не исходники или доказательство
релиза. Исторический handoff: [START_HERE](START_HERE.md); статус реализации берите
из CURRENT_STATE, а не из старых startup prompts.
