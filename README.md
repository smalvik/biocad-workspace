# BIOCAD Workspace Booking

Локальный каркас WB-01: React/Vite, независимые FastAPI Booking и Assistant,
PostgreSQL, RabbitMQ, Mailpit и nginx. Страница показывает доступность двух API.
Карта, авторизация, схема броней, конкурентная защита, MCP/LLM и Notification Worker
предстоят в следующих задачах.

Статус и доказательства: [CURRENT_STATE](docs/context/CURRENT_STATE.md),
[PROGRESS](docs/context/PROGRESS.md), [WB-01](docs/changes/WB-01.md).
Публичный deploy, PR и опубликованные релизы пока не подтверждены.

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
Пользователей, миграций и seed в сервисе пока нет; JSON в `docs/data` — будущая фикстура.

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
Vitest и Playwright Chromium для desktop/mobile. E2E пока проверяет стартовую страницу,
proxy и отказ Assistant, а не бронирование или реальный LLM.

Логи, `run.json`, Allure results и Playwright HTML/trace сохраняются отдельно
в `artifacts/<UTC-run-id>/` (исключено из Git). SHA в отчёте — базовый HEAD;
`working_tree=dirty` явно отмечает незакоммиченные изменения.

`.github/workflows/ci.yaml` запускает эти проверки для PR в `develop`, полный
доступный набор после push в `develop`, генерирует Allure HTML и загружает artifacts.
Workflow подготовлен; успешный запуск GitHub Actions ещё не подтверждён.
Публикация отчёта, staging, immutable release images и production — WB-08/WB-09.

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
