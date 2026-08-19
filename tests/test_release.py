import json
from pathlib import Path

from scripts.verify_release import validate_local


def test_release_manifest_pins_the_approved_public_replay() -> None:
    result = validate_local()
    assert result["cases"] == 6
    assert result["transactions"] == 55


def test_release_pins_the_approved_triage_period_and_its_scope() -> None:
    """The triage artifact ships, bounded to the one period the owner approved."""
    result = validate_local()
    assert result["triage_alerts"] == 749
    release = json.loads(Path("release-manifest.json").read_text(encoding="utf-8"))
    assert release["product"] == "public-replay-and-approved-triage-period"
    assert release["triage_artifact"]["review_periods"] == 1
    assert release["triage_artifact"]["period_start"] == "2022-09-07"
    assert release["public_contract"]["refused_routes"] == []
    assert "/api/triage/period" in release["public_contract"]["required_routes"]


def test_container_context_excludes_local_research_artifacts() -> None:
    """The approved artifacts ship in the image. Everything upstream does not."""
    ignored = set(Path(".dockerignore").read_text(encoding="utf-8").splitlines())
    assert "data/fixtures/public_triage.json" not in ignored
    assert "data/raw" in ignored
    assert "data/alerts" in ignored
    assert "data/features" in ignored
    assert "data/backtest" in ignored
