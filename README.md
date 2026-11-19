# CivicSignal — AI-Powered Public Complaint Intelligence

> **Pilot Target:** Amity University Lucknow (Hostels & Campus Facilities)  
> **Portfolio Reference:** Version 2.0 Architectural Blueprint

CivicSignal is an AI-powered complaint intelligence platform designed to turn scattered campus complaints (in English, Romanized Hinglish, and informal student writing) into grouped, reviewable issues. It helps campus facilities staff resolve one root problem instead of managing ten separate tickets, while guaranteeing that **the AI only suggests; a human reviewer always decides**.

---

## Key Features

1. **Messy Text & Hinglish Extraction (LLM via Groq API)**
   - Extracts `category_hint`, `location_mention`, `urgency`, and clean English summaries from raw Hinglish complaints (*"bhai hostel A ke gate pe paani bhar gaya hai"*).
   - Guardrailed with Pydantic schemas and automatic fallback to classical classification if the LLM is unavailable.

2. **Trained Classical Classifier (Model A)**
   - TF-IDF baseline (word 1–2-grams + character 3–5-grams) + Logistic Regression / Linear SVM trained across 8 fixed campus categories.
   - Evaluated on a **real-only test set** collected from Amity students to measure the synthetic-to-real generalization gap.

3. **Semantic Similarity & Duplicate Intelligence (Model B)**
   - Dense vector embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) with in-process FAISS index.
   - Spatiotemporal composite ranking score:
     $$S = w_t \cdot \text{text\_similarity} + w_l \cdot \text{location\_similarity} + w_d \cdot \text{date\_proximity}$$
   - Explainable rationales (e.g., *"text 0.82 · 40 m apart · 2 days apart"*).

4. **Geospatial Hotspot Detection (Model C)**
   - Scikit-learn `DBSCAN` with `metric='haversine'` on coordinates in radians, clustering recurring issues on an interactive Leaflet map.

5. **Natural Language Analytics (NL-to-SQL via Groq)**
   - Translates supervisor questions (*"Which hostel had the most electrical complaints this month?"*) into SQL.
   - Executed using a **dedicated read-only PostgreSQL role** with AST validation via `sqlglot`, table allow-listing (no `users` table access), row limits, and statement timeouts.

---

## Tech Stack

| Layer | Tool | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 | Typed asynchronous REST APIs |
| **Database** | PostgreSQL 16, SQLAlchemy 2.x, Alembic | Relational storage & schema migrations |
| **Classical ML** | Scikit-learn, Pandas, NumPy | Category classification & DBSCAN clustering |
| **Vector Search** | Sentence-Transformers, FAISS (`faiss-cpu`) | Multilingual embeddings & nearest-neighbour search |
| **LLM Orchestration** | Groq API via LangChain (`langchain-groq`) | High-speed field extraction & NL-to-SQL |
| **Frontend** | React, Vite, TypeScript, Tailwind CSS, Leaflet | Modern responsive student & supervisor workspace |
| **Testing** | Pytest, FastAPI TestClient, Vitest, Playwright | Comprehensive unit, API, and E2E coverage |

---

## Repository Structure

```text
civicsignal/
├── frontend/                # React + Vite + TypeScript UI
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route controllers
│   │   ├── core/            # Config, security, dependencies
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic v2 validation schemas
│   │   ├── services/        # Business logic (complaints, groups, analytics)
│   │   ├── ml/              # Model loaders (classifier, embeddings, FAISS, DBSCAN)
│   │   ├── llm/             # Prompts, extraction, summaries, NL-to-SQL
│   │   └── db/              # Database session & seeders
│   ├── alembic/             # Schema migration scripts
│   ├── tests/               # Backend pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── ml/
│   ├── data_gen/            # Synthetic Hinglish complaint generator (Groq)
│   ├── data_prep/           # Dataset cleaning & reproducible splitting
│   ├── train_classifier.py  # Model A baseline & embedding training
│   ├── evaluate_classifier.py # Macro F1, precision/recall, confusion matrix
│   ├── build_index.py       # FAISS index builder
│   ├── hotspots.py          # DBSCAN geospatial clustering
│   └── artifacts/           # Model weights & indices (gitignored)
├── data/
│   ├── DATA_CARD.md         # Data card documenting sources & categories
│   ├── raw/                 # Raw complaints
│   ├── processed/           # Train / Val splits
│   └── real/                # Real student complaints template & test set
├── docs/
│   ├── architecture.md      # System architecture & lifecycle diagram
│   ├── api.md               # 14 REST endpoint contracts
│   ├── evaluation.md        # Reproducible model benchmark logs
│   └── DECISIONS.md         # Architecture Decision Records (ADRs) for interviews
├── scripts/                 # Setup, seed, and maintenance scripts
├── .github/workflows/ci.yml # GitHub Actions CI pipeline
├── docker-compose.yml       # Local PostgreSQL 16 + Backend container setup
├── .env.example             # Configuration template
└── README.md
```

---

## Run Locally

You need three things running, each in its own terminal tab:

```bash
docker compose up -d db          # 1. Postgres (once; keeps running in the background)
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
cd frontend && npm run lint && npm run build                 # frontend checks
```

Deployment (Azure Container Apps + Neon): see [docs/deployment.md](docs/deployment.md).

## Implementation Roadmap Checkpoints

- [x] **Phase 0 — Setup**: Repository scaffolding, docker-compose, pre-commit config, CI workflow, baseline tests.
- [ ] **Phase 1 — Data**: Synthetic Hinglish generator (Groq), de-duplication, dataset splits, data card.
- [ ] **Phase 2 — Classifier**: TF-IDF + Logistic Regression/SVM baseline vs embeddings, evaluation on real test set.
- [ ] **Phase 3 — Similarity & Hotspots**: Multilingual embeddings, FAISS index, composite scoring, DBSCAN.
- [ ] **Phase 4 — LLM Features**: Hinglish field extraction, issue-group summaries, NL-to-SQL with guardrails.
- [ ] **Phase 5 — Backend**: SQLAlchemy models, Alembic migrations, JWT auth, 14 REST endpoints, seed data.
- [ ] **Phase 6 — Frontend**: React + Vite + TypeScript interface with Leaflet maps and supervisor workspace.
- [ ] **Phase 7 — End-to-End Testing**: Section 17 demo scenario verification and security hardening.
- [ ] **Phase 8 — Deployment**: Render + Vercel deployment with read-only DB role.
- [ ] **Phase 9 — Portfolio Polish**: Demo video guide, pilot metrics script, and resume writeup.
