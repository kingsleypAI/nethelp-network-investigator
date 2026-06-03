"""Datacentre, geo, threshold and ISP-signature intelligence for NEXUS.

Representative values for a support-engineering platform. Centralised here so
the rest of the engine (and the API /meta endpoints) share one source of truth.
"""
from __future__ import annotations

# 8x8 region -> datacentre + representative edge/SBC endpoints + cluster.
DATACENTRES: dict[str, dict] = {
    "United Kingdom": {"dc": "London (LON)", "code": "GB", "edge": ["lon.8x8.com"], "cluster": "EMEA"},
    "Ireland":        {"dc": "London (LON)", "code": "IE", "edge": ["lon.8x8.com"], "cluster": "EMEA"},
    "France":         {"dc": "Frankfurt (FRA)", "code": "FR", "edge": ["fra.8x8.com"], "cluster": "EMEA"},
    "Germany":        {"dc": "Frankfurt (FRA)", "code": "DE", "edge": ["fra.8x8.com"], "cluster": "EMEA"},
    "Netherlands":    {"dc": "Frankfurt (FRA)", "code": "NL", "edge": ["fra.8x8.com"], "cluster": "EMEA"},
    "Spain":          {"dc": "Frankfurt (FRA)", "code": "ES", "edge": ["fra.8x8.com"], "cluster": "EMEA"},
    "Italy":          {"dc": "Frankfurt (FRA)", "code": "IT", "edge": ["fra.8x8.com"], "cluster": "EMEA"},
    "United States":  {"dc": "US East (IAD)", "code": "US", "edge": ["iad.8x8.com"], "cluster": "NA"},
    "Canada":         {"dc": "US East (IAD)", "code": "CA", "edge": ["iad.8x8.com"], "cluster": "NA"},
    "Australia":      {"dc": "Sydney (SYD)", "code": "AU", "edge": ["syd.8x8.com"], "cluster": "APAC"},
    "Singapore":      {"dc": "Singapore (SIN)", "code": "SG", "edge": ["sin.8x8.com"], "cluster": "APAC"},
    "Japan":          {"dc": "Tokyo (TYO)", "code": "JP", "edge": ["tyo.8x8.com"], "cluster": "APAC"},
    "APAC":           {"dc": "Singapore (SIN)", "code": "SG", "edge": ["sin.8x8.com"], "cluster": "APAC"},
    "LATAM":          {"dc": "US East (IAD)", "code": "US", "edge": ["iad.8x8.com"], "cluster": "NA"},
}
REGIONS = list(DATACENTRES.keys())

# Round-trip latency budgets (ms) by route class.
LATENCY_THRESHOLDS = {
    "domestic": 50,
    "europe": 80,
    "transatlantic": 150,
    "intercontinental": 250,
}

# Required 8x8 connectivity ports.
REQUIRED_PORTS = [
    {"port": "5060", "proto": "UDP/TCP", "use": "SIP signalling"},
    {"port": "5061", "proto": "TLS", "use": "SIP secure signalling"},
    {"port": "443", "proto": "TCP", "use": "HTTPS / provisioning"},
    {"port": "10000-30000", "proto": "UDP", "use": "RTP media"},
]

# Regional ISP signatures (only surfaced when confidence > 80%).
ISP_SIGNATURES = {
    "United Kingdom": ["bt", "virgin", "virginmedia", "sky", "vodafone", "talktalk", "plusnet", "ee"],
    "Germany": ["deutsche telekom", "telekom", "vodafone", "1&1", "o2"],
    "France": ["orange", "sfr", "free", "bouygues"],
    "United States": ["comcast", "verizon", "at&t", "att", "spectrum", "cox", "lumen", "centurylink"],
    "Australia": ["telstra", "optus", "tpg", "aussie broadband"],
}

# Coarse hostname -> region hints (demo-grade geo).
HOSTNAME_GEO = [
    (r"\b(lon|ldn|thn|telehouse|london|uk)\b|\.gb\.", "United Kingdom"),
    (r"\b(dub|dublin)\b|\.ie\.", "Ireland"),
    (r"\b(fra|frankfurt)\b|\.de\.", "Germany"),
    (r"\b(par|paris)\b|\.fr\.", "France"),
    (r"\b(ams|amsterdam)\b|\.nl\.", "Netherlands"),
    (r"\b(mad|madrid)\b|\.es\.", "Spain"),
    (r"\b(mil|rome|milan)\b|\.it\.", "Italy"),
    (r"\b(iad|ash|nyc|lax|dfw|chi|atl)\b|\.us\.", "United States"),
    (r"\b(yyz|tor|toronto)\b|\.ca\.", "Canada"),
    (r"\b(syd|sydney|mel)\b|\.au\.", "Australia"),
    (r"\b(sin|singapore)\b|\.sg\.", "Singapore"),
    (r"\b(tyo|nrt|tokyo)\b|\.jp\.", "Japan"),
]
