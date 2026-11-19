"""Read-only role: least privilege (no users table, no reporter_id)

The civic_readonly role is for the future "ask the data in plain English" (NL-to-SQL)
feature, where an AI writes SQL. It must never see accounts or who wrote a complaint.

Before: init_postgres.sql gave it SELECT on EVERY table created later (users included).
After:  it can SELECT only the safe columns of complaints. New tables are no longer
        shared with it automatically; each one must be granted on purpose.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE = "civic_readonly"

# Everything about a complaint except reporter_id (who wrote it)
SAFE_COMPLAINT_COLUMNS = (
    "id, text, location, urgency_reported, predicted_category, confidence, "
    "needs_review, category, status, created_at, updated_at"
)


def _role_exists() -> bool:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":  # e.g. SQLite in tests: no roles
        return False
    return bind.execute(sa.text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": ROLE}).scalar() is not None


def upgrade() -> None:
    if not _role_exists():
        return
    # 1) stop sharing future tables automatically
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM {ROLE}")
    # 2) take away everything it has now (users, alembic_version, complaints)
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {ROLE}")
    # 3) give back only the safe complaint columns
    op.execute(f"GRANT SELECT ({SAFE_COMPLAINT_COLUMNS}) ON complaints TO {ROLE}")


def downgrade() -> None:
    if not _role_exists():
        return
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {ROLE}")
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {ROLE}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {ROLE}")
