from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_public_routes_are_bounded_and_synthetic() -> None:
    assert client.get("/api/health").json()["request_inference"] is False
    cases = client.get("/api/cases").json()["items"]
    assert {item["id"] for item in cases} == {"sim-escalation-fanout", "sim-closure-compare"}
    assert len(client.get("/api/cases/sim-escalation-fanout/timeline?limit=2").json()["items"]) == 2
    assert len(client.get("/api/cases/sim-escalation-fanout/graph?depth=2").json()["nodes"]) <= 18
    provenance = client.get("/api/provenance").json()
    assert provenance["label"] == "realistic synthetic banking data"
    assert provenance["slice_sha256"] == "62b1d7476466f5456f61ef0d019db52536cf13e46e584724d5346a9ad8b75db2"


def test_local_research_is_not_exposed() -> None:
    assert client.get("/api/cases/unknown").status_code == 404
    assert client.get("/api/elliptic").status_code == 404
