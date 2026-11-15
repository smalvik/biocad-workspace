"""Durable per-user rate windows and conservative lifetime LLM spend reservations."""

from alembic import op

revision = "0003_assistant_limits"
down_revision = "0002_floor_plan"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE assistant_rate_windows (
            employee_id varchar(32) NOT NULL REFERENCES employees(id),
            minute_at timestamptz NOT NULL,
            requests integer NOT NULL CHECK (requests >= 0),
            PRIMARY KEY (employee_id, minute_at)
        )
    """)
    op.execute("""
        CREATE TABLE assistant_budgets (
            epoch varchar(64) PRIMARY KEY,
            reserved_micro_usd bigint NOT NULL DEFAULT 0 CHECK (reserved_micro_usd >= 0)
        )
    """)
    op.execute("""
        CREATE TABLE assistant_spend_reservations (
            id uuid PRIMARY KEY,
            employee_id varchar(32) NOT NULL REFERENCES employees(id),
            epoch varchar(64) NOT NULL REFERENCES assistant_budgets(epoch),
            reserved_micro_usd bigint NOT NULL CHECK (reserved_micro_usd > 0),
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)


def downgrade():
    op.execute("DROP TABLE assistant_spend_reservations")
    op.execute("DROP TABLE assistant_budgets")
    op.execute("DROP TABLE assistant_rate_windows")
