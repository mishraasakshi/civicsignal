# Deployment

CivicSignal runs as **one container** on **Azure Container Apps**: FastAPI serves both the API
(`/api/...`) and the built React website (everything else). The database is a managed
Postgres (**Neon**, free tier).

```
Browser ──https──> Container Apps ingress ──> container (FastAPI + website + AI model)
                                                └──> Neon Postgres (TLS, AWS us-east-1)
```

Why one container: the login cookie is first-party (no cross-site cookie settings), no CORS
between site and API, and only one proxy sits in front of the app, so `TRUSTED_PROXY_HOPS=1`
gives each visitor's real IP to the rate limiter.

## What goes where

| Where | What | Public? |
|---|---|---|
| GitHub repo | Everything (code, tests, docs, ML scripts) except data and `.env` | Yes |
| Azure Container Registry (private) | Only what runs: made by `scripts/export_container.sh` (no tests, no data, no `.env`) | No |
| Container Apps secrets | Database URLs, JWT secret | No |
| `~/.civicsignal/prod-secrets.env` | Local copy of those secrets (file mode 600, outside the repo) | No |
| Neon | Users, complaints, group summaries | No |

## 1. Database (Neon)

1. Create a project (any region; ours is AWS us-east-1).
2. In Neon's SQL editor, create the read-only role used by the future NL-to-SQL feature
   (no password needed here - the next step sets one):

   ```sql
   CREATE ROLE civic_readonly LOGIN;
   GRANT CONNECT ON DATABASE neondb TO civic_readonly;
   GRANT USAGE ON SCHEMA public TO civic_readonly;
   ```

   Migration 0003 then grants it only the safe complaint columns.
3. Make the production secrets without ever displaying them. The script asks for the Neon
   owner connection string with hidden input, gives `civic_readonly` a random password,
   checks both logins, makes a JWT secret and saves all three to
   `~/.civicsignal/prod-secrets.env` (mode 600):

   ```bash
   backend/venv/bin/python scripts/make_prod_secrets.py
   ```

## 2. Azure (one time)

1. Activate **Azure for Students** (no credit card; verify with your school email):
   https://azure.microsoft.com/free/students
2. Install and sign in to the CLI:

   ```bash
   brew install azure-cli
   az login
   ```

## 3. Deploy

Azure for Students subscriptions may only deploy to a few regions (`az policy assignment list`
shows them). The script uses **East Asia** (Hong Kong): allowed, runs Container Apps, and close
to students in India. Override with `LOCATION=<region> ./scripts/deploy_azure.sh`.

```bash
./scripts/deploy_azure.sh
```

The first run creates the resource group `civicsignal-rg`, a private container registry and the
Container Apps environment, then builds the image in Azure (about 10-15 minutes the first time)
and starts the app at `https://civicsignal.<environment-domain>.eastasia.azurecontainerapps.io`.
Run the same command again to ship a new version.

The container refuses to start if any secret is weak or missing (see
`backend/app/core/production_checks.py`) and runs database migrations at start-up.

Settings used: 1 vCPU, 2 GiB memory, 0-1 replicas (scales to zero when idle, never more than
one replica so the in-memory rate limiter sees every request). The registry is pulled with the
app's managed identity - no registry password exists.

## 4. First-time data (run on your own computer, pointed at Neon)

```bash
./scripts/with_prod_db.sh backend/venv/bin/python backend/scripts/create_supervisor.py --email you@example.com
./scripts/with_prod_db.sh backend/venv/bin/python backend/scripts/import_group_summaries.py
./scripts/with_prod_db.sh backend/venv/bin/python backend/scripts/check_readonly_role.py
```

## Cost and limits

- Container Apps has a monthly free allowance (CPU, memory and requests) that easily covers a
  demo. The container registry (Basic) costs about $5 a month, paid from the Azure for Students
  credit; old images are cleaned up automatically. Without a card on file nothing can be billed.
- When idle the app scales to zero; the first visit after that takes up to a minute while the
  container starts and the AI model loads.
- Logs: `az containerapp logs show -n civicsignal -g civicsignal-rg --follow`.
- Rate-limit counts live in memory: one instance, reset on restart.
- The app refuses to be shown inside other pages (clickjacking protection), so open it directly.
