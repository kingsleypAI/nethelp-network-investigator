"""ORM models for stored investigations."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from .database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    site = Column(String(120), index=True, default="Unidentified")
    site_source = Column(String(40), nullable=True)
    region = Column(String(60), nullable=True)
    health = Column(String(12), index=True)
    confidence = Column(Integer)
    root_cause = Column(Text)

    # evidence types present (e.g. ["PINGPLOTTER","8x8 UTIL"]) for grouped display
    evidence_types = Column(JSON, default=list)
    # full analysis payload for re-rendering a case
    result = Column(JSON)

    def summary(self) -> dict:
        return {
            "id": self.id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "site": self.site,
            "siteSource": self.site_source,
            "region": self.region,
            "health": self.health,
            "confidence": self.confidence,
            "rootCause": self.root_cause,
            "evidenceTypes": self.evidence_types or [],
        }
