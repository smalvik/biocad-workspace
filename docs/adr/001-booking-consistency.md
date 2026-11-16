# ADR-001 — PostgreSQL owns booking consistency

Status: implemented in WB-02; native conflict arbitration and real race sensitivity
verification released in WB-11/WB-08, v1.4.1.

The application must reject two concurrent confirmations for one resource and
allow adjacent intervals. Availability shown to a browser or LLM can become stale.

Booking Service writes PostgreSQL `timestamptz` values. Alembic migration
`0001_booking_core` installs `btree_gist` and a nondeferrable exclusion constraint:
`space_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&`, limited to
`status='confirmed'`. An interval check prevents empty/reversed periods.

`UNIQUE(employee_id, idempotency_key)` and a SHA-256 fingerprint of the canonical
UTC request persist retry identity. `INSERT ... ON CONFLICT DO NOTHING RETURNING`
uses existing unique/exclusion arbitration. A skipped insert checks the stored key:
identical requests replay the same booking, changed requests conflict; otherwise the
slot conflict returns 409. This also applies after cancellation. Residual deadlock
victims get at most three complete transaction attempts with the same identity;
exhaustion returns retryable 503 without a committed booking/event.

The selected alternatives were an availability SELECT before INSERT and an
application lock. Neither alone protects multiple service instances or direct
database writers. GiST is the final guard; application validation still checks
authentication, resource existence, dedicated desks and periods.

Bookings and versioned outbox events commit together. The outbox was pending data
in WB-02; broker delivery and notification deduplication shipped in WB-07/v1.4.0.
Cancellation locks the booking row, checks ownership and emits at most one event.

Tests use real PostgreSQL over real HTTP, including 20 competing requests,
20 retries with one key, direct SQL rejection, adjacent intervals, injected outbox
failure and PostgreSQL/service restarts. No SQLite correctness claim is made.

WB-08 adds a real mutation sensitivity gate in a new owned child database: two HTTP
processes, observed PostgreSQL INSERT barrier, genuine failed single-winner oracle with
exclusion removed, then the exact restored constraint and passing identical oracle.
Actual [RED](../evidence/concurrency-red.md) / [GREEN](../evidence/concurrency-green.md).
It exposed native GiST INSERT deadlocks; separate WB-11 uses PostgreSQL ON CONFLICT
DO NOTHING plus bounded residual-deadlock retry, retaining all original constraints.
[Actual defect/fix evidence](../evidence/WB-11-booking-deadlock.md).

Consequence: PostgreSQL-specific DDL is intentional. Docker/database migrations
are required for local use. HTTP 409 is an expected outcome when a slot changes
between an availability read and confirmation.
