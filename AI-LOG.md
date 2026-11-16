# AI-LOG — фактическая работа, 14–16 ноября 2026 (МСК)

Пользователь задавал приоритеты, предоставил доступы в ignored env, разрешил
push/PR/merge/deploy, выбрал **только бесплатную модель / бюджет $0** и сообщил,
что браузерный доступ восстановился. Codex подготовил код, тесты, документы и
выполнил зафиксированные проверки. Личные code review/тесты пользователя не
подтверждены. Review в PR — явная самопроверка агента, не независимое human approval.
Активные часы разработчика/агента не измерялись; календарные даты их не заменяют.
Точная модель/стоимость агента неизвестны. Не заявляем сэкономленные часы.

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

Срез продукта v1.4.1: отдельные [PR #35](https://github.com/smalvik/biocad-workspace/pull/35)/
[#36](https://github.com/smalvik/biocad-workspace/pull/36), main [#37](https://github.com/smalvik/biocad-workspace/pull/37),
source **5364c9e**, [CI/server PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648):
248 checks / 35 commands exit 0 / 224 raw server Allure. RED 2 failed, GREEN 3 passed
в child DB; public app 4/report 4/race attachments 2 PASS, downloads=0; данные и
23 чужих контейнера сохранены. [Progress и история](docs/context/PROGRESS.md).

WB-10 выпущен в **v1.4.2**, [issue #38](https://github.com/smalvik/biocad-workspace/issues/38),
`docs/wb-10-delivery-evidence` от develop05e08e6 с перенесёнными WB-08 notes e301cb3:
agent сверяет C1/C2/ADR с кодом, сокращает README, составляет evidence index и
проверил clean local запуск: 7 healthy, 4 browser smoke PASS; Mermaid3 и full248
PASS, 35 commands exit0 / raw Allure222. [Task note](docs/changes/WB-10.md),
[actual commands](docs/evidence/WB-10-remote.md). Часы запрошены, пока не указаны.
PR39 → develope8e29cf, PR40 → main4a40e18;
[CI/server 43788663155 PASS](https://github.com/smalvik/biocad-workspace/actions/runs/43788663155): 248/35exit0/raw224.
Public app4/report4 PASS, download0; данные/23 чужих контейнера сохранены.
Новых LLM calls и runtime changes не было; следующая P0 docs — WB-18.
Весь PRD и отложенные WB-12–18 не объявляются готовыми.
