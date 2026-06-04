import json

from app.engine import analyse

HEALTHY = [
    {"name": "mtr.txt", "text":
        "HOST: northwind-pc  Loss%   Snt   Last   Avg  Best  Wrst StDev\n"
        "  1.|-- 192.168.1.1  0.0%  10  0.8  0.9  0.7  1.2  0.1\n"
        "  3.|-- core1.lon.bt.net  0.0%  10  9.2  9.5  9.0  10.1  0.3\n"
        "  4.|-- ae0.edge.lon.8x8.com  0.0%  10  11.3  11.6  11.0  12.4  0.4"},
    {"name": "u.json", "text": json.dumps({"customer": "Northwind Trading", "region": "United Kingdom",
        "publicIp": "62.10.20.30", "dns": "PASS", "jitter": 8, "mos": 4.3,
        "ports": {"5060": "open", "rtp": "open"}})},
]

ISP = [
    {"name": "pingplotter.txt", "text":
        "Target: lon.8x8.com\nHop IP Loss% Avg\n"
        "  3  core.virginmedia.net 4.2% 34.0\n  4  peer.virginmedia.net 4.5% 120.0\n"
        "  5  edge.lon.8x8.com 4.6% 286.0"},
    {"name": "u.txt", "text": "8x8 Utility Test\nCustomer: Acme Corp\nRegion: United Kingdom\n"
        "Public IP: 81.2.3.4\nJitter: 42\nMOS: 3.2"},
]

FIREWALL = [{"name": "u.json", "text": json.dumps({"customer": "Berlin Logistics GmbH", "region": "Germany",
    "publicIp": "91.10.10.10", "dns": "PASS", "ports": {"5060": "open", "rtp": "blocked"}})}]

WRONGDC = [
    {"name": "t.txt", "text": "traceroute to fra.8x8.com\n 4  edge.fra.8x8.com  28.0 ms 28.1 ms 27.9 ms"},
    {"name": "u.txt", "text": "8x8 Utility Test\nCustomer: Acme Corp\nRegion: United Kingdom\nDNS: WARNING\nPublic IP: 62.5.5.5"},
]

LAN = [
    {"name": "mtr.txt", "text":
        "HOST: riverside-pc  Loss%   Snt   Last   Avg  Best  Wrst StDev\n"
        "  1.|-- 192.168.1.1  6.0%  10  12.0  45.0  2.0  180.0  60.1\n"
        "  2.|-- 10.0.0.1  5.8%  10  10.0  10.5  9.0  12.0  1.0\n"
        "  3.|-- core.lon.bt.net  0.0%  10  9.0  9.2  8.9  10.0  0.3"},
    {"name": "u.txt", "text": "Customer: Riverside Dental\nRegion: United Kingdom"},
]


def test_healthy():
    r = analyse(HEALTHY)
    assert r["health"] == "healthy"
    assert r["site"] == "Northwind Trading"
    assert r["fixes"] == []


def test_isp_packet_loss_is_root_cause():
    r = analyse(ISP)
    assert r["health"] == "critical"
    assert r["findings"][0]["kind"] == "packet-loss"
    assert "ISP" in r["findings"][0]["area"]
    assert r["isp"] and "Virgin" in r["isp"]["name"]
    assert r["escalation"]["ready"] is True
    assert r["site"] == "Acme Corp"


def test_firewall():
    r = analyse(FIREWALL)
    assert r["health"] == "critical"
    assert r["findings"][0]["kind"] == "firewall"
    assert r["geo"]["region"] == "Germany"
    assert r["site"] == "Berlin Logistics GmbH"


def test_wrong_datacentre_with_override():
    r = analyse(WRONGDC, region_override="United Kingdom")
    assert r["geo"]["method"] == "Agent Override"
    assert r["geo"]["actualDc"] == "Frankfurt (FRA)"
    # a datacentre-mismatch finding must exist
    assert any(f["kind"] == "datacentre" for f in r["findings"])


def test_lan_loss():
    r = analyse(LAN)
    assert r["health"] == "critical"
    assert r["findings"][0]["area"] == "LAN"
    assert "within the customer LAN" in r["rootCause"]


def test_review_flag_healthy_not_needed():
    r = analyse(HEALTHY)
    assert r["reviewFlag"]["needed"] is False
    assert [i["name"] for i in r["rawInputs"]] == ["mtr.txt", "u.json"]


def test_review_flag_thin_evidence_needed():
    r = analyse([{"name": "p.txt", "text": "pinging 8.8.8.8\n4% packet loss\nAverage = 120ms"}])
    assert r["reviewFlag"]["needed"] is True
    assert any("single piece of evidence" in x for x in r["reviewFlag"]["reasons"])


def test_latency_is_region_aware():
    r = analyse([{"name": "p.txt", "text": "pinging lon.8x8.com\n0% packet loss\nAverage = 142ms"}],
                region_override="United Kingdom")
    lat = [f for f in r["findings"] if f["kind"] == "latency"]
    assert lat
    assert "UK-to-UK" in lat[0]["rootCause"]
    assert "<50ms" in lat[0]["rootCause"]
