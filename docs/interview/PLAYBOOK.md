# Interview playbook — WB-18, опубликован v1.4.3

Срез реализации: опубликованный main **4a40e18** ([v1.4.2](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.2)).
WB-18 опубликован в [v1.4.3](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.3); полная регрессия и
браузерная проверка red.log/green.log прошли. [Фактические gates](../evidence/WB-18-remote.md).
Проверка документа продолжена 21 ноября 2026 МСК. Текущий статус сервера подтверждается
отдельной проверкой, а не возрастом этого среза или фактом существования релиза.
Ответы из [INTERVIEW_GUIDE](INTERVIEW_GUIDE.md) сверены с реальными файлами и тестами.
Статусы: **совпадает** — подтверждено кодом; **исправлено** — гайд расходился с кодом и
исправлен; **не реализовано** — ответ описывает план, а не продукт. Показывайте код/тест,
а не пересказ. Числа проверок — из [WB-10 evidence](../evidence/WB-10-remote.md).

## Главный инвариант

Только Booking Service + PostgreSQL создают подтверждённую бронь. React, LLM, RabbitMQ
и email не могут нарушить эксклюзивность: последняя линия — `EXCLUDE USING gist
(space_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&) WHERE status='confirmed'`
в [миграции 0001](../../services/booking/migrations/versions/0001_booking_core.py).

## Сверка по задачам

| Задача | Статус ответов | Что показать |
|---|---|---|
| WB-01 | Совпадает: `/healthz` — процесс, `/readyz` — PostgreSQL (503 при недоступности) | [main.py](../../services/booking/app/main.py), [compose](../../infra/compose.yaml), [runner](../../scripts/check.py) |
| WB-02 | Совпадает; уточнение: `INSERT … ON CONFLICT DO NOTHING RETURNING`, до 3 попыток при `40P01`, затем 503 `BOOKING_RETRY` | [bookings.py](../../services/booking/app/bookings.py), [20 параллельных/same-key/adjacency](../../services/booking/tests/integration/test_booking_core.py), [deadlock](../../services/booking/tests/integration/test_deadlock_retry.py), [ADR-001](../adr/001-booking-consistency.md) |
| WB-03 | Совпадает: автообновление 25 с, кнопка «Обновить доступность», «Обновлено в … МСК», `data-testid` | [FloorMap.tsx](../../apps/web/src/FloorMap.tsx), [useSnapshot.ts](../../apps/web/src/useSnapshot.ts), [smoke.spec.ts](../../tests/e2e/specs/smoke.spec.ts) |
| WB-04 | **Исправлено**: API — `GET /api/v1/spaces?floor_id&from&to` (алиас `/api/v1/floors/{id}/occupancy`) и `GET /api/v1/employees/{id}/location?from&to` | [bookings.py](../../services/booking/app/bookings.py), [employees.py](../../services/booking/app/employees.py), [test_employees.py](../../services/booking/tests/integration/test_employees.py), [employees.spec.ts](../../tests/e2e/specs/employees.spec.ts) |
| WB-05 | Совпадает; также 403 `BOOKING_FORBIDDEN`, 404, 503 `BOOKING_RETRY`; повторная отмена не создаёт события | [bookings.py](../../services/booking/app/bookings.py), [useBookingFlow.ts](../../apps/web/src/useBookingFlow.ts), [bookings.spec.ts](../../tests/e2e/specs/bookings.spec.ts) |
| WB-06 | Совпадает. Tools: `search_employees`, `list_spaces`, `get_availability`, `get_space_details`, `propose_booking`, `ask_clarification`; **нет** write/cancel tool; подпись предложения 10 мин | [mcp_server.py](../../services/assistant/app/mcp_server.py), [proposals.py](../../services/assistant/app/proposals.py), [test_assistant.py](../../services/assistant/tests/integration/test_assistant.py), [ASSISTANT.md](../architecture/ASSISTANT.md) |
| WB-07 | Совпадает; inbox — приватный SQLite WAL, `event_id UNIQUE` + digest; exactly-once SMTP **не** обещается | [outbox.py](../../services/booking/app/outbox.py) (`SKIP LOCKED`), [store.py](../../services/notification/app/store.py), [test_delivery.py](../../services/notification/tests/test_delivery.py), [ADR-002](../adr/002-broker-and-outbox.md) |
| WB-08 | Совпадает: child DB без constraint → RED 2 failed; восстановленный → GREEN 3 passed, тот же oracle | [experiment.py](../../services/booking/race_probe/experiment.py), [invariant.py](../../services/booking/race_probe/invariant.py), [RED](../evidence/concurrency-red.md), [GREEN](../evidence/concurrency-green.md) |
| WB-09 | **Исправлено**: webhook не используется. Actions → SSH-ключ `restrict,command="/usr/local/bin/biocad-ssh-entry"` → dispatcher с allowlist JSON-операций; promotion точных digest | [ci.yaml](../../.github/workflows/ci.yaml), [bootstrap_server.py](../../scripts/bootstrap_server.py), [deploy_server.py](../../scripts/deploy_server.py), [test_delivery.py](../../tests/delivery/test_delivery.py), [DELIVERY.md](../process/DELIVERY.md) |
| WB-10 | Совпадает | [C1](../architecture/C1.md), [C2](../architecture/C2.md), [EVIDENCE](../architecture/EVIDENCE.md), [AI-LOG](../../AI-LOG.md) |
| WB-11 | Совпадает; реальный пример — #34: `40P01` → 500, найден WB-08 probe | [WB-11 note](../changes/WB-11.md), [evidence](../evidence/WB-11-booking-deadlock.md), [PR #35](https://github.com/smalvik/biocad-workspace/pull/35) |
| WB-12 | **Не реализовано**: только free-only модель и один bounded retry 429 той же модели | [config.py](../../services/assistant/app/config.py), [test_free_provider.py](../../services/assistant/tests/unit/test_free_provider.py) |
| WB-13–15 | **Не реализовано**: ответы — дизайн | [backlog](../tasks/BACKLOG.md) |
| WB-16 | Частично: счётчик нескольких броней и интервалы есть (`occupancy_kind="multiple"`, `is_partial`); отдельный calendar-scope не начат | [bookings.py](../../services/booking/app/bookings.py), [domain.test.ts](../../apps/web/src/domain.test.ts), [smoke.spec.ts](../../tests/e2e/specs/smoke.spec.ts) |
| WB-17 | Частично: task notes, [docs/releases](../releases/v1.4.2.md), GitHub Releases и asset `releases.json`; **in-product страница `/releases` и загрузка истории в UI не реализованы** | [publish_release.py](../../scripts/publish_release.py) |
| WB-18 | Этот документ | — |

## Демо-сценарий (10–12 минут)

Для записи используйте [локальный Compose](../../README.md#запуск-локально),
http://localhost:8080, вымышленные `e01`/`e02`, пароль `demo-workspace`.
https://biocad.smalvik.dev подходит для просмотра готового демо и отчётов.
Сбои и fault injection — только в изолированной регрессии. Сам walkthrough ниже
не означает, что пользователь уже выполнил эти шаги.

1. **Карта** (2 мин): `e01`, этаж с D-07; место закреплено за Анной и не бронируется.
   Лицо = бронь/закрепление на период, не физическое присутствие. Для смены владельцев
   D-03 выберите исторический seed **16.11.2026**: Мария 10–12, свободно 12–14,
   Павел 14–16 МСК. Это чтение демо-данных. Для создания выберите новую будущую дату:
   16 ноября уже в прошлом, бронирование на неё правильно отклоняется.
2. **Поиск сотрудника** (1 мин): найти коллегу → карта фокусируется на его месте за период.
3. **Ручная бронь** (2 мин): свободный FreeDesk → «Продолжить» → проверить точный ресурс
   и интервал МСК → подтвердить → «Мои бронирования». Пока не отменяйте: запись
   нужна для следующего шага. Запишите точные ресурс/дату/время.
4. **Конфликт** (1 мин): заранее подготовьте тот же свободный слот для `e02` в
   **другом браузерном профиле/инкогнито**. Две обычные вкладки делят cookie и не
   представляют двух независимых пользователей. После commit `e01` подтвердите
   оставшееся старое предложение `e02`: 409, без второй брони. При свежем открытии
   UI покажет слот занятым и не предложит подтверждение — это также корректно.
   Смежный будущий интервал проходит; затем каждый пользователь отменяет свои записи.
   Одновременные INSERT и точный HTTP-статус надёжнее показать в real-PostgreSQL тесте.
5. **AI** (2 мин, если бесплатный провайдер доступен): запрос → подсветка → отдельное
   подтверждение. При 429/недоступности форма работает — это ожидаемое поведение.
6. **Доказательства** (3 мин): [Allure](https://biocad.smalvik.dev/allure/) с race
   red/green логами, [main workflow](https://github.com/smalvik/biocad-workspace/actions/runs/43788663155),
   release с digest. Mailpit наружу не опубликован: письма показывать в локальном
   Compose (http://localhost:8025) или через E2E-проверки в Allure.

## Воспроизводимая проверка и границы доказательств

Из корня репозитория, Python 3.12+ и Docker:

```powershell
python scripts/check.py --run-type regression
```

Runner создаёт собственную среду, запускает настоящие PostgreSQL/RabbitMQ/MCP/Mailpit,
существующие unit/integration и desktop/mobile E2E, затем удаляет только свой проект.
Raw Allure и логи — в `artifacts/<UTC-run-id>`. Не запускайте SQL fault injection на
базе локального рабочего стенда или production. В текущем runner smoke/regression
выполняют один набор с разными metadata. Браузерные проверки записи ограничены
local/isolated hosts; публичный smoke не создаёт/отменяет брони.

Для демонстрации чувствительности откройте [версионный Allure v1.4.3](https://biocad.smalvik.dev/allure/v1.4.3/):
**Behaviors → race-red-green → Race sensitivity: genuine red FAIL, restored green
PASS (disposable DB only)** → `red.log` / `green.log`. Там настоящий child RED
с 2 failed и GREEN с 3 passed; обычный outer gate успешен только при восстановлении
constraint и удалении своей БД. Эти child counts не прибавляются к headline regression.
Vitest отдельно от raw Allure, UI Allure может группировать повторные phase/history.

Сценарий ручной гонки показывает stale availability; синхронизацию двух настоящих
INSERT и прямую DB-проверку доказывает автоматический эксперимент, не две вкладки
с общей сессией. Исходный WB-11 40P01/500 при включённом constraint сохранён
отдельно от намеренной поломки RED. Подробности — [deadlock evidence](../evidence/WB-11-booking-deadlock.md).

## Неудобные вопросы

- **«Вы это писали сами?»** — Код и тесты подготовил агент по приоритетам пользователя;
  ревью PR — самопроверка агента, не human approval. Защищайте решения через ADR и тесты.
  Часы не измерялись ([AI-LOG](../../AI-LOG.md)); отдельная оценка для проверки не
  становится фактическим учётом до подтверждения пользователем.
- **«Почему нет failover/comfort/quiz?»** — В первоначальном трёхдневном плане
  приоритет отдали P0; P1/P2 в [backlog](../tasks/BACKLOG.md). Документация WB-18
  продолжена 21 ноября: не утверждайте, что весь проект завершён за три дня.
- **«Регрессия использует настоящий LLM?»** — Нет: CI LLM — scripted fixture; MCP,
  RabbitMQ, PostgreSQL настоящие. Реальный free-model прогон — отдельный
  [v1.3.0 live report](https://biocad.smalvik.dev/allure/v1.3.0/live/), cost=0.
- **«Слабые места?»** — SMTP-accept и commit inbox не атомарны (возможен дубль);
  rollback БД не автоматический; SQLite inbox рассчитан на один Worker; free-модель
  может отвечать 429.

`INTERVIEW_GUIDE.docx` — историческая копия до сверки; актуальны Markdown-файлы.
