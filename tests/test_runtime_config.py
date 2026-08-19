import pytest
from fastapi.testclient import TestClient

from src.app import app, runtime_config


def test_runtime_config_is_public_synthetic_and_fail_closed_for_cors() -> None:
    config = runtime_config({"APP_MODE": "public-synthetic-fixture"})
    assert config.app_mode == "public-synthetic-fixture"
    assert config.cors_origins == ()


def test_runtime_config_accepts_only_explicit_http_cors_origins() -> None:
    config = runtime_config(
        {
            "APP_MODE": "public-synthetic-fixture",
            "SIGNAL_LEDGER_CORS_ORIGINS": "https://workbench.example,http://localhost:5173",
        }
    )
    assert config.cors_origins == (
        "https://workbench.example",
        "http://localhost:5173",
    )
    with pytest.raises(RuntimeError, match="allowlist"):
        runtime_config(
            {
                "APP_MODE": "public-synthetic-fixture",
                "SIGNAL_LEDGER_CORS_ORIGINS": "*",
            }
        )


def test_runtime_config_accepts_the_local_triage_workbench_mode() -> None:
    """The mode an operator runs on their own machine.

    It changes exactly one thing: the triage artifact is admitted without an
    approved distribution decision. Everything else, including the replay
    artifact's admission check and the CORS allowlist, is unchanged, and it is
    never the deployed mode.
    """
    config = runtime_config({"APP_MODE": "local-triage-workbench"})
    assert config.app_mode == "local-triage-workbench"
    assert config.cors_origins == ()


def test_runtime_config_rejects_any_other_application_mode() -> None:
    for mode in ("research", "public", "local", "local-triage", ""):
        with pytest.raises(RuntimeError, match="APP_MODE"):
            runtime_config({"APP_MODE": mode})


def test_default_public_service_cors_denies_cross_origin_requests() -> None:
    response = TestClient(app).options(
        "/api/health",
        headers={
            "Origin": "https://unapproved.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
