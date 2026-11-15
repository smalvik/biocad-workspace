# BIOCAD Workspace Booking

React/Vite, независимые FastAPI Booking и Assistant, PostgreSQL, RabbitMQ,
Mailpit и nginx. WB-01 интегрирован через PR #2 с успешным CI и post-merge regression.
В WB-02 добавлен Booking API с демо-сессиями, миграцией и защитой PostgreSQL;
результат его проверок — в [WB-02](docs/changes/WB-02.md).
В WB-03 реализована интерактивная SVG-карта двух этажей с настоящим API,
входом, фильтрами даты/времени и карточкой места. В WB-04 опубликованы поиск
сотрудников, оригинальные вымышленные аватары и таймлайн владельцев по интервалу.
WB-05 (форма, «Мои бронирования», отмена) выпущена в v1.2.0, 157 regression passed.
WB-06 (MCP/RabbitMQ/AI-чат) и исправление planning #24 выпущены в **v1.3.0**.
Работает настоящая `inclusionai/ling-3.2-flash:free`, только бесплатно, бюджет $0,
без платного fallback. AI предлагает ресурс, отдельное подтверждение создаёт бронь.
Полная регрессия 189 passed; реальная production приёмка — 3 API + 2 browser passed,
все успешные ответы cost=0. Free-провайдер может вернуть 429; ручная форма доступна.
WB-07 выпущен в **v1.4.0**: независимый Notification Worker отправляет письма о создании
и отмене через RabbitMQ в Mailpit. Полная регрессия 237 passed; обновление/откат с
v1.3.1 и восстановление после отказов брокера/SMTP проверены на реальных сервисах.
В v1.3.1 добавлен [просмотр Allure в браузере](https://biocad.smalvik.dev/allure/)
с автоматическим обновлением после релиза и архивом версий.

Статус и доказательства: [CURRENT_STATE](docs/context/CURRENT_STATE.md),
[PROGRESS](docs/context/PROGRESS.md), [WB-01](docs/changes/WB-01.md).
WB-02 и исправление WB-11 интегрированы в develop/main через проверенные PR.
WB-03 слита в develop через [PR #9](https://github.com/smalvik/biocad-workspace/pull/9);
[post-merge regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608755923).
Рабочее демо: **https://biocad.smalvik.dev** ·
[v1.4.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.4.0) ·
[Allure в браузере](https://biocad.smalvik.dev/allure/).
Вход: вымышленные `e01` … `e12`, пароль `demo-workspace`.

CI/CD WB-09: [runbook и фактический статус](docs/process/DELIVERY.md).
Реализованы SHA/digest images, отдельные staging/production проекты, ограниченный SSH
dispatcher, backup/rollback и Allure. Сервер обследован, BIOCAD admin/CI ключи созданы,
ограниченный dispatcher установлен. [Main workflow PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43763748048),
237 regression / server Allure 213 raw results; отдельный
[real free LLM Allure v1.3.0](https://biocad.smalvik.dev/allure/v1.3.0/live/).
[Архив v1.3.0](https://biocad.smalvik.dev/allure/v1.3.0/).
23 старых контейнера и существующие брони/аккаунты сохранились.
[Фактические evidence и ограничения WB-07](docs/evidence/WB-07-remote.md).

## Локальный запуск

Нужны Docker с Linux containers и Compose >= 2.24.4. Node и uv на хосте не нужны.
Из корня репозитория:

```powershell
docker compose --env-file .env.example -f infra/compose.yaml up -d --build --wait
```

Страница: http://localhost:8080. Booking Swagger: http://localhost:8080/api/docs.
Assistant Swagger: http://localhost:8080/api/v1/assistant/docs. Mailpit: http://localhost:8025.
API/БД/почта опубликованы только на loopback; RabbitMQ доступен внутри сети Compose.
Проверка БД: http://localhost:8080/api/v1/readyz. `/healthz` проверяет жизнь процесса,
`/readyz` Booking проверяет PostgreSQL и возвращает 503 при недоступности БД.

Для собственных настроек скопируйте `.env.example` в игнорируемый `.env` и используйте
`--env-file .env` вместо `--env-file .env.example`. Не меняйте пароль уже созданного
PostgreSQL volume только через env: это не изменит пароль роли в БД.
Без OpenRouter-ключа ручное бронирование работает; для AI укажите в ignored `.env`
`OPENROUTER_API_KEY`, `OPENROUTER_PRIMARY_MODEL=inclusionai/ling-3.2-flash:free`,
`ASSISTANT_FREE_ONLY=true`, `ASSISTANT_BUDGET_USD=0` и длинный
`ASSISTANT_PROPOSAL_SECRET`. Платные модели/fallback не разрешены.
Значения по умолчанию подходят только локальному демо.
Booking при запуске выполняет Alembic `upgrade head`. Локальный Compose включает
`SEED_DEMO_DATA=true`: вымышленные данные из `docs/data/demo_fixture.json` загружаются
идемпотентно, без перезаписи существующих броней. Вне локального окружения нужен
собственный `SESSION_SECRET` длиной минимум 32 символа.

Остановить стенд с сохранением данных:

```powershell
docker compose --env-file .env.example -f infra/compose.yaml down
```

## Проверки

С Python 3.12+ и Docker:

```powershell
python scripts/check.py
python scripts/check.py --run-type regression
python scripts/check_policy.py
```

Каждый прогон создаёт отдельный Compose-проект без host ports и отдельные volumes;
использует `.env.example`, не читает локальные LLM-ключи и запускает явно scripted
HTTP-провайдер без платных запросов. MCP SDK, RabbitMQ и PostgreSQL настоящие.
После проверки удаляет только свои
контейнеры и тестовые volumes. Уже запущенный проект `biocad` сохраняется.

Проверяются сборка/TypeScript, Ruff, pytest трёх сервисов, настоящий PostgreSQL,
AMQP round trip через durable queue с persistent message, SMTP → Mailpit,
Vitest и Playwright Chromium для desktop/mobile. E2E проверяет вход/выход, два
этажа, календарные окна, фильтры, детали, клавиатуру, pan/zoom/fit, ошибки API,
просроченную сессию и запоздалые ответы, создание/отмену через UI и AI-предложение
с отдельным подтверждением. Реальный OpenRouter проверяется отдельно с разрешённой
бесплатной моделью и бюджетом $0; scripted regression не считается доказательством live LLM.

Логи, `run.json`, Allure results, Playwright HTML и screenshots сохраняются отдельно
в `artifacts/<UTC-run-id>/` (исключено из Git). SHA в отчёте — базовый HEAD;
`working_tree=dirty` явно отмечает незакоммиченные изменения.

Authenticated traces отключены: cookies/CSRF не сохраняются в network artifacts.
`.github/workflows/ci.yaml` проверяет PR в `develop`/`main`, полный набор после push
в обе ветки, генерирует Allure HTML и загружает artifacts.
Для WB-01 подтверждены [PR CI](https://github.com/smalvik/biocad-workspace/actions/runs/43598925846)
и [post-merge regression](https://github.com/smalvik/biocad-workspace/actions/runs/43599195552).
WB-02: [develop regression](https://github.com/smalvik/biocad-workspace/actions/runs/43604565825)
и [main regression](https://github.com/smalvik/biocad-workspace/actions/runs/43604855360) — PASS.
Публикация отчёта, staging, immutable release images и production реализованы в WB-09;
дополнительные race/red-green evidence остаются WB-08.

## Уведомления — WB-07 (v1.4.0)

Подтверждение и отмена сохраняют событие в той же транзакции PostgreSQL. Отдельный
publisher отправляет его с подтверждением RabbitMQ; Worker сохраняет собственный
SQLite inbox в volume `notificationdata` перед ACK и отправляет HTML/text через Mailpit.
У Worker нет доступа к Booking DB. Сбои RabbitMQ/SMTP не откатывают бронь; доставка
повторяется с задержкой до 60 секунд, состояние переживает перезапуск.

Письмо содержит вымышленные ФИО/адрес, ресурс/этаж, точный интервал МСК, код брони
и ссылку на приложение. Локально откройте http://localhost:8025 после бронирования.
На сервере Mailpit остаётся внутренним; письма и их HTML проверяются в Allure.
Разрешены только адреса `@example.test` и демо SMTP. Готовые события дедуплицируются;
сбой между принятием SMTP и локальным commit может привести к повтору — SMTP exactly-once
не обещается. Миграция Booking DB не требуется; старые события обогащаются при публикации.
[ADR и ограничения](docs/adr/002-broker-and-outbox.md),
[реальные проверки и откат](docs/evidence/WB-07-local.md),
[релиз/сервер/публичные проверки](docs/evidence/WB-07-remote.md).

## Assistant — WB-06 (v1.3.0)

Для нового Assistant-кода смотрите [контракт и настройки WB-06](docs/architecture/ASSISTANT.md).
В `.env` требуются реальный ключ, `OPENROUTER_PRIMARY_MODEL=inclusionai/ling-3.2-flash:free`,
отдельный секрет предложений и `ASSISTANT_BUDGET_USD=0`. Разрешены только бесплатные
модели: актуальный каталог и каждый provider request проверяют нулевую цену;
платного fallback нет. Rate limits бесплатного провайдера могут временно ограничить чат.
Кнопка «AI-ассистент» запрашивает согласие на отправку текста в OpenRouter.
AI только предлагает ресурс/период; кнопка «Проверить предложение AI» открывает
обычное точное подтверждение. Ручная форма работает независимо от AI/брокера.
Доступно в public v1.3.0; [реальные проверки и Allure](docs/evidence/WB-06-remote.md).

## Booking API — WB-02

Локальные демо-логины: `e01` … `e12`, пароль по умолчанию `demo-workspace`
(только вымышленные аккаунты). E01 — Анна, e02 — Дмитрий, e03 — Мария.
`DEMO_PASSWORD` задаёт пароль при первом seed; повторный seed пароль существующей
учётной записи не меняет. Настоящего SSO нет.

В [Swagger](http://localhost:8080/api/docs):

1. Выполните `POST /api/v1/auth/login` с `username` и `password`.
   Браузер сохранит HttpOnly session cookie; ответ содержит `csrf_token`.
2. Прочитайте `GET /api/v1/floors` и `GET /api/v1/spaces` с `floor_id`, `from`, `to`.
   Даты — ISO с offset, например `2026-11-16T12:00:00+03:00`.
3. Для `POST /api/v1/bookings` передайте `X-CSRF-Token`, уникальный `Idempotency-Key`
   и точные `space_id`, `start_at`, `end_at`. Передайте их только после явного
   решения подтвердить этот ресурс/интервал. Сервер возьмёт владельца из сессии.
4. `GET /api/v1/bookings/me` показывает свои записи; `POST /api/v1/bookings/{id}/cancel`
   с тем же CSRF-токеном отменяет только собственную бронь.

Первое подтверждение — 201; повтор идентичного запроса с тем же ключом — 200
и та же бронь, даже после отмены. Новый payload с прежним ключом и пересечение — 409.
Смежные интервалы разрешены; отмена освобождает слот. Отсутствие сессии — 401,
чужая отмена/неверный CSRF — 403, некорректный период — 422. Новые брони в прошлом
отклоняются; это локальное правило WB-02. Нужны даты в будущем относительно сервера.

Время хранится/возвращается в UTC; карта показывает время Europe/Moscow.
D-07 закреплён за Анной и не бронируется. D-03 имеет два фиксированных слота
16.11.2026 (10–12 Мария, 14–16 Павел МСК); 12–14 свободно.
Поля reservations описывают бронь на время, не физическое присутствие.

Outbox-событие сохраняется с бронью в одной транзакции; отправки через RabbitMQ
и писем о пользовательских бронях пока нет. [ADR-001](docs/adr/001-booking-consistency.md).
Runner проверяет сохранность после настоящего restart PostgreSQL и Booking.

## Карта — WB-03

Откройте http://localhost:8080/ и войдите (`e01`, `demo-workspace` по умолчанию).
Основной план — 24 стола и 3 переговорные; второй — 12 столов и 2 переговорные.
Офисные зоны, стены, двери, окна и вентиляция схематические и вымышленные.
Положения ресурсов и статусы приходят из Booking API, а не из PNG.

Выберите этаж, дату и интервал МСК; быстрые окна помогают проверить сценарий D-03.
Поставьте фильтры типов/«Только свободные». Место выбирается кликом, Tab+Enter
или через доступный список под картой; на мобильном карточка открывается снизу.
Карту можно двигать за фон, приближать колесом/+ и возвращать кнопкой fit.
При фокусе на схеме стрелки двигают её, Home возвращает исходный вид.

Ручное обновление и polling 25 с получают новый snapshot. При смене периода
старые статусы скрываются, прежний запрос отменяется; ответ другого периода
не применяется. Карточка показывает все пересекающиеся брони и точное время.
Это сведения о резервировании, не физическом присутствии. Авторы брони/аватары
и поиск реализованы в WB-04. В WB-05 карта поддерживает запись
после отдельного подтверждения; доступно в public v1.2.0.

Seed обновляет геометрию floor/space для демо; существующие брони, аккаунты
и пароли сохраняются. Alembic `0002_floor_plan` добавляет поле плана без изменения
bookings/exclusion. [Проверки и настоящие screenshots](docs/evidence/WB-03-local.md).

## Поиск сотрудников — WB-04

WB-04: поиск по ФИО/отделу переключает этаж и выбирает бронь/постоянное место.
Период 16.11.2026 для D-03: Мария 10–12, свободно без лица 12–14,
Павел 14–16; 09–17 показывает два лица и полный таймлайн. Лица обозначают
бронь/закрепление, а не присутствие. `GET /api/v1/employees?q=&from=&to=`,
`/api/v1/employees/{id}/location?from=&to=` и `/api/v1/floors/{id}/occupancy?from=&to=`
требуют демо-сессию; дата/время передаются с UTC offset.
Без времени directory возвращает только профили, не предполагает текущую локацию.
Портреты — собственные SVG-иллюстрации; отсутствие/ошибка картинки даёт инициалы.
Проверки: [131 passed / реальные screenshots](docs/evidence/WB-04-local.md),
[выпуск v1.1.0 / сервер / public smoke](docs/evidence/WB-04-remote.md).

## Бронирование — WB-05

Свободное место/переговорная → «Продолжить» → проверка точного
ресурса/офиса/этажа/МСК → «Подтвердить бронирование». До этого записи нет.
«Мои бронирования» показывает свои confirmed/cancelled записи; отмена тоже
требует подтверждения. При потере ответа повторяет исходную операцию, включая
после reload вкладки. [Локальные проверки](docs/evidence/WB-05-local.md),
[реальный release/server/public smoke](docs/evidence/WB-05-remote.md).

## Begin here (VS Code + Codex)

1. Unzip the handoff; open **`biocad-workspace`** as the VS Code workspace folder (`File → Open Folder`).
2. Install/open the official **Codex IDE extension**, sign in using your ChatGPT account; or use Codex CLI from the workspace terminal.
3. Open `START_HERE.md` and paste the text from `CODEX_FIRST_PROMPT.md` into Codex. The root `AGENTS.md` is its recurring task contract.
4. Run `python scripts/verify_handoff.py` to confirm files and asset counts. This does not test a product.
5. Read `CURRENT_STATE.md` and `PROGRESS.md`, then continue the next unfinished WB task on its own branch.
6. Configure API keys and tokens **locally** using env files ignored by Git and GitHub Actions Secrets, never in chats or committed files.

## Canonical project contents
- `docs/requirements/PRD_v1.2.md` — full PRD v1.2, the canonical scope and acceptance rules.
- `docs/context/CHAT_HANDOFF.md` — human-readable distilled history of decisions across this ChatGPT thread.
- `docs/context/CURRENT_STATE.md` — evidence-based status; no code falsely marked shipped.
- `docs/tasks/` — branch-by-task backlog WB-01…WB-18.
- `docs/design/UI_CONTRACT.md` — map/avatars/calendar/drawer/responsiveness/UI tokens.
- `references/desktop`, `tablet`, `mobile` — 54 latest PNGs covering 18 WB steps.
- `references/calendar_scenarios` — 12 scenarios + overview for four time ranges.
- `references/legacy` — early prototypes/reference PNGs, not requirements.
- `references/viewer_standalone.html` — static interactive viewer, **not** React/MCP production code.
- `docs/interview/INTERVIEW_GUIDE.md` — 72 practice questions/answers.
- `docs/changes` and `docs/releases` — task/release notes templates. Historic release UI is **demo only**.
- `docs/process/DEVELOPMENT_PROCESS.md` — required Git, test, staging and release procedure.
- `CODEX_FIRST_PROMPT.md` and `docs/codex/PROMPTS.md` — prompts for startup and one task at a time.

## Primary rules
The real product must implement the original test assignment faithfully, including PostgreSQL concurrent booking, adjacent timestamps, idempotency, persistence, working React booking form, live MCP + real LLM assistant, RabbitMQ services, Mailpit, Playwright / pytest / Allure, C1/C2/ADR/AI-LOG and a public deploy. P1 comfort features, quiz and feedback follow working P0.

Do not count these PNGs, copied markdown documents or HTML prototypes as completed product development. See `docs/context/CURRENT_STATE.md`.
