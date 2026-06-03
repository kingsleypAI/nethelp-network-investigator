"""Application configuration via environment variables."""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    APP_NAME: str = "NEXUS Network Investigator"
    VERSION: str = "1.0.0"
    # Postgres in production; falls back to local SQLite so the API runs with zero setup.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")
    # Comma-separated allowed origins for the SPA.
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if o.strip()
    ]
    # Optional Claude enrichment.
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    ENABLE_CLAUDE: bool = os.getenv("ENABLE_CLAUDE", "false").lower() in ("1", "true", "yes")


@lru_cache
def get_settings() -> Settings:
    return Settings()
