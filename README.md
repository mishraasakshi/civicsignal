# CivicSignal — AI campus complaint intelligence

[![CI](https://github.com/mishraasakshi/civicsignal/actions/workflows/ci.yml/badge.svg)](https://github.com/mishraasakshi/civicsignal/actions/workflows/ci.yml)

**Live demo:** https://civicsignal.wittycliff-03d73af7.eastasia.azurecontainerapps.io
<sub>(sleeps when idle - the first visit can take up to a minute to wake up)</sub>

Students at Amity University Lucknow report hostel and campus problems the way they talk:
*"tubelight khrb h"*, *"B block geyser kharab hai, garam paani nahi aa raha"*, *"wifi is dead
again at night"*. CivicSignal turns those messy, multilingual complaints into a clean queue for
the facilities team:

- **Students** submit a complaint and follow it through *Submitted → Under Review → In Progress → Resolved*.
- **An AI model** reads English, Hindi and Hinglish and suggests one of 8 categories. Unsure
  predictions (confidence below 50 %) are flagged for a human.
- **Supervisors** review, re-categorise and update complaints, and see **repeated problems**:
  groups of similar complaints with an AI-written summary and a suggested next step.

> The AI only suggests - a person always decides.

---

## What's inside

| Area | What was built |
| :--- | :--- |
| **Data** | 1,416 synthetic complaints generated with LLMs on Groq (8 categories; English, Hinglish, short, typo-heavy styles), plus a **real test set of 98 anonymous student complaints** collected with a Google Form and never used for training ([data card](docs/data_card.md)) |
| **Classifier** | Multilingual sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) + logistic regression, chosen over a TF-IDF baseline because it generalises better to real student writing |
| **Repeated problems** | DBSCAN clustering on the embeddings groups similar complaints; an LLM (via LangChain + Groq) writes a validated JSON summary per group (title, urgency, suggested action) |
| **Similar-complaint search** | Embeddings stored per complaint; cosine search API for supervisors (finds Hinglish matches for English queries) |
| **Backend** | FastAPI, SQLAlchemy 2, Alembic migrations, PostgreSQL 16, 11 REST endpoints |
| **Frontend** | React 19, Vite, TypeScript; student page, supervisor dashboard, progress tracker |
| **Security** | httpOnly session cookie (no tokens in browser storage), bcrypt, role-based access, login and sign-up rate limits, strict security headers (CSP, HSTS, no framing), a least-privilege read-only database role, start-up checks that refuse weak production secrets |
| **Quality** | 74 backend tests (pytest) + 25 frontend tests (Vitest); GitHub Actions runs lint, formatting, tests, a real-Postgres migration and a permission check on every push |
| **Deployment** | One container (website + API + AI model) on **Azure Container Apps**, scale-to-zero; managed Postgres on **Neon** ([deployment guide](docs/deployment.md)) |

## Results (real student complaints)

| Model | Synthetic validation | Real, genuine (58) | All real (98) |
| :--- | :---: | :---: | :---: |
| TF-IDF + logistic regression (baseline) | 96.8 % | 55.2 % | 67.3 % |
| **Multilingual MiniLM + logistic regression (deployed)** | 95.8 % | **65.5 %** | **76.5 %** |
| Human agreement (students vs. our labelling rules) | - | 84.5 % | - |

- Accuracy on synthetic data looks excellent, but real student writing is much harder. Measuring
  this **synthetic-to-real gap** honestly drove the switch from TF-IDF to multilingual embeddings
  (+10 points on genuine complaints).
- Grouping: 9 groups covering 30 of the 98 real complaints, 83 % purity (share of each group in
  its main category); the other 68 were one-off problems.

All numbers come from the scripts in `ml/models/` and are saved in `ml/artifacts/*_metrics.json`.

## Architecture

```
Browser ──https──> Azure Container Apps ──> one container
                                             ├─ FastAPI: /api/...  (auth, complaints, AI)
                                             ├─ React website (built, served by FastAPI)
                                             └─ MiniLM model + classifier (loaded at start)
                                                      │
                                                      └──TLS──> Neon PostgreSQL
                                                                 (app role + read-only role)

Offline (on a laptop): data generation, training, evaluation, clustering and LLM group
summaries -> results imported into the database with backend/scripts/.
```

One container keeps the login cookie first-party (no cross-site cookie settings, no CORS between
site and API) and keeps hosting free on a student plan.

## Repository structure

```text
backend/
  app/api/        REST endpoints (auth, classify, complaints, similar, insights)
  app/core/       config, security, rate limiting, security headers, production checks
  app/ml/         classifier + similar-complaint search
  app/models/     SQLAlchemy models        app/schemas/  Pydantic schemas
  alembic/        database migrations      scripts/      admin and data-import scripts
  tests/          pytest suite
frontend/src/     React app (pages, components, tests)
ml/
  data_gen/       synthetic complaint generator (Groq)
  data_prep/      real test-set cleaning
  models/         training, evaluation, clustering, LLM summaries
  artifacts/      metrics (model files are git-ignored)
deploy/container/ Dockerfile + start script for production
scripts/          dev servers, container export, Azure deploy
docs/             data card, deployment guide, decisions
```

## Run locally

You need three things running, each in its own terminal tab:

```bash
docker compose up -d db          # 1. Postgres (keeps running in the background)
./scripts/dev_backend.sh         # 2. API on http://localhost:8000 (docs: /docs)
./scripts/dev_frontend.sh        # 3. Website on http://localhost:5173
```

First-time setup:

```bash
cp .env.example .env                                         # then fill in the values
backend/venv/bin/alembic -c backend/alembic.ini upgrade head # create / update tables
backend/venv/bin/python backend/scripts/create_supervisor.py --email you@example.com
backend/venv/bin/python backend/scripts/backfill_embeddings.py     # "similar complaints" for older rows
backend/venv/bin/python backend/scripts/import_group_summaries.py  # AI group summaries into the DB
cd frontend && npm install
```

Checks:

```bash
backend/venv/bin/python -m pytest backend -q                 # backend tests
backend/venv/bin/python backend/scripts/check_readonly_role.py
cd frontend && npm run lint && npm test && npm run build     # frontend checks
```

## Privacy

Real survey responses stay on the developer's machine and are git-ignored; names and room
numbers were removed before evaluation. The repository and the deployed container contain no
student data.

## Roadmap

- [x] Synthetic + real data, data card
- [x] Classifier (TF-IDF baseline vs. multilingual embeddings), evaluation on real complaints
- [x] Similar-complaint search and repeated-problem groups with LLM summaries
- [x] Backend, frontend, security hardening, tests, CI
- [x] Deployment on Azure Container Apps + Neon
- [ ] Plain-English analytics for supervisors (NL-to-SQL on the read-only role)
- [ ] Extracting location and urgency from Hinglish text with an LLM
- [ ] Email-based password reset
