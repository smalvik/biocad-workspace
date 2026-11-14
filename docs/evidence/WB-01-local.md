# WB-01 — локальный smoke, 2026-11-14

Проверен незакоммиченный рабочий каталог `chore/wb-01-bootstrap`.
Base HEAD: `4b005dd7e5ad39a4d0502fa9e455c180d00504d1`, `working_tree=dirty`.
Run ID `20261114T124950Z-46a9ee` содержит время UTC (15:49:50 Europe/Moscow).
Это локальный smoke каркаса, не GitHub CI, не post-merge regression и не релиз.

Команда из корня:

```powershell
python scripts/check.py
```

Runner создал `biocad-check-20261114t124950z-46a9ee`, собрал runtime/test images,
поднял PostgreSQL/RabbitMQ/Mailpit/Booking/Assistant/web с `--wait`, выполнил
проверки и удалил только свои контейнеры, сеть и volumes. `.env` не загружался;
использованы `.env.example` и отдельные фиксированные тестовые настройки.

| Проверка | Фактический результат |
|---|---|
| Compose config/build/health gates | exit 0, все 6 сервисов healthy |
| Booking pytest | 8 passed in 2.45s |
| Assistant pytest | 2 passed in 0.12s |
| Vitest | 2 passed |
| Production build / web TypeScript | exit 0 |
| E2E TypeScript | exit 0 |
| Playwright Chromium | 5 passed (12.2s), 3 desktop + 2 mobile |
| Ruff check/format двух сервисов | exit 0 |
| Завершение/очистка runner | exit 0, run.json result=passed |
| Allure results | 15 passed, без failed/skipped; Vitest отдельно |

AMQP-тест создал собственную durable queue, отправил persistent message,
прочитал/подтвердил его и удалил только эту очередь. SMTP-тест отправил
письмо на вымышленный `example.test` адрес и нашёл его в настоящем Mailpit API.
PostgreSQL проверен через running Booking `/readyz`. Бронирования,
сохранность доменных данных после рестарта и GiST concurrency здесь не проверяются — WB-02.
Сбой Assistant в браузерном smoke смоделирован ответом 503 через Playwright route.

Дополнительно выполнены `python scripts/check_policy.py` с корректными PR branch/title,
`python -X utf8 scripts/verify_handoff.py`, `git diff --check` и
`docker run --rm -v "C:/projects/biocad-workspace:/repo" -w /repo rhysd/actionlint:latest .github/workflows/ci.yaml`;
все завершились с exit 0. Это локальная валидация workflow; запуск Actions не утверждается.

Локальные файлы (исключены из Git):

- [Команды и полный вывод](../../artifacts/20261114T124950Z-46a9ee/commands.log)
- [Машиночитаемый результат](../../artifacts/20261114T124950Z-46a9ee/run.json)
- [Standalone Allure HTML](../../artifacts/20261114T124950Z-46a9ee/allure-report/index.html)
- [Playwright HTML](../../artifacts/20261114T124950Z-46a9ee/playwright-report/index.html)

Allure HTML действительно сгенерирован командой (exit 0):

```powershell
docker run --rm -v "C:/projects/biocad-workspace/artifacts:/reports" -v biocad-allure-cli:/tools:ro eclipse-temurin:17-jre-jammy /tools/node_modules/allure-commandline/dist/bin/allure generate /reports/20261114T124950Z-46a9ee/allure-results --single-file --clean -o /reports/20261114T124950Z-46a9ee/allure-report
```

До этого `allure-commandline@2.32.0` установлен в named volume `biocad-allure-cli`
через `npm install` внутри `node:22.12.0-bookworm-slim`. Allure labels:
`run_type=smoke`, `environment=local`, `git_sha=<base HEAD>`,
`working_tree=dirty`, `release_version=unreleased`.

Неуспешные первые прогоны сохранены в `artifacts/20261114T124443Z-ae9416`
(Windows cp1251/UnicodeEncodeError) и `artifacts/20261114T124614Z-84b575`
(root healthcheck/Erlang cookie race). Ошибки исправлены перед зелёным прогоном.
PR, code review, merge, staging, Docker Hub и release не выполнялись.
