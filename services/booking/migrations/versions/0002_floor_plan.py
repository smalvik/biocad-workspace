"""Plan metadata belongs to a floor; fictional geometry is populated by explicit seed."""

from alembic import op

revision = "0002_floor_plan"
down_revision = "0001_booking_core"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE floors ADD COLUMN plan jsonb NOT NULL DEFAULT '{}'::jsonb")


def downgrade():
    op.execute("ALTER TABLE floors DROP COLUMN plan")
