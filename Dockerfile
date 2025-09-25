# ---- Builder Stage ----
FROM python:3.13.7-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from official image
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

WORKDIR /app

# Set environment variables for the application
ENV JWT_SECRET_KEY="secret_jwt_key"

# Copy requirements first (better caching)
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-cache

# Copy in the rest of the app
COPY ./app ./app
COPY ./migrations ./migrations
COPY ./alembic.ini ./alembic.ini

# Prepare data dirs
RUN mkdir -p /app/uploads /app/logs

# ---- Runtime Stage ----
FROM python:3.13.7-slim

# Install runtime tools needed by entrypoint and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -ms /bin/bash appuser

WORKDIR /app

# Copy uv + installed deps from builder
COPY --from=builder /bin/uv /bin/uvx /bin/
COPY --from=builder /app /app
COPY ./scripts ./scripts
RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["./scripts/entrypoint.sh"]

USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI via uvicorn
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
