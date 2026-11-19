"""Check what the read-only database role can and cannot see.

Run from the project root (after `alembic upgrade head`):
    backend/venv/bin/python backend/scripts/check_readonly_role.py

Connects AS civic_readonly (DATABASE_READONLY_URL in .env) and prints PASS/FAIL for each rule.
Only counts and permission errors are printed - never any row data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from app.core.config import settings  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.exc import ProgrammingError  # noqa: E402


def readonly_url() -> str:
    url = settings.DATABASE_READONLY_URL
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url.removeprefix("postgresql://")
    return url


def allowed(conn, sql: str) -> bool:
    try:
        with conn.begin_nested():
            conn.execute(text(sql))
        return True
    except ProgrammingError:  # permission denied
        return False


def main() -> None:
    engine = create_engine(readonly_url())
    checks = [
        (
            "can read complaint text/category/status",
            "SELECT count(id), count(text), count(status) FROM complaints",
            True,
        ),
        ("cannot read complaints.reporter_id", "SELECT reporter_id FROM complaints LIMIT 1", False),
        ("cannot SELECT * (would include reporter_id)", "SELECT * FROM complaints LIMIT 1", False),
        ("cannot read users table", "SELECT count(*) FROM users", False),
        ("cannot read alembic_version", "SELECT count(*) FROM alembic_version", False),
        ("cannot insert complaints", "INSERT INTO complaints (text) VALUES ('x')", False),
        ("cannot update complaints", "UPDATE complaints SET status = status WHERE false", False),
        ("cannot delete complaints", "DELETE FROM complaints WHERE false", False),
    ]
    failures = 0
    with engine.connect() as conn:
        for name, sql, should_work in checks:
            ok = allowed(conn, sql) == should_work
            failures += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {name}")
        conn.rollback()
    print(
        "\nAll good: the read-only role follows least privilege."
        if not failures
        else f"\n{failures} check(s) FAILED"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
