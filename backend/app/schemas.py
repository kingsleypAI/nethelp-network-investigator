"""Pydantic request/response schemas."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class EvidenceInput(BaseModel):
    name: str = Field(..., description="Filename or label for the evidence")
    text: str = Field(..., description="Raw diagnostic text")


class AnalyzeRequest(BaseModel):
    inputs: list[EvidenceInput]
    region_override: Optional[str] = Field(None, alias="regionOverride")
    site_id: Optional[str] = Field(None, alias="siteId")
    store: bool = True

    class Config:
        populate_by_name = True


class CaseSummary(BaseModel):
    id: int
    createdAt: Optional[str]
    site: str
    siteSource: Optional[str]
    region: Optional[str]
    health: str
    confidence: int
    rootCause: str
    evidenceTypes: list[str]


class SiteGroup(BaseModel):
    site: str
    worstHealth: str
    count: int
    evidenceTypes: list[str]
    cases: list[CaseSummary]


class AnalyzeResponse(BaseModel):
    # The engine returns a rich dynamic dict; expose it as-is plus the stored id.
    caseId: Optional[int] = None
    analysis: dict[str, Any]
