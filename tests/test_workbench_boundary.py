from pathlib import Path


def test_browser_verification_is_read_only_and_covers_local_audit() -> None:
    script = Path("scripts/verify_workbench_browser.sh").read_text(encoding="utf-8")
    assert "Simulate escalation" in script
    assert "Reset my local records" in script
    assert "Simulated reviewer rationale" in script
    assert "agent-browser close" in script
    assert "POST" not in script
    assert "method:" not in script


def test_public_workbench_has_no_evaluation_or_local_source_client_route() -> None:
    frontend = Path("frontend/src/main.tsx").read_text(encoding="utf-8")
    assert "/api/elliptic" not in frontend
    assert "/api/evaluation" not in frontend
    assert "/api/metrics" not in frontend
