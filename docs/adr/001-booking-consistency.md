# ADR-001 — PostgreSQL owns booking consistency

Status: implemented in WB-02; local verification recorded in the WB-02 evidence note.

The application must reject two concurrent confirmations for one resource and
allow adjacent intervals. Availability shown to a browser or LLM can become stale.

Booking Service writes PostgreSQL `timestamptz` values. Alembic migration
`0001_booking_core` installs `btree_gist` and a nondeferrable exclusion constraint:
`space_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&`, limited to
`status='confirmed'`. An interval check prevents empty/reversed periods.

`UNIQUE(employee_id, idempotency_key)` and a SHA-256 fingerprint of the canonical
UTC request persist retry identity. On either unique or exclusion failure, the
transaction rolls back and checks the stored key: identical requests replay the
same booking, changed requests conflict. This also applies after cancellation.

The selected alternatives were an availability SELECT before INSERT and an
application lock. Neither alone protects multiple service instances or direct
database writers. GiST is the final guard; application validation still checks
authentication, resource existence, dedicated desks and periods.

Bookings and versioned outbox events commit together. The outbox is pending data
in WB-02; broker delivery and notification deduplication belong to WB-07.
Cancellation locks the booking row, checks ownership and emits at most one event.

Tests use real PostgreSQL over real HTTP, including 20 competing requests,
20 retries with one key, direct SQL rejection, adjacent intervals, injected outbox
failure and PostgreSQL/service restarts. No SQLite correctness claim is made.

Consequence: PostgreSQL-specific DDL is intentional. Docker/database migrations
are required for local use. HTTP 409 is an expected outcome when a slot changes
between an availability read and confirmation.
