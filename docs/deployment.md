# Deployment

CivicSignal runs as **one container** on Hugging Face Spaces (free CPU tier): FastAPI serves
both the API (`/api/...`) and the built React website (everything else). The database is a
managed Postgres (Neon, free tier).

```
Browser ──https──> Hugging Face proxy ──> Space container (FastAPI + website + AI model)
                                                   └──> Neon Postgres (TLS)
```

Why one container: the login cookie is first-party (no cross-site cookie settings), no CORS,
and only one proxy sits in front of the app, so `TRUSTED_PROXY_HOPS=1` gives each visitor's
real IP to the rate limiter.

## What goes where

| Where | What | Public? |
|---|---|---|
| GitHub repo | Everything (code, tests, docs, ML scripts) except data and `.env` | Yes |
| Space repo | Only what runs: made by `scripts/export_space.sh` (no tests, no data, no history) | Yes |
| Space **secrets** | Database URLs, JWT secret | No |
| Neon | Users, complaints, group summaries | No |

## 1. Database (Neon)

1. Create a project (region close to your users) and copy the **pooled connection string**.
   It looks like `postgresql://USER:PASSWORD@HOST/neondb?sslmode=require`.
2. In Neon's SQL editor, create the read-only role used by the future NL-to-SQL feature
   (choose your own strong password):

   ```sql
   CREATE ROLE civic_readonly LOGIN PASSWORD '<strong password>';
   GRANT CONNECT ON DATABASE neondb TO civic_readonly;
   GRANT USAGE ON SCHEMA public TO civic_readonly;
   ```

   Migration 0003 then grants it only the safe complaint columns.

## 2. Space secrets

In the Space: **Settings → Variables and secrets → New secret**.

| Secret | Value |
|---|---|
| `DATABASE_URL` | Neon connection string (main user) |
| `DATABASE_READONLY_URL` | Same host, user `civic_readonly` and its password |
| `JWT_SECRET_KEY` | 48+ random characters: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | `["https://<owner>-<space>.hf.space"]` |

The container refuses to start if any of these are weak or missing (see
`backend/app/core/production_checks.py`). Migrations run automatically at start-up.

## 3. Publish the code to the Space

```bash
./scripts/export_space.sh ../civicsignal-space     # clean folder
cd ../civicsignal-space && git push                 # into the Space's git repo
```

The Space builds the Docker image (about 10 minutes the first time) and starts it.

## 4. First-time data (run on your own computer, pointed at Neon)

```bash
DATABASE_URL='<neon url>' backend/venv/bin/python backend/scripts/create_supervisor.py --email you@example.com
DATABASE_URL='<neon url>' backend/venv/bin/python backend/scripts/import_group_summaries.py
```

## Limits of the free tier

- The Space sleeps after 48 hours without visitors; the first visit then takes about a minute.
- Rate-limit counts live in memory: one container, reset on restart.
- Open the app at `https://<owner>-<space>.hf.space` (the app refuses to be shown inside other
  pages, including the huggingface.co Space page, to prevent clickjacking).
