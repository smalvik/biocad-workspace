"""Initial authoritative Booking schema; PostgreSQL-only constraints are intentional."""

from alembic import op

revision = "0001_booking_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    # Keep migration DDL frozen instead of importing mutable application models.
    statements = [
        """CREATE TABLE employees (
            id varchar(32) PRIMARY KEY, full_name text NOT NULL, job_title text NOT NULL,
            department text NOT NULL, avatar_url text, fictional boolean NOT NULL DEFAULT true
        )""",
        """CREATE TABLE demo_accounts (
            employee_id varchar(32) PRIMARY KEY REFERENCES employees(id),
            username text NOT NULL UNIQUE, password_hash text NOT NULL
        )""",
        """CREATE TABLE auth_sessions (
            id uuid PRIMARY KEY, employee_id varchar(32) NOT NULL REFERENCES employees(id),
            csrf_token text NOT NULL, expires_at timestamptz NOT NULL
        )""",
        "CREATE INDEX auth_sessions_expiry_idx ON auth_sessions(expires_at)",
        "CREATE TABLE offices (id text PRIMARY KEY, name text NOT NULL)",
        """CREATE TABLE floors (
            id text PRIMARY KEY, office_id text NOT NULL REFERENCES offices(id),
            number integer NOT NULL, name text NOT NULL, UNIQUE(office_id, number)
        )""",
        """CREATE TABLE spaces (
            id text PRIMARY KEY, floor_id text NOT NULL REFERENCES floors(id),
            kind text NOT NULL CHECK (kind IN ('DESK', 'MEETING_ROOM')),
            desk_mode text, capacity integer NOT NULL CHECK (capacity > 0),
            zone text NOT NULL, layout jsonb NOT NULL,
            CHECK ((kind = 'DESK' AND desk_mode IS NOT NULL
                    AND desk_mode IN ('DEDICATED', 'FREEDESK'))
                OR (kind = 'MEETING_ROOM' AND desk_mode IS NULL))
        )""",
        "CREATE INDEX spaces_floor_idx ON spaces(floor_id)",
        """CREATE TABLE permanent_assignments (
            id uuid PRIMARY KEY, employee_id varchar(32) NOT NULL REFERENCES employees(id),
            space_id text NOT NULL REFERENCES spaces(id),
            valid_from timestamptz NOT NULL, valid_to timestamptz,
            CHECK (valid_to IS NULL OR valid_from < valid_to),
            CONSTRAINT assignments_no_overlap EXCLUDE USING gist (
                space_id WITH =, tstzrange(valid_from, valid_to, '[)') WITH &&
            )
        )""",
        """CREATE TABLE bookings (
            id uuid PRIMARY KEY, employee_id varchar(32) NOT NULL REFERENCES employees(id),
            space_id text NOT NULL REFERENCES spaces(id),
            start_at timestamptz NOT NULL, end_at timestamptz NOT NULL,
            status text NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled')),
            idempotency_key varchar(128) NOT NULL, request_hash varchar(64) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(), cancelled_at timestamptz,
            CHECK (start_at < end_at),
            CONSTRAINT bookings_employee_key_uniq UNIQUE(employee_id, idempotency_key),
            CONSTRAINT bookings_no_overlap EXCLUDE USING gist (
                space_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&
            ) WHERE (status = 'confirmed')
        )""",
        "CREATE INDEX bookings_space_start_idx ON bookings(space_id, start_at)",
        "CREATE INDEX bookings_employee_start_idx ON bookings(employee_id, start_at)",
        """CREATE TABLE outbox_events (
            id uuid PRIMARY KEY, aggregate_id uuid NOT NULL REFERENCES bookings(id),
            event_type text NOT NULL, schema_version integer NOT NULL DEFAULT 1,
            payload jsonb NOT NULL, occurred_at timestamptz NOT NULL, published_at timestamptz
        )""",
        "CREATE INDEX outbox_pending_idx ON outbox_events(occurred_at) WHERE published_at IS NULL",
    ]
    for statement in statements:
        op.execute(statement)


def downgrade():
    for table in (
        "outbox_events",
        "bookings",
        "permanent_assignments",
        "spaces",
        "floors",
        "offices",
        "auth_sessions",
        "demo_accounts",
        "employees",
    ):
        op.execute(f"DROP TABLE {table}")
    # btree_gist may be shared by other schemas; do not remove the extension.
