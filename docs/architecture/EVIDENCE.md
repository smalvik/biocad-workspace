# Evidence index — код, проверка и наблюдаемое поведение

Индекс среза v1.4.1 и текущей документации WB-10. Не заменяет логи/CI и не означает
готовности всего PRD. Исторические локальные пути под artifacts игнорируются Git;
долговечные публичные доказательства — Actions artifacts, GitHub Release assets и
versioned Allure. Actions artifacts имеют ограниченный retention, release assets сохраняют
основные proof/log/manifest/aggregate summaries. Не публикуйте raw production snapshots.

| Демонстрация / инвариант | Код и настоящий тест | Публичное доказательство |
|---|---|---|
| Одно подтверждение на пересекающийся слот, идемпотентный повтор, смежные интервалы, отмена только своей | [bookings](../../services/booking/app/bookings.py), [20 parallel requests / SQL / rollback tests](../../services/booking/tests/integration/test_booking_core.py), [deadlock retry](../../services/booking/tests/integration/test_deadlock_retry.py) | [v1.4.1 main CI](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648), [ADR-001](../adr/001-booking-consistency.md) |
| RED: без child constraint два реальных HTTP процесса создают две брони; GREEN: та же проверка с exact restoration даёт одного победителя | [experiment](../../services/booking/race_probe/experiment.py), [unchanged oracle](../../services/booking/race_probe/invariant.py), [outer gate](../../services/booking/tests/integration/test_race_sensitivity.py) | [RED](../evidence/concurrency-red.md), [GREEN](../evidence/concurrency-green.md), [released raw proof](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/race-proof.json) |
| Face = выбранная бронь/закрепление; смена периода, несколько владельцев, отсутствие картинки | [employee API tests](../../services/booking/tests/integration/test_employees.py), [desktop/mobile UI](../../tests/e2e/specs/employees.spec.ts) | [WB-04 evidence](../evidence/WB-04-remote.md), [последний report](https://biocad.smalvik.dev/allure/) |
| Форма → точное подтверждение → свои брони → отмена; lost-response retry/reload | [flow hook](../../apps/web/src/useBookingFlow.ts), [browser E2E](../../tests/e2e/specs/bookings.spec.ts) | [WB-05 evidence](../evidence/WB-05-remote.md), [v1.4.1 regression](https://biocad.smalvik.dev/allure/v1.4.1/) |
| Реальный MCP STDIO + RabbitMQ read/propose; подтверждение отдельное; AI outage оставляет форму | [Assistant integration](../../services/assistant/tests/integration/test_assistant.py), [UI including service outage](../../tests/e2e/specs/assistant.spec.ts), [protocol](ASSISTANT.md) | [WB-06](../evidence/WB-06-remote.md); CI LLM scripted, не live proof |
| Настоящий бесплатный provider, cost=0, без booking writes | [live checker](../../scripts/check_live_assistant.py), [free-only settings](../../services/assistant/app/config.py) | [Оригинальный live report v1.3.0](https://biocad.smalvik.dev/allure/v1.3.0/live/): 3 API + 2 browser PASS, initial mobile 429 сохранён отдельно; новых вызовов WB-10 не требует |
| Booking survives PostgreSQL/service restart | [real persistence phases](../../services/booking/tests/integration/persistence_check.py), [runner](../../scripts/check.py) | [main regression](https://github.com/smalvik/biocad-workspace/actions/runs/43779639648) |
| Atomic outbox, broker/SMTP outage recovery, Worker restart/replay/dedup, реальные письма | [publisher tests](../../services/booking/tests/integration/test_outbox_publisher.py), [recovery phases](../../services/booking/tests/integration/notifications_recovery.py), [Worker tests](../../services/notification/tests/test_delivery.py), [UI/mail E2E](../../tests/e2e/specs/bookings.spec.ts) | [WB-07 proof/rollback](../evidence/WB-07-local.md), [released audit](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/notification-audit.json) |
| Same-SHA PR/push build-once; точные digest staging → production, backup и rollback isolation | [workflow](../../.github/workflows/ci.yaml), [package](../../scripts/package_images.py), [dispatcher](../../scripts/deploy_server.py), [manifest](../../scripts/delivery_manifest.py) | [build-once proof](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/build-once-proof.json), [manifest](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/candidate.json), [delivery runbook](../process/DELIVERY.md) |
| Allure HTML просматривается inline, source/checksum совпадают, red/green logs раскрываются без download | [public HTTP check](../../scripts/check_public_allure.py), [Web nginx](../../apps/web/nginx.conf) | [WB-09 fix](../evidence/WB-09-allure-web.md), [actual browser race results](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/race-browser-smoke.json) |
| Не сломать существующие приложения и данные | [scoped deployment](../../scripts/deploy_server.py), [server ownership rules](../process/DELIVERY.md) | [counts-only data proof](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/data-preservation.json), [23-container preservation summary](https://github.com/smalvik/biocad-workspace/releases/download/v1.4.1/container-preservation-summary.json) |

Все labels источника/окружения/run_type должны соответствовать реальному запуску.
248 — outer regression checks; 222 — raw regression Allure, 26 Vitest отдельно;
stage/prod smoke добавляет 2 raw результата. Child RED 2 failed/GREEN 3 passed —
вложения sensitivity gate, не дополнительные headline проверки. Allure UI может
группировать повторные phase/history identities; raw count не обещает столько же
видимых строк. Проверки smoke/regression сейчас выполняют один набор с разными metadata.

Короткий walkthrough: вход → будущий интервал → employee lookup/карта → manual
confirm → свои брони/отмена → Mailpit локально → AI предложение/отдельное confirm
при доступном бесплатном провайдере → Allure/red.log/green.log. Сбои сервисов и
DB fault injection показывайте через изолированную регрессию, не останавливая production.
Реальный live AI без брони уже проверен отдельно; поведение AI-confirm с записью
подтверждено в настоящем Booking/PostgreSQL E2E при scripted provider.

Дальнейшая interview-подготовка WB-18 и in-product release-history WB-17 не закрыты
этим индексом. [Task WB-10](../tasks/WB-10.md), [current state](../context/CURRENT_STATE.md).
