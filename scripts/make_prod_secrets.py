"""Make the production secrets without ever showing them.

- asks for the Neon owner connection string with hidden input
- gives civic_readonly a fresh random password and checks it can log in
- makes a fresh JWT secret
- saves everything to ~/.civicsignal/prod-secrets.env (only you can read it, outside the repo)
- prints only names, never values
"""

import getpass
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import psycopg2
from psycopg2 import sql

OUT_DIR = Path.home() / ".civicsignal"
OUT = OUT_DIR / "prod-secrets.env"

print("\nCopy the Neon connection string first (Neon -> Connect -> copy icon).")
url = getpass.getpass("Paste it HERE (nothing will show), then press Enter: ").strip()

if not url.startswith("postgresql://neondb_owner:") or "neon.tech" not in url:
    sys.exit("\nThat is not the Neon owner connection string. Nothing was changed. Run me again.")

parts = urlsplit(url)
ro_password = secrets.token_urlsafe(24)

conn = psycopg2.connect(url, connect_timeout=20)
with conn, conn.cursor() as cur:
    cur.execute(
        sql.SQL("ALTER ROLE civic_readonly WITH PASSWORD {}").format(sql.Literal(ro_password))
    )
conn.close()
print("OK  owner login works, civic_readonly got a new password")

host = parts.hostname + (f":{parts.port}" if parts.port else "")
ro_url = urlunsplit(
    (
        parts.scheme,
        f"civic_readonly:{quote(ro_password, safe='')}@{host}",
        parts.path,
        parts.query,
        parts.fragment,
    )
)

conn = psycopg2.connect(ro_url, connect_timeout=20)
with conn, conn.cursor() as cur:
    cur.execute("select current_user")
    assert cur.fetchone()[0] == "civic_readonly"
conn.close()
print("OK  civic_readonly can log in with the new password")

values = {
    "DATABASE_URL": url,
    "DATABASE_READONLY_URL": ro_url,
    "JWT_SECRET_KEY": secrets.token_urlsafe(48),
}

OUT_DIR.mkdir(mode=0o700, exist_ok=True)
os.chmod(OUT_DIR, 0o700)
fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    for name, value in values.items():
        f.write(f"{name}={value}\n")

subprocess.run(
    "pbcopy", input=b"", check=False
)  # don't leave the connection string on the clipboard
print(f"OK  saved {', '.join(values)} to ~/.civicsignal/prod-secrets.env (values not shown)")
print("\nAll done.")
