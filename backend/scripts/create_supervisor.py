"""Create (or promote) a supervisor account.

Run from the project root:
    backend/venv/bin/python backend/scripts/create_supervisor.py --email someone@example.com

The password is typed in hidden (not shown on screen, not saved in shell history).
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import complaint  # noqa: E402,F401
from app.models.user import User  # noqa: E402
from app.schemas.auth import RegisterIn  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("New supervisor password (min 8 characters, hidden): ")
    if password != getpass.getpass("Type it again: "):
        sys.exit("Passwords do not match - nothing changed.")
    try:
        data = RegisterIn(email=args.email, password=password)  # same rules as sign-up
    except ValueError as e:
        sys.exit(f"Invalid input: {e}")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == data.email))
        if user is None:
            user = User(email=data.email, hashed_password=hash_password(data.password), role="supervisor")
            db.add(user)
            action = "Created"
        else:
            user.role = "supervisor"
            user.hashed_password = hash_password(data.password)
            action = "Promoted"
        db.commit()
        print(f"{action} supervisor: {data.email} (id {user.id})")


if __name__ == "__main__":
    main()
