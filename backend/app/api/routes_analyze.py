"""/analyze — run the rules engine, optionally enrich and persist."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..engine import analyse, claude
from ..engine.evidence_types import guess_type
from ..models import Investigation
from ..schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    inputs = [{"name": i.name, "text": i.text} for i in req.inputs]

    result = analyse(inputs, region_override=req.region_override, site_id=req.site_id)
    if settings.ENABLE_CLAUDE and claude.is_enabled():
        result = claude.enrich(result)

    case_id = None
    if req.store:
        types = sorted({guess_type(i["text"], i["name"]) for i in inputs})
        inv = Investigation(
            site=result.get("site") or "Unidentified",
            site_source=result.get("siteSource"),
            region=(result.get("geo") or {}).get("region"),
            health=result["health"],
            confidence=result["confidence"],
            root_cause=result["rootCause"],
            evidence_types=types,
            result=result,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        case_id = inv.id

    return AnalyzeResponse(caseId=case_id, analysis=result)
