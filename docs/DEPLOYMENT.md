# Deployment Guide

## 1. Prerequisites

- Docker + Docker Compose (recommended), or Python 3.12 + Node 20 for manual deploys.
- A PostgreSQL 14+ instance for production (the SQLite fallback is for local dev only).

## 2. Environment variables

Copy `.env.example` to `.env` and set:

| Var | Required | Notes |
|-----|----------|-------|
| `DATABASE_URL` | prod | `postgresql+psycopg2://user:pass@host:5432/db` |
| `CORS_ORIGINS` | prod | Comma-separated list of allowed SPA origins |
| `ENABLE_CLAUDE` | no | `true` to turn on Claude enrichment |
| `ANTHROPIC_API_KEY` | if Claude on | Anthropic API key |
| `ANTHROPIC_MODEL` | no | Defaults to `claude-opus-4-6` |
| `VITE_API_URL` | build | API base baked into the frontend (Docker default `/api`) |

## 3. Docker Compose (single host)

```bash
cp .env.example .env
docker compose up --build -d
```

Brings up Postgres, the FastAPI backend (`:8000`), and the nginx-served SPA (`:3000`).
nginx proxies `/api` to the backend, so only port 3000 needs to be public.

Verify:

```bash
curl localhost:8000/health
curl localhost:3000
```

## 4. Manual deploy

### Backend

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/nexus
export CORS_ORIGINS=https://nexus.example.com
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Put it behind a reverse proxy (nginx/Caddy) and a process manager (systemd/supervisor).
Tables are created on startup; for controlled schema changes, introduce Alembic.

### Frontend

```bash
cd frontend
npm ci
VITE_API_URL=https://api.nexus.example.com npm run build
# serve the static dist/ from any web server or CDN
```

## 5. Database

`init_db()` runs `create_all` at startup, which is fine for first deploy. For
evolving schemas in production, add Alembic:

```bash
pip install alembic
alembic init alembic   # point sqlalchemy.url at DATABASE_URL, then autogenerate
```

## 6. Optional Claude enrichment

Set `ENABLE_CLAUDE=true` and `ANTHROPIC_API_KEY`. If the key is missing or a call
fails, the deterministic rules result is returned unchanged — enrichment can never
break or alter the diagnosis.

## 7. Production hardening checklist

- [ ] Replace demo datacentre/IP/ISP data in `engine/datacentres.py`
- [ ] Set restrictive `CORS_ORIGINS`
- [ ] Run backend with multiple workers behind TLS
- [ ] Managed Postgres with automated backups
- [ ] Add auth (e.g. SSO/JWT) in front of `/analyze` and `/cases` if exposed
- [ ] Add Alembic migrations
- [ ] Wire logs/metrics to your observability stack
```
