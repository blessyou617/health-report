"""report payment state machine

Revision ID: 20260309_01
Revises: 
Create Date: 2026-03-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260309_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # report: add unlock field
    op.add_column("reports", sa.Column("is_unlocked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # report: normalize existing status values to new workflow states
    op.execute("UPDATE reports SET status = 'uploaded' WHERE status IN ('pending')")
    op.execute("UPDATE reports SET status = 'analyzing' WHERE status IN ('processing')")
    op.execute("UPDATE reports SET status = 'analysis_ready' WHERE status IN ('completed')")
    op.execute("UPDATE reports SET status = 'analysis_failed' WHERE status IN ('failed')")

    # payment: normalize legacy status to new statuses
    op.execute("UPDATE payments SET status = 'paid' WHERE status IN ('success')")
    op.execute("UPDATE payments SET status = 'refunded' WHERE status IN ('closed')")


def downgrade() -> None:
    # payment rollback mapping
    op.execute("UPDATE payments SET status = 'success' WHERE status IN ('paid')")
    op.execute("UPDATE payments SET status = 'closed' WHERE status IN ('refunded')")

    # report rollback mapping
    op.execute("UPDATE reports SET status = 'pending' WHERE status IN ('uploaded', 'questionnaire_submitted')")
    op.execute("UPDATE reports SET status = 'processing' WHERE status IN ('analyzing')")
    op.execute("UPDATE reports SET status = 'completed' WHERE status IN ('analysis_ready')")
    op.execute("UPDATE reports SET status = 'failed' WHERE status IN ('analysis_failed')")

    op.drop_column("reports", "is_unlocked")
