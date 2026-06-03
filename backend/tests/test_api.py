import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "nexus_test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

# fresh schema per test session
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

ISP = {
    "inputs": [
        {"name": "pingplotter.txt", "text": "Target: lon.8x8.com\nHop IP Loss% Avg\n"
         "  3  core.virginmedia.net 4.2% 34.0\n  5  edge.lon.8x8.com 4.6% 286.0"},
        {"name": "u.txt", "text": "8x8 Utility Test\nCustomer: Acme Corp\nRegion: United Kingdom\nPublic IP: 81.2.3.4"},
    ],
    "siteId": "Acme Corp · London",
}
WRONGDC = {
    "inputs": [
        {"name": "t.txt", "text": "traceroute to fra.8x8.com\n 4  edge.fra.8x8.com  28.0 ms 28.0 ms 28.0 ms"},
        {"name": "u.txt", "text": "8x8 Utility Test\nRegion: United Kingdom\nDNS: WARNING\nPublic IP: 62.5.5.5"},
    ],
    "siteId": "Acme Corp · London",
    "regionOverride": "United Kingdom",
}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_meta():
    assert "United Kingdom" in client.get("/meta/regions").json()
    assert len(client.get("/meta/datacentres").json()) > 5
    assert len(client.get("/meta/samples").json()) == 5


def test_analyze_and_store():
    r = client.post("/analyze", json=ISP).json()
    assert r["analysis"]["health"] == "critical"
    assert r["caseId"] is not None


def test_grouping_collapses_same_site():
    client.post("/analyze", json=ISP)
    client.post("/analyze", json=WRONGDC)
    groups = client.get("/cases/grouped").json()
    acme = [g for g in groups if g["site"] == "Acme Corp · London"]
    assert acme, "Acme group should exist"
    g = acme[0]
    assert g["count"] >= 2
    # both pingplotter and traceroute evidence present under one site
    assert "PINGPLOTTER" in g["evidenceTypes"]
    assert "TRACE" in g["evidenceTypes"]
