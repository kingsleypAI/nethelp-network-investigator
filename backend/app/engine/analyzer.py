"""Top-level orchestration: parse -> detect -> correlate -> compose outputs."""
from __future__ import annotations

from typing import Optional

from . import detectors as D
from .datacentres import DATACENTRES
from .parsers import Evidence, parse_all

SEV_RANK = {"critical": 3, "degraded": 2, "info": 1, "healthy": 0}
KIND_RANK = {"packet-loss": 6, "firewall": 5, "dns": 4, "datacentre": 4, "jitter": 3, "mos": 2, "latency": 1}


def _derive_affected(findings: list) -> list:
    s: list[str] = []
    def add(x):
        if x not in s:
            s.append(x)
    for f in findings:
        if f["kind"] in ("packet-loss", "jitter", "mos", "latency", "firewall"):
            add("Voice Calls")
        if f["kind"] in ("dns", "datacentre"):
            add("Call Setup / Routing")
        if f["kind"] == "firewall":
            add("Media / RTP")
    return s


def _build_evidence(ev: Evidence, geo: dict, findings: list) -> dict:
    lines: dict = {}
    for f in findings[:4]:
        lines.update(f.get("metrics", {}))
    affected = _derive_affected(findings)
    if affected:
        lines["Affected Services"] = ", ".join(affected)
    if geo and geo.get("region"):
        lines["Region"] = geo["region"] + (f" ({geo['confidence']}%)" if geo.get("confidence") else "")
    if ev.public_ips:
        lines["Public IP"] = ev.public_ips[0]
    if not lines:
        lines["Status"] = "All measured metrics within normal range."
    return lines


def _rank_fixes(findings: list) -> list:
    if not findings or findings[0]["severity"] == "healthy":
        return []
    area = findings[0]["area"]
    table = {
        "ISP": [("ISP Escalation", 87), ("Reboot Router / CPE", 41), ("Connect via Ethernet (bypass Wi-Fi)", 33)],
        "ISP-edge": [("ISP Escalation", 78), ("Reboot Router / CPE", 55), ("Replace WAN cable / check line", 38)],
        "LAN": [("Connect via Ethernet (bypass Wi-Fi)", 72), ("Check switch / cabling for the affected device", 58), ("Reboot local network equipment", 44)],
        "Firewall": [("Open required 8x8 ports (SIP 5060/5061, RTP 10000-30000)", 91), ("Disable SIP ALG on the firewall", 64), ("Review firewall rules vs 8x8 requirements", 60)],
        "DNS": [("Set DNS to a public resolver (e.g. 8.8.8.8 / 1.1.1.1)", 76), ("Flush DNS cache", 48), ("Verify DNS is not forced via VPN", 40)],
        "Routing": [("Verify DNS and WAN routing policy", 70), ("Disable VPN / check SD-WAN breakout", 62), ("ISP Escalation", 45)],
    }
    rows = table.get(area, [("Reboot Router", 41)])
    return [{"label": l, "probability": p} for l, p in rows]


def _detect_isp_signature(ev: Evidence, geo: dict, findings: list) -> Optional[dict]:
    if not geo or not geo.get("region"):
        return None
    isp = D.detect_isp(ev.raw_text, geo["region"])
    loss_in_isp = any(f["area"] in ("ISP", "ISP-edge") for f in findings)
    if isp and loss_in_isp:
        name = isp[:1].upper() + isp[1:]
        conf = 87
        if conf > 80:
            return {"name": name, "confidence": conf,
                    "text": f"Known Pattern Detected: {name} congestion signature. "
                            f"Recommended action: escalate to ISP."}
    return None


def _customer_text(health: str, top: Optional[dict]) -> str:
    if not top or health == "healthy":
        return ("We ran a full diagnostic on your connection and everything looks healthy. "
                "We did not find any network issues affecting your service.")
    area = top["area"]
    if area in ("ISP", "ISP-edge"):
        return ("We identified packet loss occurring outside your local network. This appears to be related to "
                "your internet provider. We recommend contacting your ISP and providing the attached diagnostics.")
    if area == "Firewall":
        return ("We found that some of the network ports required for your phone service appear to be blocked by "
                "your firewall. We recommend your IT team allow the required 8x8 ports, then retest.")
    if area == "LAN":
        return ("We found a connectivity issue inside your local network. We recommend connecting the affected "
                "device by Ethernet, checking your switch and cabling, then retesting.")
    if area in ("DNS", "Routing"):
        return ("We found your connection may be routing to the wrong region or using an unreliable DNS. We "
                "recommend checking your DNS settings and any VPN/SD-WAN policies, then retesting.")
    return "We identified a network issue affecting your service. Please see the recommended steps and retest."


def _engineer_text(health: str, top: Optional[dict], geo: dict) -> str:
    if not top or health == "healthy":
        return "All measured metrics within tolerance. No reproducible issue. No action required."
    bits = [top["rootCause"]]
    if top.get("firstLossHop"):
        bits.append("Reproducible within LAN." if top["firstLossHop"] <= 2
                    else "Not reproducible within LAN — first sustained loss is beyond the CPE.")
    if geo and geo.get("region"):
        bits.append(f"Region {geo['region']}, expected DC {geo['expectedDc']}"
                    + (f", observed {geo['actualDc']}." if geo.get("actualDc") else "."))
    return " ".join(bits)


def _ticket_notes(health: str, top: Optional[dict], geo: dict, findings: list) -> list:
    notes = []
    if geo and geo.get("region"):
        notes.append(f"Region: {geo['region']} -> expected DC {geo['expectedDc']}.")
    if not top or health == "healthy":
        notes.append("Diagnostics reviewed: no significant issue detected.")
        return notes[:5]
    notes.append(f"Health: {health.upper()} — {top['rootCause']}")
    m = top.get("metrics", {})
    ms = ", ".join(f"{k}: {v}" for k, v in list(m.items())[:2])
    if ms:
        notes.append("Evidence: " + ms + ".")
    aff = _derive_affected(findings)
    if aff:
        notes.append("Impact: " + ", ".join(aff) + ".")
    nxt = ("ISP escalation with attached trace" if top["area"] in ("ISP", "ISP-edge")
           else "open required 8x8 ports, retest" if top["area"] == "Firewall"
           else "apply recommended fix, retest")
    notes.append(f"Next: {nxt}.")
    return notes[:5]


def _escalation_summary(top: Optional[dict], ev: Evidence, geo: dict) -> str:
    if not top or top["severity"] == "healthy":
        return "No escalation required — network healthy."
    lines = [f"ROOT CAUSE: {top['rootCause']}"]
    lines.append(f"REGION/DC: {geo['region'] + ' -> ' + geo['expectedDc'] if geo and geo.get('region') else 'unresolved'}"
                 + (f" (observed {geo['actualDc']})" if geo and geo.get("actualDc") else ""))
    m = top.get("metrics", {})
    lines.append("EVIDENCE: " + "; ".join(f"{k}={v}" for k, v in m.items()))
    onfile = (("8x8 utility test; " if ev.utilities else "")
              + ("traceroute/MTR; " if ev.traceroutes else "")
              + ("ping; " if ev.pings else "")).strip()
    lines.append(f"EVIDENCE ON FILE: {onfile}")
    lines.append(f"CONFIDENCE: {top['confidence']}%")
    return "\n".join(lines)


def _review_flag(inputs, ev: Evidence, geo: dict, findings: list, health: str, confidence: int) -> dict:
    """When should a human double-check the automated verdict?"""
    reasons = []
    if health != "healthy" and confidence < 75:
        reasons.append("Confidence is below 75% — the automated reading is not certain.")
    if not geo or not geo.get("region"):
        reasons.append("Region could not be determined automatically — set it manually and re-run.")
    elif geo.get("method") != "Agent Override" and geo.get("confidence") and geo["confidence"] < 70:
        reasons.append("Region was detected with low confidence — verify (VPN / SD-WAN / Citrix can mislead this).")
    if len(findings) >= 2:
        a, b = findings[0], findings[1]
        if a["severity"] == b["severity"] and abs(a["confidence"] - b["confidence"]) <= 8:
            reasons.append("Two possible root causes scored similarly — confirm which is primary.")
    evidence_count = len(ev.traceroutes) + len(ev.pings) + len(ev.utilities)
    if health != "healthy" and evidence_count <= 1:
        reasons.append("Verdict is based on a single piece of evidence — attach a traceroute/PingPlotter to confirm.")
    if any(f["kind"] == "datacentre" for f in findings):
        reasons.append("Datacentre mismatch can have several causes (DNS / VPN / SD-WAN) — confirm against the customer's setup.")
    return {"needed": len(reasons) > 0, "reasons": reasons}


def _escalation_readiness(ev: Evidence, geo: dict, findings: list) -> dict:
    checks = {
        "Utility Test Present": len(ev.utilities) > 0,
        "Trace / PingPlotter Attached": len(ev.traceroutes) > 0,
        "Datacentre Identified": bool(geo and geo.get("region")),
        "Packet Loss Confirmed": any(f["kind"] == "packet-loss" for f in findings),
        "Routing Analysis Completed": len(ev.traceroutes) > 0,
        "Root Cause Identified": any(f["severity"] != "healthy" for f in findings),
    }
    passed = sum(1 for v in checks.values() if v)
    ready = passed >= 5 and checks["Root Cause Identified"]
    return {"ready": ready, "checks": checks, "passed": passed, "total": len(checks)}


def analyse(inputs: list[dict], region_override: Optional[str] = None,
            site_id: Optional[str] = None) -> dict:
    ev = parse_all(inputs)
    geo = D.resolve_geo(ev, region_override)
    site = D.detect_site(ev, site_id)

    findings: list = []
    D.detect_packet_loss(ev, findings)
    D.detect_latency(ev, geo, findings)
    D.detect_jitter_mos(ev, findings)
    D.detect_firewall(ev, findings)
    D.detect_dns(ev, geo, findings)
    D.detect_datacentre(ev, geo, findings)

    findings.sort(key=lambda f: (SEV_RANK[f["severity"]], KIND_RANK.get(f["kind"], 0), f["confidence"]),
                  reverse=True)

    top = findings[0] if findings else None
    health, root_cause, confidence = "healthy", "Network appears healthy. No significant issues detected.", 96
    if top and top["severity"] != "healthy":
        health = "critical" if top["severity"] == "critical" else "degraded"
        root_cause = top["rootCause"]
        confidence = top["confidence"]

    return {
        "health": health,
        "rootCause": root_cause,
        "confidence": confidence,
        "geo": geo,
        "site": site["id"],
        "siteSource": site["source"],
        "findings": findings,
        "evidence": _build_evidence(ev, geo, findings),
        "fixes": _rank_fixes(findings),
        "isp": _detect_isp_signature(ev, geo, findings),
        "affectedServices": _derive_affected(findings),
        "customerText": _customer_text(health, top),
        "engineerText": _engineer_text(health, top, geo),
        "ticketNotes": _ticket_notes(health, top, geo, findings),
        "escalationSummary": _escalation_summary(top, ev, geo),
        "escalation": _escalation_readiness(ev, geo, findings),
        "reviewFlag": _review_flag(inputs, ev, geo, findings, health, confidence),
        "rawInputs": [{"name": i.get("name", "input"), "text": i.get("text", "")} for i in (inputs or [])],
        "detected": {
            "sources": ev.sources,
            "publicIps": ev.public_ips,
            "traceroutes": len(ev.traceroutes),
            "pings": len(ev.pings),
            "utilities": len(ev.utilities),
        },
    }
