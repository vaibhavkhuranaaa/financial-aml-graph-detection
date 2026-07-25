from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

CASE_ID = "sim-escalation-fanout"
PUBLIC_GET_ROUTES = {
    "/api/health",
    "/api/readiness",
    "/api/cases",
    "/api/cases/{case_id}",
    "/api/cases/{case_id}/timeline",
    "/api/cases/{case_id}/graph",
    "/api/cases/{case_id}/evidence",
    "/api/provenance",
    "/api/methodology",
}


def test_public_contracts_are_typed_bounded_and_synthetic() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "mode": "public-ibm-synthetic-scenario",
        "request_inference": False,
        "read_only": True,
    }
    assert client.get("/api/readiness").json()["visitor_persistence"] is False

    cases = client.get("/api/cases").json()
    assert {item["id"] for item in cases["items"]} == {
        "sim-escalation-fanout",
        "sim-closure-compare",
    }
    assert cases["maximum"] == 2
    assert (
        client.get(f"/api/cases/{CASE_ID}").json()["rationale"]
        == "Simulated analyst rationale is stored only in this browser."
    )

    timeline = client.get(f"/api/cases/{CASE_ID}/timeline?rail=Cheque&limit=2").json()
    assert len(timeline["items"]) == 2
    assert {item["rail"] for item in timeline["items"]} == {"Cheque"}

    topology = client.get(f"/api/cases/{CASE_ID}/graph?depth=2").json()
    assert topology["bounded"] is True
    assert len(topology["nodes"]) <= 18
    assert len(topology["edges"]) <= 18

    evidence = client.get(f"/api/cases/{CASE_ID}/evidence").json()
    assert {item["kind"] for item in evidence["items"]} == {"replay", "boundary"}
    provenance = client.get("/api/provenance").json()
    assert provenance["label"] == "realistic synthetic banking data"
    assert (
        provenance["slice_sha256"]
        == "62b1d7476466f5456f61ef0d019db52536cf13e46e584724d5346a9ad8b75db2"
    )
    assert (
        "No rows, graphs, or metrics are public."
        in client.get("/api/methodology").json()["elliptic"]
    )


def test_invalid_and_boundary_parameters_return_stable_safe_errors() -> None:
    assert client.get(f"/api/cases/{CASE_ID}/timeline?limit=18").status_code == 200
    assert client.get(f"/api/cases/{CASE_ID}/graph?depth=1").status_code == 200
    for path in (
        f"/api/cases/{CASE_ID}/timeline?limit=0",
        f"/api/cases/{CASE_ID}/timeline?limit=19",
        f"/api/cases/{CASE_ID}/timeline?limit=two",
        f"/api/cases/{CASE_ID}/timeline?rail=wire",
        f"/api/cases/{CASE_ID}/graph?depth=0",
        f"/api/cases/{CASE_ID}/graph?depth=3",
        "/api/cases/elliptic",
    ):
        response = client.get(path)
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid request parameters."}
    missing = client.get("/api/cases/sim-unknown-case")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Public simulated case not found."}


def test_public_route_allowlist_and_forbidden_inputs() -> None:
    api_routes = {route.path for route in app.routes if route.path.startswith("/api/")}
    assert api_routes == PUBLIC_GET_ROUTES
    for path in (
        "/api/elliptic",
        "/api/local-source",
        "/api/research",
        "/api/cases/../../data/provenance/ibm_aml_data_v8_source.json",
        "/docs",
        "/openapi.json",
    ):
        assert client.get(path).status_code == 404
    for path in ("/api/cases", f"/api/cases/{CASE_ID}/evidence", "/api/provenance"):
        assert (
            client.post(
                path, json={"visitor_note": "persist this", "infer": True}
            ).status_code
            == 405
        )
