"""NEXUS Network Investigator — FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_analyze, routes_cases, routes_meta
from .config import get_settings
from .database import init_db

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION,
              description="AI-assisted, rules-based network diagnostics for VoIP / UCaaS support engineers.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


app.include_router(routes_analyze.router)
app.include_router(routes_cases.router)
app.include_router(routes_meta.router)
