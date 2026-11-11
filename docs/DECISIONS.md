# Architecture Decision Log (ADR) — CivicSignal

This document records the architectural and engineering decisions made during the design and development of CivicSignal, complete with rationale, trade-offs, and interview talking points.

---

## ADR 001: Target Pilot Setting & Scoping (Amity University Lucknow)
- **Status:** Accepted (Phase 0)
- **Context:** Rather than building a generic municipal complaint system for an entire city, we chose Amity University Lucknow as our focused pilot environment.
- **Decision:**
  - 1 Organization (Amity University Lucknow).
  - 2 User Roles in MVP: `reporter` (students/staff) and `supervisor` (wardens/facilities managers). Department staff and multi-tenancy are deferred to post-pilot.
  - Fixed domain categories (8): `water_plumbing`, `electrical`, `cleanliness`, `internet_wifi`, `furniture`, `mess_food`, `security`, `other`.
- **Why this matters for interviews:**
  - Real users can be reached immediately via campus hostel WhatsApp groups and Google Forms.
  - Locations are strictly bounded (~15 landmarks: Hostel A–D, Library, Canteen, etc.), enabling precise geospatial validation.
  - Solves the classic junior mistake of trying to build "all features for everyone" and ending up with an untestable generic tool.

---

## ADR 002: Modular Monolith vs. Microservices
- **Status:** Accepted (Phase 0)
- **Context:** Selecting the high-level system architecture for solo development and rapid iteration.
- **Decision:** Built as a **modular monolith** with one FastAPI backend process coordinating business logic, classical ML inference, and LLM orchestration, communicating with PostgreSQL and React.
- **Why this matters for interviews:**
  - Avoids distributed systems failure modes (network latency, RPC serialization, dual writes, eventual consistency bugs).
  - Keeps deployment simple (single Docker container on Render, PostgreSQL database, React on Vercel).
  - Clean separation within code (`app/api`, `app/services`, `app/ml`, `app/llm`) ensures that if the system grows to city-scale, modules can be peeled off into independent microservices with minimal refactoring.

---

## ADR 003: Dropping NYC 311 Dataset (Avoiding Label Leakage)
- **Status:** Accepted (Phase 0)
- **Context:** NYC 311 Open Data is commonly used in tutorial projects for public service requests.
- **Decision:** Dropped NYC 311 for category classification in favor of domain-specific synthetic complaints (generated via Groq) + real Amity student complaints collected via Google Forms.
- **Why this matters for interviews:**
  - **Label Leakage:** In NYC 311, the `descriptor` field is almost always a short categorical label assigned by operators (e.g. "Street Light Out"), not raw human text. Training a model on this yields falsely inflated >98% accuracy that completely collapses on messy raw user text.
  - **Linguistic Reality:** Indian college students write complaints in casual English, Romanized Hinglish (*"bhai hostel A ke gate pe paani bhar gaya hai"*), and with heavy abbreviations/typos (*"contnuous leak"*). A model trained on New York City data cannot handle this domain.

---

## ADR 004: Vector Search with FAISS vs. pgvector / Managed Vector DBs
- **Status:** Accepted (Phase 0)
- **Context:** Choosing vector storage and similarity retrieval for complaint embeddings (`paraphrase-multilingual-MiniLM-L12-v2`).
- **Decision:** Use `faiss-cpu` (cosine / inner product on normalized dense vectors) indexed on disk, keyed by complaint ID.
- **Why this matters for interviews:**
  - At university scale (thousands to tens of thousands of complaints), FAISS running in-process delivers sub-millisecond retrieval with zero external dependencies and zero cloud vector DB cost (Pinecone/Qdrant).
  - Avoids requiring special PostgreSQL extensions (pgvector/PostGIS) which complicate local setups, test suites, and managed DB tier choices.

---

## ADR 005: Dual Database Roles for NL-to-SQL Security
- **Status:** Accepted (Phase 0)
- **Context:** Supervisors can ask arbitrary natural-language questions (e.g., *"How many water complaints came from Hostel A this week?"*) which an LLM translates into SQL.
- **Decision:**
  1. A dedicated restricted PostgreSQL role (`civic_readonly`) is created.
  2. The role is only granted `SELECT` privileges on an allow-list of operational tables (`complaints`, `locations`, `issue_groups`, `status_history`).
  3. The `users` table is strictly prohibited from the read-only role.
  4. AST parsing with `sqlglot` validates queries before execution, rejecting any statement that is not a single `SELECT` or contains disallowed tables, and enforcing an automatic `LIMIT 200` and statement timeout.
- **Why this matters for interviews:**
  - Demonstrates defense-in-depth against prompt injection and destructive SQL generation.
