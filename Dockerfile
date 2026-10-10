# --- Stage 1: Build Frontend SPA ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend

# Copy frontend package manifests and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build assets
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python Backend & Single-Origin Production Host ---
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SENTINEL_ENV=production \
    SENTINEL_DB_PATH=/data/sentinel.db \
    SENTINEL_COOKIE_SECURE=false \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source
COPY backend/ ./backend/
COPY sample-data/ ./sample-data/

# Copy compiled frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Persistent volume directory for SQLite
RUN mkdir -p /data && chmod 777 /data
VOLUME ["/data"]

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start FastAPI application
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
