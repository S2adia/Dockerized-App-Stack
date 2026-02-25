# ---- builder stage ----
FROM python:3.12-slim AS builder

# Workdir for building wheels
WORKDIR /build

# Copy dependency list
COPY requirements.txt .

# Build wheels for all dependencies into /wheels
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# ---- runtime stage ----
FROM python:3.12-slim

# Minimal tools for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy prebuilt wheels from builder
COPY --from=builder /wheels /wheels

# Install dependencies from wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY app.py .

# Drop privileges
USER appuser

EXPOSE 8080

# Healthcheck hits /health
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://localhost:8080/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
