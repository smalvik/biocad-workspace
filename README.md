# BIOCAD Workspace Booking

React/Vite, независимые FastAPI Booking и Assistant, PostgreSQL, RabbitMQ,
Mailpit и nginx. WB-01 интегрирован через PR #2 с успешным CI и post-merge regression.
В WB-02 добавлен Booking API с демо-сессиями, миграцией и защитой PostgreSQL;
результат его проверок — в [WB-02](docs/changes/WB-02.md).
В WB-03 реализована интерактивная SVG-карта двух этажей с настоящим API,
входом, фильтрами даты/времени и карточкой места. В WB-04 локально проверены поиск
сотрудников, оригинальные вымышленные аватары и таймлайн владельцев по интервалу.
Форма подтверждения брони, MCP/LLM и Notification Worker — следующие задачи.

Статус и доказательства: [CURRENT_STATE](docs/context/CURRENT_STATE.md),
[PROGRESS](docs/context/PROGRESS.md), [WB-01](docs/changes/WB-01.md).
WB-02 и исправление WB-11 интегрированы в develop/main через проверенные PR.
WB-03 слита в develop через [PR #9](https://github.com/smalvik/biocad-workspace/pull/9);
[post-merge regression PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43608755923).
Рабочее демо: **https://biocad.smalvik.dev** ·
[v1.0.0](https://github.com/smalvik/biocad-workspace/releases/tag/v1.0.0) ·
[Allure HTML](https://github.com/smalvik/biocad-workspace/releases/download/v1.0.0/index.html).
Вход: вымышленные `e01` … `e12`, пароль `demo-workspace`.

CI/CD WB-09: [runbook и фактический статус](docs/process/DELIVERY.md).
Реализованы SHA/digest images, отдельные staging/production проекты, ограниченный SSH
dispatcher, backup/rollback и Allure. Сервер обследован, BIOCAD admin/CI ключи созданы,
ограниченный dispatcher установлен. [Main workflow PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43626386129),
public desktop/mobile smoke — 2 passed; 23 старых контейнера сохранились.

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
LLM-ключи для WB-01 не требуются. Значения по умолчанию подходят только локальному демо.
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
использует `.env.example`, а LLM-ключи отключает. После проверки удаляет только свои
контейнеры и тестовые volumes. Уже запущенный проект `biocad` сохраняется.

Проверяются сборка/TypeScript, Ruff, pytest двух сервисов, настоящий PostgreSQL,
AMQP round trip через durable queue с persistent message, SMTP → Mailpit,
Vitest и Playwright Chromium для desktop/mobile. E2E проверяет вход/выход, два
этажа, календарные окна, фильтры, детали, клавиатуру, pan/zoom/fit, ошибки API,
просроченную сессию и запоздалые ответы. Бронирование через UI и реальный LLM ещё не проверяются.

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
Публикация отчёта, staging, immutable release images и production — WB-08/WB-09.

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
и поиск появятся в WB-04; форма подтверждения — WB-05. Сейчас карта не записывает бронь.

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
Проверки: [131 passed / реальные screenshots](docs/evidence/WB-04-local.md).

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
