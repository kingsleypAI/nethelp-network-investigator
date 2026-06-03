"""/meta — reference data: regions, datacentres, ports, thresholds, samples."""
from __future__ import annotations

import json

from fastapi import APIRouter

from ..config import get_settings
from ..engine import DATACENTRES, LATENCY_THRESHOLDS, REGIONS, REQUIRED_PORTS
from ..engine import claude

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/regions")
def regions():
    return REGIONS


@router.get("/datacentres")
def datacentres():
    return [{"region": r, **d} for r, d in DATACENTRES.items()]


@router.get("/ports")
def ports():
    return REQUIRED_PORTS


@router.get("/thresholds")
def thresholds():
    return LATENCY_THRESHOLDS


@router.get("/config")
def config():
    s = get_settings()
    return {"app": s.APP_NAME, "version": s.VERSION,
            "claudeEnabled": s.ENABLE_CLAUDE and claude.is_enabled()}


@router.get("/samples")
def samples():
    """Built-in demo cases (kept server-side so the SPA and tests share them)."""
    return {
        "Healthy UK": [
            {"name": "mtr.txt", "text": "HOST: northwind-pc                Loss%   Snt   Last   Avg  Best  Wrst StDev\n"
             "  1.|-- 192.168.1.1                0.0%    10    0.8   0.9   0.7   1.2   0.1\n"
             "  2.|-- 10.20.0.1                  0.0%    10    7.1   7.4   6.9   8.0   0.3\n"
             "  3.|-- core1.lon.bt.net           0.0%    10    9.2   9.5   9.0  10.1   0.3\n"
             "  4.|-- ae0.edge.lon.8x8.com       0.0%    10   11.3  11.6  11.0  12.4   0.4"},
            {"name": "utility.json", "text": json.dumps({"customer": "Northwind Trading · Leeds",
             "region": "United Kingdom", "publicIp": "62.10.20.30", "dns": "PASS", "sbc": "PASS",
             "jitter": 8, "mos": 4.3, "ports": {"5060": "open", "5061": "open", "rtp": "open", "443": "open"}})},
        ],
        "ISP Packet Loss": [
            {"name": "pingplotter.txt", "text": "Target: lon.8x8.com\nHop  IP                       Loss%  Avg\n"
             "  1  192.168.1.1              0.0%   1.0\n  2  10.0.0.1                 0.0%   8.0\n"
             "  3  core.virginmedia.net     4.2%   34.0\n  4  peer.virginmedia.net     4.5%   120.0\n"
             "  5  edge.lon.8x8.com         4.6%   286.0"},
            {"name": "8x8util.txt", "text": "8x8 Utility Test\nCustomer: Acme Corp · London\n"
             "Region: United Kingdom\nPublic IP: 81.2.3.4\nDNS: PASS\nSBC Reachability: PASS\nJitter: 42\nMOS: 3.2"},
        ],
        "Firewall RTP Blocked": [
            {"name": "utility.json", "text": json.dumps({"customer": "Berlin Logistics GmbH", "region": "Germany",
             "publicIp": "91.10.10.10", "dns": "PASS", "sbc": "WARNING",
             "ports": {"5060": "open", "5061": "open", "rtp": "blocked", "443": "open"}})},
        ],
        "Wrong Datacentre (Acme)": [
            {"name": "trace.txt", "text": "traceroute to fra.8x8.com\n 1  192.168.0.1  1.1 ms 1.0 ms 1.2 ms\n"
             " 2  10.0.0.1  6.0 ms 6.1 ms 6.2 ms\n 3  core.bt.net  10.0 ms 10.1 ms 9.9 ms\n"
             " 4  edge.fra.8x8.com  28.0 ms 28.1 ms 27.9 ms"},
            {"name": "util.txt", "text": "8x8 Utility Test\nCustomer: Acme Corp · London\n"
             "Region: United Kingdom\nDNS: WARNING\nPublic IP: 62.5.5.5"},
        ],
        "LAN / Wi-Fi Loss": [
            {"name": "mtr.txt", "text": "HOST: riverside-pc                Loss%   Snt   Last   Avg  Best  Wrst StDev\n"
             "  1.|-- 192.168.1.1                6.0%    10   12.0  45.0   2.0  180.0  60.1\n"
             "  2.|-- 10.0.0.1                   5.8%    10   10.0  10.5   9.0  12.0   1.0\n"
             "  3.|-- core.lon.bt.net            0.0%    10    9.0   9.2   8.9  10.0   0.3"},
            {"name": "u.txt", "text": "Customer: Riverside Dental · Manchester\nRegion: United Kingdom"},
        ],
    }
