"""add report analysis error message field

Revision ID: 20260309_02
Revises: 20260309_01
Create Date: 2026-03-09 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260309_02"
down_revision = "20260309_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("analysis_error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "analysis_error_message")
