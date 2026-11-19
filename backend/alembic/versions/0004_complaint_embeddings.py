"""complaints.embedding - stored text embeddings for "similar complaints"

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 384 float32 numbers per complaint (1.5 KB). Not granted to the read-only role.
    op.add_column("complaints", sa.Column("embedding", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("complaints", "embedding")
