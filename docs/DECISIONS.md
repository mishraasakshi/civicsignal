# Decision log

The main engineering decisions behind CivicSignal: what was decided, why, and what it cost.

---

## 1. A focused pilot: one campus, two roles, eight categories

- **Decision:** build for Amity University Lucknow hostels and campus facilities only, with two
  roles (`reporter` = student, `supervisor` = facilities staff) and 8 fixed categories
  (`water_plumbing`, `electrical`, `cleanliness`, `internet_wifi`, `furniture`, `mess_food`,
  `security`, `other`).
- **Why:** real users are reachable (classmates, a Google Form), the categories match how campus
  problems are actually handled, and a narrow scope can be finished, tested and evaluated
  honestly instead of building "everything for everyone".

## 2. Synthetic training data + a real test set (not NYC 311)

- **Decision:** generate 1,416 training complaints with LLMs on Groq in English, Hinglish and
  typo-heavy styles, and collect **real** student complaints only for testing.
- **Why:** public datasets such as NYC 311 have short operator-written labels ("Street Light
  Out") instead of how Indian students write ("tubelight khrb h"), so models trained on them look
  great and fail on real input. Keeping real data out of training gives an honest score.
- **Cost:** synthetic text is cleaner and narrower than real writing - which the evaluation then
  measured (see 3).

## 3. Multilingual embeddings over TF-IDF - decided on real data

- **Decision:** deploy `paraphrase-multilingual-MiniLM-L12-v2` embeddings + logistic regression.
- **Why:** TF-IDF scored slightly *higher* on synthetic validation (96.8-97.2 % vs 95.8 %) but
  much lower on genuine student complaints (55.2 % vs 65.5 %). The model was chosen on the real
  test set, because that is what users produce ([evaluation](evaluation.md)).
- **Cost:** a ~1 GB-RAM model in production (PyTorch), which ruled out 512 MB free hosting tiers.

## 4. The AI suggests, a person decides

- **Decision:** predictions below 50 % confidence are flagged for review; supervisors can always
  correct the category; status changes follow a fixed workflow enforced by the server.
- **Why:** with ~65 % accuracy on genuine complaints, silently trusting the model would misroute
  many complaints. Making uncertainty visible keeps the system useful and safe.

## 5. Similar-complaint search with stored embeddings instead of a vector database

- **Decision:** store each complaint's embedding (384 float32 values) in Postgres and rank by
  cosine similarity in NumPy. FAISS was used offline for exploration and clustering.
- **Why:** at campus scale (hundreds to thousands of complaints) a full scan takes milliseconds,
  needs no extra service or index to keep in sync, and works with any managed Postgres
  (no pgvector extension needed).
- **When to revisit:** tens of thousands of complaints -> pgvector or a FAISS index.

## 6. LLM work offline, not in the request path

- **Decision:** group summaries are generated offline (DBSCAN groups -> Groq via LangChain ->
  Pydantic-validated JSON, cached) and imported into the `group_insights` table.
- **Why:** no API key in the production container, no per-request LLM cost or latency, no
  failure mode when the LLM provider is down, and every summary can be checked before it is shown.

## 7. Security: cookie sessions, least privilege, refuse unsafe config

- **Decision:** JWT in an httpOnly cookie (no tokens in browser storage), bcrypt, rate limits on
  login and sign-up, strict CSP/HSTS, a `civic_readonly` database role limited to safe complaint
  columns, and start-up checks that refuse weak production secrets.
- **Why:** the app holds students' complaints and accounts; the common failure modes (stolen
  tokens via XSS, password guessing, over-privileged DB users, a forgotten default secret) are
  each blocked by a specific measure, and the read-only role is verified in CI.
- **Next:** the read-only role is the foundation for plain-English analytics (NL-to-SQL), where
  generated SQL can only ever read allowed columns.

## 8. One container on Azure Container Apps + Neon

- **Decision:** a single container (FastAPI serves the API, the built website and the model) on
  Azure Container Apps (Azure for Students, scale-to-zero, 1 replica), with Neon Postgres.
- **Why:** first-party cookies and no CORS between site and API; one trusted proxy hop for
  rate-limit IPs; free on a student plan.
- **What changed on the way:** Hugging Face Docker Spaces became paid; free no-card hosts offer
  512 MB RAM (the model needs ~1 GB); the student subscription allows only a few regions (East
  Asia was the closest one that runs Container Apps), blocks building images inside Azure (so the
  image is built locally and pushed), and its newer "Express" environments cannot pull private
  images (so a standard workload-profiles environment is used). Each constraint is handled in
  `scripts/deploy_azure.sh` and documented in [deployment.md](deployment.md).
