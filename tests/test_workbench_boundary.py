from pathlib import Path


def test_browser_verification_is_read_only_and_covers_local_audit() -> None:
    script = Path("scripts/verify_workbench_browser.sh").read_text(encoding="utf-8")
    assert "Simulate escalation" in script
    assert "Reset my local records" in script
    assert "Simulated reviewer rationale" in script
    assert '"$browser_cli" close' in script
    assert "POST" not in script
    assert "method:" not in script


def test_triage_verification_is_read_only_and_covers_the_states_that_matter() -> None:
    script = Path("scripts/verify_triage_browser.sh").read_text(encoding="utf-8")
    for check in (
        "BASELINE_WINS_RENDERED",
        "STRUCTURAL_ZERO_RENDERED",
        "CLAIMS_COPY_PRESENT",
        "DEFERRED_ALERTS_VISIBLE",
        "RANK_HAS_NO_COLOUR_SCALE",
        "DISPOSITION_CARRIES_NO_DEFAULT",
        "CONSEQUENCE_RESTATED",
        "BASELINE_IN_PLACE",
    ):
        assert check in script
    assert "POST" not in script
    assert "method:" not in script


def frontend_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(Path("frontend/src").glob("*.tsx"))
    )


def test_public_workbench_has_no_evaluation_or_local_source_client_route() -> None:
    frontend = frontend_sources()
    assert "/api/elliptic" not in frontend
    assert "/api/evaluation" not in frontend
    assert "/api/metrics" not in frontend


def test_the_client_never_writes_and_never_asks_for_a_score() -> None:
    """The triage desk does arithmetic over a fixed table and nothing else.

    A write, or a request carrying a visitor supplied value to be scored, is the
    boundary this project is built around. The client has neither.
    """
    frontend = frontend_sources()
    for forbidden in ('method: "POST"', "method: 'POST'", "/api/score", "/api/predict"):
        assert forbidden not in frontend


def test_the_triage_surface_carries_the_claims_line_and_the_deferred_wording() -> None:
    """Copy the design language fixes, in the same visual field as the rank."""
    triage = Path("frontend/src/triage.tsx").read_text(encoding="utf-8")
    assert "period.claims" in triage
    assert "Not reached at this capacity" in triage
    assert "Structural zero" in triage
    # Deferred, never dismissed.
    for forbidden in ("Excluded", "Cleared", "Filtered out", "Low risk"):
        assert forbidden not in triage


def test_default_surface_is_the_approved_replay() -> None:
    """The replay is what a visitor lands on. The triage desk is an explicit ask.

    The triage desk is approved for one review period, so the surface that opens
    by default is still the replay and the queue is reached deliberately.
    """
    main = Path("frontend/src/main.tsx").read_text(encoding="utf-8")
    assert 'get("surface")' in main
    assert 'surface === "triage" ? <TriageApp /> : <App />' in main
    assert "One approved review period" in main


def test_the_triage_surface_states_the_scope_of_its_approval() -> None:
    """An approval that does not say what it covers reads as covering everything."""
    main = Path("frontend/src/main.tsx").read_text(encoding="utf-8")
    for bound in ("HI-Small variant, and for nothing else", "LI-Small", "stay local"):
        assert bound in main


def test_rank_carries_no_colour_in_the_stylesheet() -> None:
    """No bar, no heat scale, no gradient, and no tint keyed to position.

    A colour scale invites rank to be read as a probability or a severity, and it
    is neither. The rank cell is monospace, right aligned and unstyled.
    """
    styles = Path("frontend/src/styles.css").read_text(encoding="utf-8")
    rank_rule = next(
        line for line in styles.splitlines() if line.startswith(".queue-row .rank")
    )
    assert "gradient" not in rank_rule
    assert "background" not in rank_rule
    assert "#edf2df" in rank_rule
