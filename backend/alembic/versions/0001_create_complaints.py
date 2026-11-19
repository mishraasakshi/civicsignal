"""create complaints table

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200)),
        sa.Column("urgency_reported", sa.String(10)),
        sa.Column("predicted_category", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="Submitted"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaints_category", "complaints", ["category"])
    op.create_index("ix_complaints_status", "complaints", ["status"])


def downgrade() -> None:
    op.drop_index("ix_complaints_status", table_name="complaints")
    op.drop_index("ix_complaints_category", table_name="complaints")
    op.drop_table("complaints")
