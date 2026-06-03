"""Classify a piece of evidence into a display type (for grouped case history)."""
from __future__ import annotations

import json
import re


def guess_type(text: str, name: str = "") -> str:
    name = (name or "").lower()
    if "pingplotter" in name or re.search(r"pingplotter", text, re.I):
        return "PINGPLOTTER"
    if re.search(r"loss%\s+snt|wrst|stdev|\bmtr\b", text, re.I):
        return "MTR"
    if re.search(r"^\s*target\s*:", text, re.I | re.M) and re.search(r"loss\s*%", text, re.I):
        return "PINGPLOTTER"
    if re.search(r"utility test|sbc|reachability|\"sbc\"|\"reachability\"", text, re.I):
        return "8x8 UTIL"
    if re.search(r"traceroute|\bhop\b|\bms\b", text, re.I):
        return "TRACE"
    if re.search(r"ping|packets", text, re.I):
        return "PING"
    try:
        j = json.loads(text)
        if isinstance(j, dict) and (j.get("region") or j.get("dns") or j.get("ports") or j.get("sbc")):
            return "8x8 UTIL"
        return "JSON"
    except (json.JSONDecodeError, ValueError):
        pass
    return "LOG"
