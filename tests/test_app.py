from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_public_routes_are_bounded_and_synthetic() -> None:
    assert client.get("/api/health").json()["request_inference"] is False
    assert client.get("/api/cases").status_code == 503


def test_local_research_is_not_exposed() -> None:
    assert client.get("/api/cases/unknown").status_code == 503
    assert client.get("/api/elliptic").status_code == 404
