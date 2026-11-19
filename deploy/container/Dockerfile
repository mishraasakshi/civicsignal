# CivicSignal: one container serves the website AND the API (deployed on Azure Container Apps).
# Built from the clean folder made by scripts/export_container.sh (no data, no tests, no secrets).

# ---- 1) build the website ----
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- 2) the app ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/ml/.hf_cache \
    ENVIRONMENT=production \
    FRONTEND_DIST=/app/frontend_dist \
    TRUSTED_PROXY_HOPS=1 \
    PORT=8080

# Run as an unprivileged user, never root
RUN useradd --create-home --uid 1000 user
WORKDIR /app

# Python packages (CPU-only PyTorch: much smaller, no GPU needed)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r backend/requirements.txt

# Download the multilingual embedding model once, at build time (fast, offline start-up)
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}', device='cpu')"

COPY backend/ backend/
COPY ml/artifacts/embed_minilm.joblib ml/artifacts/embed_minilm.joblib
COPY --from=web /web/dist /app/frontend_dist
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh && chown -R user:user /app
ENV HF_HUB_OFFLINE=1
USER user

EXPOSE 8080
CMD ["/app/start.sh"]
