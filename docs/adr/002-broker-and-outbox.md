# ADR-002 — RabbitMQ outbox and worker-owned notification inbox

Status: implemented for WB-06/WB-07; final WB-07 integration/release evidence pending.

Booking + PostgreSQL remain the only confirmed-booking authority. Assistant uses bounded
RabbitMQ request/reply to the same authenticated Booking handlers. Booking confirmation
and its outbox event commit in one PostgreSQL transaction; no broker/SMTP call occurs in
the HTTP transaction. A background publisher claims rows with `FOR UPDATE SKIP LOCKED`,
keeps creation before cancellation for each aggregate, and marks publication only after
a mandatory persistent RabbitMQ publisher confirmation. Unknown outcomes may republish
the same stable event UUID; the source fact remains durable.

Fictional recipient addresses are deterministically derived from the authenticated demo
employee ID in the reserved `example.test` domain; the fictional office address comes
from the canonical fixture. New events freeze these fields. No new Booking migration is
needed, keeping the old Alembic-bearing image startable after rollback.

Notification Worker is a separate Python image/process, consuming a durable queue from
the versioned topic exchange. It receives only the necessary frozen notification fields,
not DB/session/LLM credentials. Its private persistent SQLite WAL inbox is sufficient for
the single-worker demo: Booking never reads that volume, Worker never accesses Booking
PostgreSQL. ACK follows inbox commit, so worker/broker restarts re-admit the same event
without another job. SMTP delivery and completed-event deduplication live in that inbox.
SQLite serializes sending; pending jobs retry with a bounded SMTP timeout and exponential
delay capped at60 seconds, preserving order per booking while other bookings can progress.
Pending jobs are retained through outages, not discarded after an arbitrary attempt count.
Invalid contracts go to a separate durable dead-letter queue.

SMTP and the local delivery transaction cannot commit atomically. A process loss after
Mailpit accepts DATA but before the local sent-state commit can cause a retry/duplicate.
Stable Message-ID helps tracing but is not assumed to make SMTP idempotent. We guarantee
deduplication of durably completed events and normal broker/restart replay, not exactly-once
external SMTP. Avoid claiming a stronger property than the protocol provides.

Alternatives: synchronous SMTP in Booking would couple availability and lose the event on
process failure; direct Worker SQL access to Booking would violate ownership; shared
PostgreSQL dedup schema would require additional credentials/role management for this
single-instance demo. Horizontal workers on different hosts require migrating the private
inbox to an appropriate shared transactional store, not copying separate SQLite files.

Delivery manifest schema2 adds notification/runtime-test images; schema1 seven-image
releases remain valid for backup/rollback. Legacy rollback stops the worker, disables the
publisher and preserves the notification volume and unchanged Booking schema. Never
restore the booking database automatically or delete delivery state during image rollback.

Validation: worker template/escaping/dedup/concurrency/restart/SMTP retry unit tests;
real PostgreSQL publisher row locking/confirm-failure tests; full disposable-stack broker
and SMTP outage/recovery/replay phases; real Mailpit assertions from desktop/mobile
booking/cancellation E2E. Actual commands/results belong in the WB-07 evidence notes.

Primary sources: [RabbitMQ acknowledgements and confirms](https://www.rabbitmq.com/docs/confirms),
[aio-pika publication semantics](https://docs.aio-pika.com/_modules/aio_pika/exchange.html),
[Mailpit integration testing](https://mailpit.axllent.org/docs/integration/).
