"""Diagnostic parsers: traceroute, MTR, PingPlotter exports, ping, 8x8 utility tests."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

IP_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


def is_private_ip(ip: str) -> bool:
    return bool(
        re.match(r"^10\.", ip)
        or re.match(r"^192\.168\.", ip)
        or re.match(r"^172\.(1[6-9]|2\d|3[01])\.", ip)
        or re.match(r"^127\.", ip)
        or re.match(r"^169\.254\.", ip)
    )


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _status_word(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    if re.search(r"pass|ok|good|reachable|success", v, re.I):
        return "PASS"
    if re.search(r"warn", v, re.I):
        return "WARNING"
    if re.search(r"fail|block|error|bad", v, re.I):
        return "FAIL"
    return v.upper()


@dataclass
class Hop:
    hop: int
    host: str
    ip: Optional[str]
    loss: Optional[float]
    avg: Optional[float]
    best: Optional[float] = None
    worst: Optional[float] = None


@dataclass
class Traceroute:
    type: str
    hops: list[Hop]
    public_ips: list[str] = field(default_factory=list)


@dataclass
class Ping:
    type: str
    target: Optional[str]
    loss: float
    avg: Optional[float]


@dataclass
class Utility:
    type: str = "8x8-utility"
    dns: Optional[str] = None
    sbc: Optional[str] = None
    firewall: Optional[str] = None
    region: Optional[str] = None
    jitter: Optional[float] = None
    mos: Optional[float] = None
    ports: dict = field(default_factory=dict)
    public_ip: Optional[str] = None
    raw: dict = field(default_factory=dict)


def parse_traceroute(text: str) -> Optional[Traceroute]:
    hops: list[Hop] = []
    public_ips: set[str] = set()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # MTR style: "3.|-- 10.0.0.1  0.0%  5  1.2 1.3 1.0 1.5 0.1"
        m = re.match(
            r"^\s*(\d+)\.?\|?-+\s+(\S+)\s+([\d.]+)%\s+\d+\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
            line,
        )
        if m:
            host = m.group(2)
            ipm = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host)
            ip = ipm.group(0) if ipm else None
            if ip and not is_private_ip(ip):
                public_ips.add(ip)
            hops.append(Hop(int(m.group(1)), host, ip, float(m.group(3)),
                            float(m.group(5)), float(m.group(6)), float(m.group(7))))
            continue

        # Classic traceroute: "3  host (1.2.3.4)  12.3 ms 11.2 ms 13.1 ms"
        m = re.match(r"^\s*(\d+)\s+(.+)$", line)
        if m and re.search(r"\d+(\.\d+)?\s*ms", line, re.I):
            hop_no = int(m.group(1))
            rest = m.group(2)
            hostm = re.match(r"^([^\(\s]+)?\s*\(?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})?\)?", rest)
            host = hostm.group(1) if hostm and hostm.group(1) else "*"
            ip = hostm.group(2) if hostm and hostm.group(2) else None
            if host == "*" and ip:
                host = ip
            times = [float(x) for x in re.findall(r"([\d.]+)\s*ms", rest, re.I)]
            timeouts = len(re.findall(r"\*", rest))
            probes = len(times) + timeouts
            loss = round(timeouts / probes * 100, 1) if probes else (0.0 if times else 100.0)
            avg = round(sum(times) / len(times), 1) if times else None
            if ip and not is_private_ip(ip):
                public_ips.add(ip)
            hops.append(Hop(hop_no, host, ip, loss, avg,
                            min(times) if times else None, max(times) if times else None))
            continue

        # Timed-out hop "3  * * *"
        m = re.match(r"^\s*(\d+)\s+\*\s+\*\s+\*", line)
        if m:
            hops.append(Hop(int(m.group(1)), "*", None, 100.0, None, None, None))
            continue

        # PingPlotter / tabular: "3  core.virginmedia.net  4.2%  34.0"  (no 'ms')
        if re.match(r"^(hop|#)\b", line, re.I) or re.match(r"^target\s*:", line, re.I):
            continue
        m = re.match(r"^\s*(\d+)\s+(\S+)\s+([\d.]+)\s*%\s+([\d.]+)\s*(?:ms)?\s*$", line, re.I)
        if m:
            host = m.group(2)
            ipm = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host)
            ip = ipm.group(0) if ipm else None
            if ip and not is_private_ip(ip):
                public_ips.add(ip)
            avg = float(m.group(4))
            hops.append(Hop(int(m.group(1)), host, ip, float(m.group(3)), avg, avg, avg))

    if not hops:
        return None
    kind = "mtr" if any(h.worst is not None for h in hops) and re.search(r"mtr|loss%", text, re.I) else "traceroute"
    return Traceroute(kind, hops, sorted(public_ips))


def parse_ping(text: str) -> Optional[Ping]:
    if not re.search(r"ping|pinging|packets|round-trip|rtt", text, re.I):
        return None
    loss = avg = target = None
    m = re.search(r"(\d+(?:\.\d+)?)%\s*(?:packet\s*)?loss", text, re.I)
    if m:
        loss = float(m.group(1))
    m = re.search(r"(?:rtt|round-trip).*?=\s*[\d.]+/([\d.]+)/", text, re.I)
    if m:
        avg = float(m.group(1))
    if avg is None:
        m = re.search(r"Average\s*=\s*(\d+)ms", text, re.I)
        if m:
            avg = float(m.group(1))
    m = re.search(r"ping(?:ing)?\s+(\S+)", text, re.I)
    if m:
        target = re.sub(r"[:\[\]]", "", m.group(1))
    if loss is None and avg is None:
        return None
    return Ping("ping", target, 0.0 if loss is None else loss, avg)


def parse_8x8_utility(text: str) -> Optional[Utility]:
    data = None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    looks = re.search(r"8x8|utility test|sbc|reachability|media port|rtp|sip|jitter|mos", text, re.I)
    if data is None and not looks:
        return None

    u = Utility()
    if isinstance(data, dict):
        def g(*keys):
            for k in keys:
                if k in data and data[k] is not None:
                    return data[k]
            return None
        u.dns = g("dns")
        u.sbc = g("sbc", "reachability")
        u.region = g("region", "location")
        u.public_ip = g("publicIp", "public_ip", "wanIp")
        u.jitter = _num(g("jitter"))
        u.mos = _num(g("mos"))
        u.ports = data.get("ports", {}) or {}
        u.firewall = data.get("firewall")
        u.raw = data

    def grab(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None

    u.dns = u.dns or _status_word(grab(r"DNS[:\s]+([A-Za-z]+)"))
    u.sbc = u.sbc or _status_word(grab(r"(?:SBC|Reachability)[:\s]+([A-Za-z]+)"))
    u.region = u.region or grab(r"(?:Region|Location|Country)[:\s]+([A-Za-z ]+)")
    u.public_ip = u.public_ip or grab(r"Public\s*IP[:\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    if u.jitter is None:
        u.jitter = _num(grab(r"Jitter[:\s]+([\d.]+)"))
    if u.mos is None:
        u.mos = _num(grab(r"MOS[:\s]+([\d.]+)"))

    def port_status(label, pattern):
        m = re.search(pattern, text, re.I)
        if m:
            u.ports[label] = "open" if re.search(r"open|allow|pass|ok|reachable", m.group(0), re.I) else "blocked"

    port_status("5060", r"5060[^\n]*?(open|allow|pass|ok|reachable|block|closed|fail|filter)")
    port_status("5061", r"5061[^\n]*?(open|allow|pass|ok|reachable|block|closed|fail|filter)")
    port_status("rtp", r"(rtp|media|10000[\- ]?30000)[^\n]*?(open|allow|pass|ok|reachable|block|closed|fail|filter)")
    port_status("443", r"443[^\n]*?(open|allow|pass|ok|reachable|block|closed|fail|filter)")
    return u


@dataclass
class Evidence:
    traceroutes: list[Traceroute] = field(default_factory=list)
    pings: list[Ping] = field(default_factory=list)
    utilities: list[Utility] = field(default_factory=list)
    public_ips: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    raw_text: str = ""


def parse_all(inputs: list[dict]) -> Evidence:
    """inputs: [{"name": str, "text": str}]"""
    ev = Evidence()
    pub: set[str] = set()
    for inp in inputs:
        text = inp.get("text", "") or ""
        ev.sources.append(inp.get("name", "input"))
        util = parse_8x8_utility(text)
        if util:
            ev.utilities.append(util)
            if util.public_ip:
                pub.add(util.public_ip)
        tr = parse_traceroute(text)
        if tr:
            ev.traceroutes.append(tr)
            pub.update(tr.public_ips)
        pg = parse_ping(text)
        if pg:
            ev.pings.append(pg)
        for ip in IP_RE.findall(text):
            if not is_private_ip(ip):
                pub.add(ip)
    ev.public_ips = sorted(pub)
    ev.raw_text = "\n".join(i.get("text", "") for i in inputs)
    return ev
