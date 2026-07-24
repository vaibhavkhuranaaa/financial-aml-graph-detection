from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_public_api_is_synthetic_and_bounded() -> None:
    assert client.get("/api/health").json()["mode"] == "public-synthetic-fixture"
    assert len(client.get("/api/queue?limit=2").json()["items"]) == 2
    graph = client.get("/api/graph/case-017?depth=2").json()
    assert graph["bounded"] is True
    assert len(graph["nodes"]) <= 18


def test_unknown_case_is_not_exposed() -> None:
    assert client.get("/api/cases/not-a-case").status_code == 404
