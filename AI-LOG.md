# AI-LOG — фактическая работа, 2026-11-14

Codex продолжил существующий незакоммиченный React/FastAPI-каркас, найденный на
`chore/st-00-bootstrap`. Авторство исходного каркаса не установлено и агенту этой
сессии не приписывается. Человеческое ревью новых изменений пока не проводилось.

Агент прочитал AGENTS, WB-01, backlog, статус, релевантные разделы PRD и процесс.
Создал локальную `chore/wb-01-bootstrap` от `develop`, сохранив исходные изменения.
Добавил RabbitMQ/Mailpit, изолированный runner, инфраструктурные smoke-тесты,
Allure metadata, CI workflow и документацию. `.env` и значения секретов не читались.
Remote push, release и deploy не выполнялись.

Решения агента:

1. Проверять инфраструктуру в отдельном Compose-проекте с отдельными volumes
   без host ports: сохраняет уже работающий локальный стенд.
2. Использовать настоящий AMQP/SMTP/PostgreSQL; бизнес-RPC, worker и schema
   оставить соответствующим WB-задачам.
3. Сохранять SHA базового HEAD вместе с `working_tree=dirty`, отдельные artifacts
   и реальные ошибки; не выдавать локальную проверку за GitHub CI или релиз.

Команды: `git status --short --branch`, `git branch -avv`, чтение через `rg`
и `Get-Content`, `git switch -c chore/wb-01-bootstrap develop`, `docker version`,
`docker compose ... ps/build/run`, исходный pytest (4 passed), `uv lock`,
`npm install --package-lock-only`, Ruff check/format, `python scripts/check.py`.
Выявлены и исправлены Windows cp1251/UnicodeEncodeError и гонка root healthcheck
с Erlang cookie RabbitMQ. Итоговые результаты: [WB-01](docs/changes/WB-01.md).
Итог: 10 pytest + 2 Vitest + 5 Playwright прошли; Ruff, TypeScript/build,
actionlint, policy/handoff checks прошли. Allure HTML с 15 результатами создан
локально через `allure-commandline@2.32.0` и Java в Docker. Модель: Codex;
точный model id, стоимость и человеческое время не установлены.

Публикация WB-01 (новое поручение пользователя): проверен существующий пустой
GitHub repo smalvik/biocad-workspace; настроен origin. После проверки staged paths
и credential patterns создан `bc283c7` и отправлены main, develop,
chore/wb-01-bootstrap. Созданы issue #1 и PR #2; CI запущен, его успех пока не заявляется.
Для аутентификации локальный токен прочитан только в память и передан Docker
через environment, без включения в argv/URL/log. Секреты не коммитились.

WB-01: head CI `43598925846` прошёл; в PR явно зафиксирована самопроверка агента.
PR #2 слит в develop как `e5bb0b5`, ветка сохранена; полный post-merge regression
`43599195552` прошёл. Старый gh pr edit оказался несовместим с удалённым API;
описание обновлено через gh api. Человеческое approval не заявляется.

WB-02: issue #3, отдельная ветка от обновлённого develop. Агент реализовал
Alembic/GiST, demo sessions/CSRF/scrypt, idempotent create/cancel, availability,
transactional outbox и seed. Исправил расхождения D-07/ролей фикстуры по PRD;
описал выбор в ADR-001. Регрессия `python scripts/check.py --run-type regression`:
52 passed (41 Booking + 2 Assistant + 2 persistence + 2 Vitest + 5 Playwright),
Allure 50 passed. Проверены 20 конкурентов, 20 повторов ключа, прямой SQL,
инъекция outbox failure и реальные restart. Первые прогоны выявили ошибки
event loop scope и whitespace header в harness; исправлены, логи сохранены.
Изменения WB-02 пока локальны; их remote CI/merge/deploy не заявляются.
Локальный Booking обновлён с сохранением volume; через nginx проверены login,
availability, Swagger/CSRF inputs и logout, без создания пользовательских броней.
