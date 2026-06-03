"""Detection passes + geo/site resolution. Each detector appends Finding dicts."""
from __future__ import annotations

import re
from typing import Optional

from .datacentres import DATACENTRES, HOSTNAME_GEO, ISP_SIGNATURES, LATENCY_THRESHOLDS, REGIONS
from .parsers import Evidence


def _clamp(n, lo, hi):
    return max(lo, min(hi, n))


def _r1(n):
    return round(n * 10) / 10


def detect_region_from_text(text: str) -> Optional[dict]:
    for pattern, region in HOSTNAME_GEO:
        if re.search(pattern, text, re.I):
            return {"region": region, "confidence": 92}
    return None


def detect_isp(text: str, region: Optional[str]) -> Optional[str]:
    lc = text.lower()
    for sig in ISP_SIGNATURES.get(region or "", []):
        if sig in lc:
            return sig
    return None


# ---------------------------------------------------------------- geo / site
def resolve_geo(ev: Evidence, override: Optional[str]) -> dict:
    last_hosts = " ".join(h.host or "" for t in ev.traceroutes for h in t.hops)
    dc_hit = detect_region_from_text(last_hosts)
    actual_dc = DATACENTRES[dc_hit["region"]]["dc"] if dc_hit else None

    if override and override in DATACENTRES:
        return {"region": override, "expectedDc": DATACENTRES[override]["dc"],
                "actualDc": actual_dc, "confidence": 100, "method": "Agent Override",
                "note": "Manual selection overrides automatic detection."}

    region, conf, method = None, 0, "Automatic Detection"
    for u in ev.utilities:
        if u.region:
            norm = next((r for r in REGIONS if r.lower() == str(u.region).strip().lower()), None)
            if norm:
                region, conf = norm, 97
    if not region:
        hit = detect_region_from_text(ev.raw_text)
        if hit:
            region, conf = hit["region"], hit["confidence"]
    if not region and ev.public_ips:
        region, conf, method = "United Kingdom", 55, "Automatic Detection (low confidence)"
    if not region:
        return {"region": None, "expectedDc": None, "actualDc": None, "confidence": 0,
                "method": "Unresolved",
                "note": "Region could not be determined automatically. Select a region to continue."}
    return {"region": region, "expectedDc": DATACENTRES[region]["dc"], "actualDc": actual_dc,
            "confidence": conf, "method": method, "note": None}


def detect_site(ev: Evidence, override: Optional[str]) -> dict:
    if override and str(override).strip():
        return {"id": str(override).strip(), "source": "Agent label"}
    keys = ["site", "siteId", "siteID", "site_name", "customer", "customerName",
            "customer_name", "company", "account", "accountName", "account_name", "name"]
    for u in ev.utilities:
        raw = u.raw or {}
        for k in keys:
            if raw.get(k) is not None and str(raw[k]).strip():
                return {"id": str(raw[k]).strip(), "source": "Utility field"}
    m = re.search(
        r"(?:Site\s*ID|Site\s*Name|Site|Customer\s*Name|Customer|Company|Account\s*Name|Account)\s*[:=]\s*([^\n\r]{2,48})",
        ev.raw_text, re.I)
    if m:
        return {"id": re.sub(r"\s{2,}", " ", m.group(1).strip()), "source": "Diagnostics"}
    m = re.search(r"HOST\s*:\s*([A-Za-z0-9][A-Za-z0-9._-]{1,40})", ev.raw_text, re.I)
    if m and not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", m.group(1)):
        return {"id": m.group(1).strip(), "source": "Hostname"}
    if ev.public_ips:
        return {"id": ev.public_ips[0], "source": "Public IP"}
    return {"id": None, "source": None}


# ---------------------------------------------------------------- detectors
def detect_packet_loss(ev: Evidence, out: list):
    first_hop = None
    max_loss = 0.0
    location = None
    for tr in ev.traceroutes:
        for i, h in enumerate(tr.hops):
            if h.loss is None:
                continue
            nxt = tr.hops[i + 1] if i + 1 < len(tr.hops) else None
            sustained = h.loss >= 2 and (nxt is None or nxt.loss is None or nxt.loss >= max(1, h.loss - 5))
            if h.loss > max_loss:
                max_loss = h.loss
            if sustained and first_hop is None and h.loss >= 2:
                first_hop = h.hop
                location = "lan" if h.hop <= 2 else ("cpe/isp-edge" if h.hop <= 3 else "isp")
    for pg in ev.pings:
        if pg.loss > max_loss:
            max_loss = pg.loss
    if max_loss < 1:
        return

    severity = "critical" if max_loss >= 3 else "degraded"
    if location == "lan":
        where, area = "within the customer LAN", "LAN"
        rc = f"Packet loss ({_r1(max_loss)}%) detected within the customer LAN at hop {first_hop}."
    elif location == "cpe/isp-edge":
        where, area = "at the CPE / ISP gateway", "ISP-edge"
        rc = f"Packet loss ({_r1(max_loss)}%) detected between the customer LAN and the ISP gateway (hop {first_hop})."
    elif location == "isp":
        where, area = "in the ISP / backbone path", "ISP"
        rc = f"Packet loss ({_r1(max_loss)}%) detected outside the customer LAN, beginning at hop {first_hop} (ISP path)."
    else:
        where, area = "in the end-to-end path", "ISP"
        rc = f"Packet loss ({_r1(max_loss)}%) detected in the end-to-end path."

    out.append({
        "kind": "packet-loss", "area": area, "severity": severity,
        "confidence": _clamp(70 + round(max_loss * 4), 70, 95), "rootCause": rc,
        "metrics": {"Packet Loss": f"{_r1(max_loss)}%",
                    "Issue Starts": f"Hop {first_hop}" if first_hop else "—",
                    "Location": where},
        "firstLossHop": first_hop,
    })


def _route_class(geo: dict) -> dict:
    if not geo or not geo.get("region"):
        return {"key": "domestic", "label": "domestic"}
    region = geo["region"]
    cluster = DATACENTRES.get(region, {}).get("cluster")
    if cluster == "NA" and region != "United States":
        return {"key": "domestic", "label": f"{region}-to-DC"}
    if region == "United Kingdom":
        return {"key": "domestic", "label": "UK-to-UK"}
    if cluster == "EMEA":
        return {"key": "europe", "label": "intra-Europe"}
    if cluster == "APAC":
        return {"key": "europe", "label": "intra-APAC"}
    return {"key": "domestic", "label": "domestic"}


def detect_latency(ev: Evidence, geo: dict, out: list):
    baseline = peak = peak_hop = None
    for tr in ev.traceroutes:
        finals = [h for h in tr.hops if h.avg is not None]
        if not finals:
            continue
        dest = finals[-1]
        if peak is None or dest.avg > peak:
            peak = dest.avg
        if baseline is None:
            baseline = finals[0].avg
        for h in finals:
            if peak_hop is None and h.worst is not None and h.best is not None and (h.worst - h.best) > 60:
                peak_hop = h.hop
    for pg in ev.pings:
        if pg.avg is not None and (peak is None or pg.avg > peak):
            peak = pg.avg
    if peak is None:
        return

    cls = _route_class(geo)
    thr = LATENCY_THRESHOLDS[cls["key"]]
    if peak <= thr:
        return
    severity = "critical" if peak > thr * 2.5 else "degraded"
    out.append({
        "kind": "latency", "area": "ISP", "severity": severity,
        "confidence": _clamp(68 + round((peak - thr) / thr * 20), 68, 90),
        "rootCause": f"Latency is high for a {cls['label']} route. Expected <{thr}ms, observed {_r1(peak)}ms.",
        "metrics": {
            "Latency": (f"{_r1(baseline)}ms → " if baseline is not None else "") + f"{_r1(peak)}ms",
            "Expected": f"<{thr}ms ({cls['label']})",
            "Spike At": f"Hop {peak_hop}" if peak_hop else "—",
        },
    })


def detect_jitter_mos(ev: Evidence, out: list):
    jitter = mos = None
    for u in ev.utilities:
        if u.jitter is not None:
            jitter = max(jitter or 0, u.jitter)
        if u.mos is not None:
            mos = u.mos if mos is None else min(mos, u.mos)
    if jitter is not None and jitter > 30:
        out.append({
            "kind": "jitter", "area": "ISP", "severity": "critical" if jitter > 50 else "degraded",
            "confidence": _clamp(70 + round(jitter), 70, 92),
            "rootCause": f"Excessive jitter ({_r1(jitter)}ms) detected — voice quality will be affected. Target <30ms.",
            "metrics": {"Jitter": f"{_r1(jitter)}ms", "Target": "<30ms"},
        })
    if mos is not None and mos < 3.6:
        out.append({
            "kind": "mos", "area": "ISP", "severity": "critical" if mos < 3.0 else "degraded",
            "confidence": 85,
            "rootCause": f"Degraded call quality — MOS {_r1(mos)} (good >=4.0, acceptable >=3.6).",
            "metrics": {"MOS": _r1(mos), "Target": ">=3.6"},
        })


def detect_firewall(ev: Evidence, out: list):
    blocked = []
    for u in ev.utilities:
        for k, v in (u.ports or {}).items():
            if re.search(r"block|closed|fail|filter", str(v), re.I):
                blocked.append(k.upper())
    if not blocked:
        return
    media = any(re.search(r"RTP|MEDIA|10000", b) for b in blocked)
    sig = any("506" in b for b in blocked)
    out.append({
        "kind": "firewall", "area": "Firewall",
        "severity": "critical" if (media or sig) else "degraded", "confidence": 90,
        "rootCause": f"Required 8x8 {'media (RTP)' if media else 'signalling'} ports appear blocked or filtered: {', '.join(blocked)}.",
        "metrics": {"Blocked Ports": ", ".join(blocked),
                    "SIP 5060/5061": "BLOCKED" if sig else "OK",
                    "RTP 10000-30000": "BLOCKED" if media else "OK"},
    })


def detect_dns(ev: Evidence, geo: dict, out: list):
    for u in ev.utilities:
        if u.dns and re.search(r"FAIL|WARNING|ERROR|SLOW", str(u.dns), re.I):
            out.append({
                "kind": "dns", "area": "DNS",
                "severity": "critical" if re.search(r"FAIL|ERROR", str(u.dns), re.I) else "degraded",
                "confidence": 82,
                "rootCause": f"DNS resolution problem detected ({u.dns}). This can cause geo-routing to the wrong 8x8 datacentre.",
                "metrics": {"DNS": u.dns},
            })


def detect_datacentre(ev: Evidence, geo: dict, out: list):
    if not geo or not geo.get("region") or not geo.get("actualDc"):
        return
    if geo["actualDc"] != geo["expectedDc"]:
        out.append({
            "kind": "datacentre", "area": "Routing", "severity": "degraded", "confidence": 80,
            "rootCause": f"Traffic is reaching {geo['actualDc']} but {geo['region']} should route to "
                         f"{geo['expectedDc']}. Likely DNS, VPN, SD-WAN or ISP routing.",
            "metrics": {"Expected DC": geo["expectedDc"], "Actual DC": geo["actualDc"], "Status": "WARNING"},
        })
