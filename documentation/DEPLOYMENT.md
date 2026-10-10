# Sentinel — Deployment & Production Guide

This guide details running Sentinel in local development and production environments using Docker and persistent SQLite storage.

---

## 1. Single-Origin Production Deployment Architecture

In production, Sentinel runs as a single-origin container:
- The React TypeScript frontend is compiled into optimized static assets (`dist/`).
- FastAPI serves API routes under `/api/v1` and serves the frontend static SPA directly at the root `/`.
- Client-side routes are routed back to `index.html`.
- No separate Nginx container is required, simplifying resource requirements and single-port hosting.

```
                      Client Browser
                            |
                   HTTPS Port 443 / 8000
                            v
          +------------------------------------+
          |       Sentinel Docker Container    |
          |  (FastAPI + Static SPA + Engine)   |
          +-----------------+------------------+
                            |
                     Persistent Volume
                      (/data/sentinel.db)
```

---

## 2. Docker & Compose Quickstart

### Using Docker Compose (Recommended)

1. Clone or download the repository.
2. Ensure Docker and Docker Compose are installed.
3. Start the container:
   ```bash
   docker compose up --build -d
   ```
4. Access the application in your browser:
   ```
   http://localhost:8000
   ```
5. View container logs:
   ```bash
   docker compose logs -f
   ```
6. Stop the container:
   ```bash
   docker compose down
   ```

### Important Storage Notice: SQLite Volume Persistence
> **CRITICAL:** In Docker, SQLite database files will be lost if stored on an ephemeral container layer. Sentinel mounts `/data` to a persistent named volume (`sentinel_data`).
> SQLite is designed for single-instance prototype deployments. If scaling across multiple worker instances, migrate the SQLAlchemy engine to PostgreSQL.

---

## 3. Local Development Setup (Without Docker)

### Backend (Python 3.10+)
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   API docs will be available at `http://localhost:8000/docs`.

### Frontend (Node 18+)
1. In a separate terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Access Vite at `http://localhost:5173`. Requests to `/api` are automatically proxied to port 8000.

---

## 4. Production Environment Variables Reference

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SENTINEL_ENV` | `development` | Set to `production` for live deployments. |
| `SENTINEL_SECRET_KEY` | *random string* | Secret used for cryptographic signing. |
| `SENTINEL_DB_PATH` | `./sentinel.db` | Path to SQLite file (use `/data/sentinel.db` in Docker). |
| `SENTINEL_COOKIE_SECURE` | `false` | Set to `true` when serving over HTTPS. |
| `SENTINEL_PORT` | `8000` | Port for the Uvicorn web server. |
| `SENTINEL_DEMO_EXPIRE_HOURS` | `24` | Duration in hours before guest sessions expire. |
