"""/cases — stored investigations, grouped by site."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Investigation

router = APIRouter(prefix="/cases", tags=["cases"])

_SEV = {"healthy": 0, "degraded": 1, "critical": 2}


@router.get("")
def list_cases(db: Session = Depends(get_db)):
    """Flat list of stored cases, newest first."""
    rows = db.query(Investigation).order_by(Investigation.created_at.desc()).all()
    return [r.summary() for r in rows]


@router.get("/grouped")
def grouped_cases(db: Session = Depends(get_db)):
    """Cases grouped by site identifier so multiple tests per company collapse."""
    rows = db.query(Investigation).order_by(Investigation.created_at.desc()).all()
    groups: list[dict] = []
    idx: dict[str, int] = {}
    for r in rows:
        key = (r.site or "Unidentified").lower()
        if key not in idx:
            idx[key] = len(groups)
            groups.append({"site": r.site or "Unidentified", "cases": []})
        groups[idx[key]]["cases"].append(r.summary())
    for g in groups:
        cases = g["cases"]
        g["count"] = len(cases)
        g["worstHealth"] = max((c["health"] for c in cases), key=lambda h: _SEV.get(h, 0))
        g["evidenceTypes"] = sorted({t for c in cases for t in c["evidenceTypes"]})
        # recurring root-cause hint
        kinds: dict[str, int] = {}
        for c in cases:
            kinds[c["health"]] = kinds.get(c["health"], 0) + 1
    return groups


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    row = db.query(Investigation).filter(Investigation.id == case_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"summary": row.summary(), "analysis": row.result}


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    row = db.query(Investigation).filter(Investigation.id == case_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(row)
    db.commit()
    return {"deleted": case_id}
