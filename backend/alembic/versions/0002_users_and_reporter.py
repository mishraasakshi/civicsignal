"""users table + complaints.reporter_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    with op.batch_alter_table("complaints") as batch:  # batch mode also works on SQLite
        batch.add_column(sa.Column("reporter_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_complaints_reporter_id_users", "users", ["reporter_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_complaints_reporter_id", ["reporter_id"])


def downgrade() -> None:
    with op.batch_alter_table("complaints") as batch:
        batch.drop_index("ix_complaints_reporter_id")
        batch.drop_constraint("fk_complaints_reporter_id_users", type_="foreignkey")
        batch.drop_column("reporter_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
