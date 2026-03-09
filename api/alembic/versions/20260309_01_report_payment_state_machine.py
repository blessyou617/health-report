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

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    payment_columns = {column["name"] for column in inspector.get_columns("payments")}

    # payment: ensure legacy schema is migrated to normalized columns first
    with op.batch_alter_table("payments") as batch_op:
        if "order_id" in payment_columns and "order_no" not in payment_columns:
            batch_op.alter_column("order_id", new_column_name="order_no")
        if "pay_type" in payment_columns and "provider" not in payment_columns:
            batch_op.alter_column(
                "pay_type",
                new_column_name="provider",
                existing_type=sa.String(length=32),
                server_default="wechat",
                nullable=False,
            )
        if "transaction_id" in payment_columns and "provider_txn_id" not in payment_columns:
            batch_op.alter_column("transaction_id", new_column_name="provider_txn_id")

        if "provider" not in payment_columns and "pay_type" not in payment_columns:
            batch_op.add_column(sa.Column("provider", sa.String(length=32), nullable=False, server_default="wechat"))
        if "provider_txn_id" not in payment_columns and "transaction_id" not in payment_columns:
            batch_op.add_column(sa.Column("provider_txn_id", sa.String(length=64), nullable=True))

    op.execute("UPDATE payments SET provider = 'wechat' WHERE provider IS NULL OR provider = ''")

    # payment: normalize legacy status to new statuses
    op.execute("UPDATE payments SET status = 'paid' WHERE status IN ('success')")
    op.execute("UPDATE payments SET status = 'refunded' WHERE status IN ('closed')")


def downgrade() -> None:
    # payment rollback mapping
    op.execute("UPDATE payments SET status = 'success' WHERE status IN ('paid')")
    op.execute("UPDATE payments SET status = 'closed' WHERE status IN ('refunded')")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    payment_columns = {column["name"] for column in inspector.get_columns("payments")}

    with op.batch_alter_table("payments") as batch_op:
        if "provider_txn_id" in payment_columns and "transaction_id" not in payment_columns:
            batch_op.alter_column("provider_txn_id", new_column_name="transaction_id")
        if "provider" in payment_columns and "pay_type" not in payment_columns:
            batch_op.alter_column(
                "provider",
                new_column_name="pay_type",
                existing_type=sa.String(length=32),
            )
        if "order_no" in payment_columns and "order_id" not in payment_columns:
            batch_op.alter_column("order_no", new_column_name="order_id")

    # report rollback mapping
    op.execute("UPDATE reports SET status = 'pending' WHERE status IN ('uploaded', 'questionnaire_submitted')")
    op.execute("UPDATE reports SET status = 'processing' WHERE status IN ('analyzing')")
    op.execute("UPDATE reports SET status = 'completed' WHERE status IN ('analysis_ready')")
    op.execute("UPDATE reports SET status = 'failed' WHERE status IN ('analysis_failed')")

    op.drop_column("reports", "is_unlocked")
