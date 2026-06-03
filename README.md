# NEXUS Network Investigator

An AI-assisted, **rules-based** network diagnostics platform for Technical Support Engineers supporting VoIP, UCaaS and Contact Centre environments (built around 8x8 connectivity requirements).

Upload diagnostics — traceroutes, MTR, ping tests, 8x8 utility tests, PingPlotter exports, firewall logs — and NEXUS answers the only four questions that matter:

> **What is wrong? · Why do we think this? · How severe is it? · What should the customer do next?**

No 200-line reports. A root cause, the evidence, a ranked fix, customer + engineer + ticket text, and an escalation-readiness verdict — in seconds.

> A zero-install single-file demo (`demo/NEXUS.html`) is also included — open it in a browser for a quick look without running the stack.

---

## Why it's different

- **Deterministic core, no API key required.** The analysis engine is pure rules and thresholds — it runs offline and gives the same answer every time. The Claude API is an *optional* layer that only polishes the customer-facing wording; it never changes the verdict.
- **Region-aware.** Latency is judged against the route class ("high for a UK-to-UK route, expected <50ms, observed 142ms"), not a blanket threshold.
- **Datacentre intelligence.** Detects the customer's region and compares the datacentre traffic actually reaches against where 8x8 expects it (PASS / WARNING with likely causes).
- **Evidence correlation.** Multiple uploads (e.g. a PingPlotter screenshot export *and* a utility test) are analysed together to pick the single most likely root cause.
- **Site grouping.** Every investigation is tagged with a Site / Customer ID (auto-detected or entered) so Previous Cases group multiple tests per company.

## Features

| Area | What it does |
|------|--------------|
| Detection | Packet loss (LAN vs CPE vs ISP), latency, jitter, MOS, firewall/port blocks, DNS, datacentre mismatch |
| Geo engine | Auto-detect region from diagnostics + manual agent override (VPN / SD-WAN / Citrix) |
| ISP signatures | Surfaces known patterns (e.g. Virgin Media congestion) only above 80% confidence |
| Fix ranking | Ranks the likely fixes by probability instead of listing twenty |
| Outputs | Customer response · engineer findings · ≤5-bullet ticket notes · escalation summary — one-click copy |
| Escalation | Six-point readiness checklist with a YES/NO verdict |
| History | Investigations persisted to PostgreSQL, grouped by site |

## Tech stack

- **Frontend:** React + TypeScript + Vite (industrial NOC UI)
- **Backend:** FastAPI + Python rules engine
- **Database:** PostgreSQL (SQLite fallback for zero-setup local dev)
- **Processing:** Pandas/NumPy/OpenCV available; OpenCV used for screenshot visual signals
- **AI (optional):** Claude API enrichment behind an env flag

---

## Quick start

### Option A — Docker (everything)

```bash
cp .env.example .env        # optional: add ANTHROPIC_API_KEY + ENABLE_CLAUDE=true
docker compose up --build
```

- App: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>

### Option B — Local dev (no Docker, no Postgres)

**Backend** (uses the SQLite fallback automatically):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173 (proxies /api -> :8000)
```

---

## Project structure

```
nexus/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app + routers
│   │   ├── config.py          env-driven settings
│   │   ├── database.py        SQLAlchemy (Postgres / SQLite fallback)
│   │   ├── models.py          Investigation ORM
│   │   ├── schemas.py         Pydantic models
│   │   ├── api/               /analyze · /cases · /meta routes
│   │   └── engine/            the rules engine
│   │       ├── datacentres.py datacentre/threshold/ISP intelligence
│   │       ├── parsers.py     traceroute / MTR / ping / PingPlotter / 8x8 utility
│   │       ├── detectors.py   per-issue detection + geo/site resolution
│   │       ├── analyzer.py    orchestration + output composition
│   │       ├── images.py      OpenCV screenshot signals (OCR extension point)
│   │       └── claude.py      optional enrichment
│   ├── tests/                 pytest (parsers · analyzer · API)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx            layout + state
│   │   ├── api.ts             typed API client
│   │   ├── types.ts
│   │   └── components/        TopBar · Nav · Workspace · Results · Summary · Console · Cases · DatacentreDB · KB
│   ├── Dockerfile + nginx.conf
│   └── vite.config.ts
├── docker-compose.yml
├── .github/workflows/ci.yml
├── .env.example
└── docs/DEPLOYMENT.md
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/analyze` | Run the engine on uploaded evidence; optionally persist |
| GET | `/cases` | Flat list of stored investigations |
| GET | `/cases/grouped` | Investigations grouped by site |
| GET | `/cases/{id}` | Full stored analysis |
| GET | `/meta/regions` `/meta/datacentres` `/meta/ports` `/meta/samples` `/meta/config` | Reference data |
| GET | `/health` | Liveness |

Interactive docs at `/docs` (Swagger) when the backend is running.

## Testing

```bash
cd backend && pytest -q
```

Covers the parsers, the five canonical scenarios (healthy / ISP loss / firewall / wrong-DC / LAN loss), region-aware latency, and the API including site grouping. CI runs backend tests + a frontend type-check/build on every push (`.github/workflows/ci.yml`).

## Notes & disclaimers

Datacentre maps, IP ranges and ISP signatures are representative demo values. Replace the data in `backend/app/engine/datacentres.py` with your current internal 8x8 reference data before production use. The platform is a support-acceleration aid — engineers remain responsible for the final diagnosis.
