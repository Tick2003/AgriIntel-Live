# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Dependency Builder
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# System packages needed for ML libraries (lightgbm, catboost)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned lockfile first (maximise layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime Image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

LABEL org.opencontainers.image.title="AgriIntel.in"
LABEL org.opencontainers.image.description="National Unified Agricultural Intelligence Stack"
LABEL org.opencontainers.image.source="https://github.com/Tick2003/AgriIntel-Live"
LABEL org.opencontainers.image.licenses="MIT"

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN addgroup --system agriintel && adduser --system --ingroup agriintel agriintel

WORKDIR /app

# Copy source code
COPY --chown=agriintel:agriintel . .

# Create required runtime directories
RUN mkdir -p data/run_manifests mlruns logs \
    && chown -R agriintel:agriintel data mlruns logs

USER agriintel

# Ports: 8501 = Streamlit UI, 8000 = FastAPI
EXPOSE 8501 8000

# Healthcheck — hits Streamlit's health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" \
    || exit 1

# Default: run the Streamlit app
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false"]
