from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_public_routes_are_bounded_and_synthetic() -> None:
    assert client.get("/api/health").json()["request_inference"] is False
    cases = client.get("/api/cases").json()["items"]
    assert {item["id"] for item in cases} == {"sim-escalation-fanout", "sim-closure-compare"}
    assert len(client.get("/api/cases/sim-escalation-fanout/timeline?limit=2").json()["items"]) == 2
    assert len(client.get("/api/cases/sim-escalation-fanout/graph?depth=2").json()["nodes"]) <= 18


def test_local_research_is_not_exposed() -> None:
    assert client.get("/api/cases/unknown").status_code == 404
    assert client.get("/api/elliptic").status_code == 404
