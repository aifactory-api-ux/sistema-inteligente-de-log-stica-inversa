# =============================================================================
# Backend Dockerfile - Multi-stage build for Sistema Inteligente de Logistica Inversa
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and prepare environment
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Production image with non-root user
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    USER=appuser

COPY --chown=appuser:appgroup . .

RUN mkdir -p /home/appuser/uploads /home/appuser/qrcodes && \
    chown -R appuser:appgroup /home/appuser

USER appuser

EXPOSE 21001

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:21001/health/live')"

CMD ["sh", "-c", "python migrations/run_migrations.py && uvicorn src.main:app --host 0.0.0.0 --port 21001"]
