"""The triage artifact and the surface that serves it.

Four properties carry the milestone and each has a test that fails when it
breaks: the tuned rule parameters never reach the payload, every alert in the
period is present in every ordering including the ones below the cut line, the
public service refuses an artifact that carries no approved distribution
decision, and it also refuses an approved artifact that is not the pinned
release, so an unreviewed rebuild cannot serve itself on an inherited flag.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import polars as pl
import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.pipeline import alert_store, backtest, features, ranker, rules, triage
from src.triage_artifact import admitted_triage_artifact
from tests.test_rules import JURISDICTIONS, txn, txns

PERIOD = date(2022, 9, 5)

# Parameters loosened so the small fixture fires rules at all. The alert store's
# parameter hash follows the set that built it, which is what keeps a fixture
# store from being mistaken for the measured one.
PARAMS = rules.Parameters().replace(
    r3_min_originators=2, r4_min_beneficiaries=2, r1_min_count=2, r5_min_count=2
)

BACKTEST_RECORD = {
    "k": 3,
    "reference_rung": "B2",
    "pooled": [
        {"rung": "B0", "periods": 2, "worked": 6, "true_positives": 1, "precision": 0.1667},
        {"rung": "B1", "periods": 2, "worked": 6, "true_positives": 2, "precision": 0.3333},
        {"rung": "B2", "periods": 2, "worked": 6, "true_positives": 3, "precision": 0.5},
        {"rung": "B3", "periods": 2, "worked": 6, "true_positives": 2, "precision": 0.3333},
        {"rung": "C1", "periods": 2, "worked": 6, "true_positives": 3, "precision": 0.5},
    ],
    "precision_intervals": {
        "B0": [0.0, 0.4],
        "B1": [0.1, 0.6],
        "B2": [0.2, 0.8],
        "B3": [0.1, 0.6],
        "C1": [0.2, 0.8],
    },
    "lift": [
        {"rung": "C1", "against": "B0", "lift": 3.0},
        {"rung": "C1", "against": "B2", "lift": 1.0},
    ],
    "lift_intervals": {"B0": [1.5, 5.0], "B2": [0.8, 1.3]},
    "per_period": [
        {
            "rung": rung,
            "period_start": period,
            "worked": 3,
            "true_positives": tp,
            "period_alerts": alerts,
            "precision": tp / 3,
        }
        for period, alerts in (("2022-09-04", 13), ("2022-09-05", 21))
        for rung, tp in (("B0", 1), ("B1", 1), ("B2", 2), ("B3", 1), ("C1", 2))
    ],
    "typology_recall": [
        {
            "rung": rung,
            "typology": typology,
            "attempts": attempts,
            "attempts_surfaced": surfaced,
            "attempts_recovered": 1 if rung == "C1" and surfaced else 0,
            "recall": (1 / attempts) if rung == "C1" and surfaced else 0.0,
            "recall_of_surfaced": (1 / surfaced) if rung == "C1" and surfaced else 0.0,
        }
        for rung in ("B0", "B1", "B2", "B3", "C1")
        for typology, attempts, surfaced in (("FAN-OUT", 4, 2), ("STACK", 3, 0))
    ],
    "recall_intervals": {"C1|FAN-OUT": [0.0, 0.5], "C1|STACK": [0.0, 0.0]},
    "unattributed": [
        {
            "rung": rung,
            "typology": "UNATTRIBUTED",
            "alerts_in_population": 5,
            "alerts_recovered": recovered,
        }
        for rung, recovered in (("B0", 1), ("B1", 1), ("B2", 2), ("B3", 1), ("C1", 3))
    ],
    # One period frees volume and one costs it, so the sign is exercised.
    "volume_reduction": [
        {
            "period_start": "2022-09-04",
            "period_alerts": 13,
            "worked": 3,
            "attempts_depth": 5,
            "alerts_depth": 2,
            "attempts_target": 1,
            "alerts_target": 2,
            "attempts_freed": -2,
            "alerts_freed": 1,
            "target_was_zero": False,
        },
        {
            "period_start": "2022-09-05",
            "period_alerts": 21,
            "worked": 3,
            "attempts_depth": 1,
            "alerts_depth": 1,
            "attempts_target": 0,
            "alerts_target": 2,
            "attempts_freed": 2,
            "alerts_freed": 2,
            "target_was_zero": True,
        },
    ],
    "volume_reduction_pooled": 0.5,
    "rank_stability": [{"period_start": "2022-09-05", "alerts": 21, "spearman": 0.91}],
    "importance": [
        {"feature": f"feature_{index}", "gain": 512.5 - index * 7.3} for index in range(20)
    ],
}

SOURCE_MANIFEST = {
    "provider": "IBM / Erik Altman",
    "dataset": "IBM Transactions for Anti Money Laundering (AML)",
    "dataset_version": 8,
    "source_ref": "https://example.invalid/source",
    "retrieved_at": "2026-08-12T00:00:00Z",
    "source_file": "HI-Small_Trans.csv",
    "source_sha256": "0" * 64,
    "license": "CDLA-Sharing-1.0",
    "license_url": "https://cdla.dev/sharing-1-0/",
}

OPERATING_POINT = {
    "analysts": 2,
    "productive_hours_per_analyst": 1.0,
    "handling_minutes_per_alert": 20.0,
    "k_alerts_worked_per_period": 3,
    "assumption_note": "Assumptions, not measurements.",
}

APPROVED_SOURCE_SHA256 = "b19d39f515523373f991b689c07e11e7b0b95c17a2c27a87d91584ae16c5b040"
APPROVED = {"public_distribution_status": "approved"}
UNAPPROVED = {"public_distribution_status": "pending_owner_approval"}


SUBJECTS = ("A", "B", "C", "D", "E")


def fixture_transactions() -> pl.DataFrame:
    """Five days of activity where every subject fans out on every day.

    Five subjects and a cut line of three alerts, so the published period has
    alerts on both sides of the line and the queue can be checked for the ones
    below it.
    """
    rows = []
    identifier = 0
    for day in range(1, 6):
        for position, subject in enumerate(SUBJECTS):
            for index, receiver in enumerate(("P", "Q", "R")):
                rows.append(
                    txn(
                        identifier,
                        (position * 3 + index) % 24,
                        subject,
                        f"{subject}{receiver}{day}",
                        9_200.0 + position * 100 + index,
                        day=day,
                    )
                )
                identifier += 1
    return txns(rows)


def artifact(distribution: dict) -> dict:
    frame = fixture_transactions()
    rows = rules.run_rules(frame, JURISDICTIONS, PARAMS)
    alerts = alert_store.build_alerts(rows, PARAMS)
    built = features.build_features(alerts, frame)
    # Two flagged transactions in the published period, one of them attributed
    # to an injected attempt so a typology has something to recover.
    labels = pl.DataFrame(
        {
            "txn_id": pl.Series([10, 11], dtype=pl.UInt32),
            rules.PERIOD: [PERIOD, PERIOD],
            "attempt_id": [7, None],
            "typology": ["FAN-OUT", None],
        },
        schema_overrides={"attempt_id": pl.Int64, "typology": pl.String},
    )
    prepared = backtest.prepare(alerts, frame, labels)
    universe = backtest.attempt_universe(prepared, labels, date(2022, 9, 4))
    stamp = pl.Series([PERIOD]).cast(pl.Datetime("us"))[0]
    period_alerts = prepared.filter(pl.col("period_start") == stamp)
    period_universe = triage.period_attempt_universe(period_alerts, labels, PERIOD)
    columns = features.feature_columns(built)
    booster = ranker.train(ranker.training_frame(built, prepared, PERIOD), columns, rounds=5)
    scores = ranker.score(booster, built.filter(pl.col("period_start") == stamp), columns)
    return triage.build_artifact(
        alerts=alerts,
        txns=frame,
        prepared=prepared,
        built=built,
        universe=universe,
        period_universe=period_universe,
        period=PERIOD,
        scores=scores,
        booster=booster,
        backtest_record=BACKTEST_RECORD,
        source_manifest=SOURCE_MANIFEST,
        distribution=distribution,
        operating_point=OPERATING_POINT,
    )


def test_the_tuned_rule_parameters_never_reach_the_payload():
    """The one property a public surface cannot get back once it is wrong.

    Every rule writes both the quantities that met its trigger and the parameters
    that set it into the same evidence blob. The published quantity list is an
    allowlist, so a parameter added to a rule later is dropped by default rather
    than carried by default.
    """
    payload = artifact(UNAPPROVED)
    queue = json.dumps(payload["alerts"])
    for parameter in (
        "threshold",
        "band",
        "tolerance",
        "minimum_counterparties",
        "minimum_amount",
        "multiple",
        "lookback_periods",
    ):
        assert parameter not in queue
    # The published quantities are exactly the allowlist, per rule.
    for alert in payload["alerts"]:
        for evidence in alert["trigger_evidence"]:
            keys = {quantity["key"] for quantity in evidence["quantities"]}
            assert keys <= set(triage.PUBLISHABLE_EVIDENCE[evidence["rule_id"]])
    # The distinctive tuned values are absent from the whole payload, not only
    # from the evidence blocks that carry their names.
    whole = json.dumps(payload)
    for value in (PARAMS.r1_threshold, PARAMS.r1_band, PARAMS.r2_tolerance, PARAMS.r5_min_amount):
        assert f": {value}" not in whole


def test_the_funnel_states_where_the_attempts_are_lost():
    """The bound on every ranking number in the project.

    Attempts the rules never surfaced cannot be recovered by any ordering, so the
    surfaced count is the ceiling the ranking layer competes against. If this
    arithmetic ever stops holding, a reader would conclude the ordering is losing
    attempts it never had access to.
    """
    funnel = artifact(UNAPPROVED)["evidence"]["funnel"]
    assert funnel["attempts_surfaced"] <= funnel["attempts_live"]
    assert funnel["lost_before_ordering"] == (
        funnel["attempts_live"] - funnel["attempts_surfaced"]
    )
    for rung, reached in funnel["attempts_reached"].items():
        assert reached <= funnel["attempts_surfaced"], rung


def test_both_recall_denominators_travel_together():
    """Recall of live scores the rules. Recall of surfaced scores the ordering.

    Carrying only the first is what makes a coverage failure read as a ranking
    failure, so the payload has to hold both on every typology and the surfaced
    denominator can never exceed the live one.
    """
    detail = artifact(UNAPPROVED)["evidence"]["typology_detail"]
    assert detail
    for row in detail:
        assert row["attempts_surfaced"] <= row["attempts_live"]
        assert 0.0 <= row["recall_of_live"] <= 1.0
        assert 0.0 <= row["recall_of_surfaced"] <= 1.0
        if row["attempts_surfaced"]:
            # A denominator that is smaller cannot produce a smaller rate.
            assert row["recall_of_surfaced"] >= row["recall_of_live"]
        else:
            assert row["recall_of_surfaced"] == 0.0


def test_a_period_that_cost_volume_keeps_its_negative_sign():
    """The volume claim survives scrutiny only because it is not pooled alone.

    A negative freed figure means the challenger cost more volume than the
    reference at equal coverage. Two of the seven measured periods do exactly
    that, and a payload that dropped or clamped the sign would turn an honest
    number into a flattering one.
    """
    volume = artifact(UNAPPROVED)["evidence"]["volume_reduction"]
    assert volume["per_period"]
    assert any(row["attempts_freed"] < 0 for row in volume["per_period"])
    assert any(row["target_was_zero"] for row in volume["per_period"])


def test_the_evidence_block_carries_no_rule_internals():
    """Feature names are model features. Prior hit rates are closer to triggers.

    The B3 per rule prior hit rates are what the rules only priority ordering is
    built from, and they sit nearer the tuned trigger set than to a published
    result, so they stay out of the payload.
    """
    payload = artifact(UNAPPROVED)
    whole = json.dumps(payload)
    assert "b3_hit_rates" not in whole
    assert "hit_rate" not in whole
    assert "observed_rate" not in whole
    importance = payload["evidence"]["feature_importance"]
    # The list is bounded and says so, with the true count beside it.
    assert importance["carried"] <= triage.MAX_IMPORTANCE_FEATURES
    assert len(importance["top"]) == importance["carried"]
    assert importance["features_in_model"] >= importance["carried"]
    assert str(importance["features_in_model"]) in importance["bound_note"]


def test_the_evidence_route_serves_the_measured_run(monkeypatch, tmp_path):
    client = serve(monkeypatch, tmp_path, app_module.LOCAL_TRIAGE_MODE, UNAPPROVED)
    body = client.get("/api/triage/evidence").json()
    assert body["request_inference"] is False
    assert body["reference_rung"] == BACKTEST_RECORD["reference_rung"]
    evidence = body["evidence"]
    assert evidence["funnel"]["attempts_live"] >= evidence["funnel"]["attempts_surfaced"]
    assert evidence["per_period"]
    for row in evidence["per_period"]:
        assert 0.0 < row["coverage"] <= 1.0
    assert evidence["unattributed"]["alerts_in_population"] > 0
    assert evidence["rank_stability"]["threshold"] == 0.70


def test_every_ordering_covers_the_whole_period_with_no_gap():
    """The cut line only means something if nothing is removed from the queue."""
    payload = artifact(UNAPPROVED)
    total = payload["period"]["alerts"]
    assert total == len(payload["alerts"])
    for ordering in triage.LADDER_AND_CHALLENGER:
        positions = sorted(alert["ranks"][ordering] for alert in payload["alerts"])
        assert positions == list(range(1, total + 1))


def test_accounts_are_pseudonymised_and_transactions_are_bounded_with_their_count():
    payload = artifact(UNAPPROVED)
    serialised = json.dumps(payload)
    assert "1|A" not in serialised
    for alert in payload["alerts"]:
        assert alert["subject"].startswith("Party-")
        assert len(alert["contributing_transactions"]) <= triage.MAX_CONTRIBUTING_TRANSACTIONS
        assert alert["contributing_transaction_count"] >= len(alert["contributing_transactions"])


def test_structural_zeros_are_carried_with_a_reason_and_never_dropped():
    payload = artifact(UNAPPROVED)
    catalogue = {rule["rule_id"]: rule for rule in payload["rules"]}
    assert set(catalogue) == {f"R{index}" for index in range(1, 9)}
    for rule_id in ("R1", "R5", "R6", "R7", "R8"):
        assert catalogue[rule_id]["supported"] is False
        assert catalogue[rule_id]["attempts"] == 0
        # The volume is a real analyst cost and stays on the row.
        assert "alerts_in_store" in catalogue[rule_id]
    assert catalogue["R4"]["supported"] is True
    assert [typology["typology"] for typology in payload["typologies"]] == backtest.INJECTED_TYPOLOGIES


def test_the_period_and_evaluation_denominators_are_reported_separately():
    """A single period's recall read against a seven period denominator flatters."""
    payload = artifact(UNAPPROVED)
    for typology in payload["typologies"]:
        assert typology["in_period"]["attempts_live"] <= typology["across_evaluation"]["attempts_live"]
        assert typology["in_period"]["attempts_surfaced"] <= typology["in_period"]["attempts_live"]
    fan_out = next(item for item in payload["typologies"] if item["typology"] == "FAN-OUT")
    assert fan_out["in_period"]["attempts_live"] == 1
    assert {attempt["typology"] for attempt in payload["period_attempts"]} == {"FAN-OUT"}


def test_the_measured_result_travels_with_the_surface():
    payload = artifact(UNAPPROVED)
    gate = payload["result"]["gate"]
    assert gate["reference_rung"] == "B2"
    assert gate["threshold"] == 1.3
    assert gate["met"] is False
    assert gate["promoted"] is False
    assert {row["ordering"] for row in payload["result"]["measured"]} == set(
        triage.LADDER_AND_CHALLENGER
    )


def test_an_unapproved_artifact_is_refused_for_publication_and_served_locally(tmp_path):
    path = triage.write_artifact(artifact(UNAPPROVED), tmp_path / "triage.json")
    with pytest.raises(ValueError, match="no approved distribution decision"):
        triage.approved_artifact(path)
    local = admitted_triage_artifact(path, require_approval=False)
    assert local["provenance"]["distribution"]["status"] == "not approved"


def test_an_approved_artifact_passes_publication_admission_and_a_tampered_one_does_not(tmp_path):
    path = triage.write_artifact(artifact(APPROVED), tmp_path / "triage.json")
    assert triage.approved_artifact(path)["artifact_schema"] == triage.ARTIFACT_SCHEMA

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["alerts"][0]["alert_amount"] += 1.0
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        triage.approved_artifact(path)
    with pytest.raises(ValueError, match="checksum"):
        admitted_triage_artifact(path, require_approval=False)


def serve(monkeypatch, tmp_path, mode: str, distribution: dict) -> TestClient:
    path = triage.write_artifact(artifact(distribution), tmp_path / "triage.json")
    monkeypatch.setattr(app_module, "TRIAGE_PATH", path)
    monkeypatch.setattr(
        app_module,
        "RUNTIME",
        app_module.RuntimeConfig(app_mode=mode, cors_origins=()),
    )
    return TestClient(app_module.app)


def test_the_public_service_refuses_the_unapproved_triage_slice(monkeypatch, tmp_path):
    client = serve(monkeypatch, tmp_path, app_module.PUBLIC_MODE, UNAPPROVED)
    for path in ("/api/triage/period", "/api/triage/queue"):
        response = client.get(path)
        assert response.status_code == 503
        assert response.json() == {
            "detail": "Triage artifact is not approved for delivery on this surface."
        }
    # The approved replay artifact keeps serving, so refusing the triage slice
    # does not take the deployed surface down with it.
    assert client.get("/api/cases").status_code == 200


def test_the_public_service_refuses_an_approved_artifact_that_is_not_the_pinned_release(
    monkeypatch, tmp_path
):
    """Approval is a decision about a source. The pin is a decision about a build.

    The distribution decision approves a source checksum, and any rebuild that
    reads that source carries the approval flag forward. The deployed function
    cannot see the pipeline that produced the file it is handed, so without a
    pinned digest an unreviewed rebuild would serve itself on the strength of a
    flag it inherited.
    """
    client = serve(monkeypatch, tmp_path, app_module.PUBLIC_MODE, APPROVED)
    response = client.get("/api/triage/period")
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Triage artifact is not approved for delivery on this surface."
    }
    assert client.get("/api/cases").status_code == 200


def test_the_public_service_serves_the_pinned_approved_release(monkeypatch, tmp_path):
    path = triage.write_artifact(artifact(APPROVED), tmp_path / "triage.json")
    digest = json.loads(path.read_text(encoding="utf-8"))["artifact_sha256"]
    monkeypatch.setattr(app_module, "TRIAGE_PATH", path)
    monkeypatch.setattr(app_module, "APPROVED_TRIAGE_ARTIFACT_SHA256", digest)
    monkeypatch.setattr(
        app_module,
        "RUNTIME",
        app_module.RuntimeConfig(app_mode=app_module.PUBLIC_MODE, cors_origins=()),
    )
    client = TestClient(app_module.app)
    period = client.get("/api/triage/period").json()
    assert period["delivery"]["status"] == "approved"
    assert period["delivery"]["published"] is True
    assert period["request_inference"] is False
    queue = client.get("/api/triage/queue?ordering=B2").json()
    assert len(queue["items"]) == period["period"]["alerts"]
    assert [row["position"] for row in queue["items"]] == list(range(1, queue["alerts"] + 1))


def test_the_local_workbench_admits_a_rebuild_the_public_pin_would_refuse(
    monkeypatch, tmp_path
):
    """The local mode exists to run the artifact an operator just built.

    Applying the release pin there would refuse the one thing the mode is for, so
    the pin is public mode only and every other check still runs.
    """
    client = serve(monkeypatch, tmp_path, app_module.LOCAL_TRIAGE_MODE, APPROVED)
    assert client.get("/api/triage/period").status_code == 200


def test_the_committed_artifact_is_the_approved_pinned_release() -> None:
    """The file that ships is the file the pin names, and it says it is published.

    Every other admission test builds its own artifact, so nothing else would
    catch a rebuild that changed the digest without the pin following it.
    """
    served = admitted_triage_artifact(
        app_module.TRIAGE_PATH,
        require_approval=True,
        expected_sha256=app_module.APPROVED_TRIAGE_ARTIFACT_SHA256,
    )
    assert served["provenance"]["distribution"]["status"] == "approved"
    assert served["provenance"]["source_sha256"] == APPROVED_SOURCE_SHA256
    decision = json.loads(
        Path("data/provenance/ibm_aml_data_v8_triage_distribution.json").read_text(
            encoding="utf-8"
        )
    )
    assert decision["public_distribution_status"] == "approved"
    assert decision["approved_source_sha256"] == APPROVED_SOURCE_SHA256
    assert decision["owner_approval"] is not None
    assert decision["blocker"] is None


def test_the_local_workbench_serves_the_queue_whole_and_says_it_is_not_published(
    monkeypatch, tmp_path
):
    client = serve(monkeypatch, tmp_path, app_module.LOCAL_TRIAGE_MODE, UNAPPROVED)
    period = client.get("/api/triage/period").json()
    assert period["delivery"] == {
        "status": "local-only",
        "published": False,
        "statement": period["delivery"]["statement"],
    }
    assert "not approved for publication" in period["delivery"]["statement"]
    assert period["request_inference"] is False

    queue = client.get("/api/triage/queue?ordering=B2").json()
    assert len(queue["items"]) == period["period"]["alerts"]
    assert queue["cut_line"] == OPERATING_POINT["k_alerts_worked_per_period"]
    assert [row["position"] for row in queue["items"]] == list(range(1, queue["alerts"] + 1))
    # Positions past the cut line are returned, not filtered away.
    assert any(row["position"] > queue["cut_line"] for row in queue["items"])

    detail = client.get(f"/api/triage/alerts/{queue['items'][0]['alert_id']}?ordering=B2").json()
    assert detail["disposition"].startswith("Not recorded")
    assert "never sent to this API" in detail["disposition_storage"]
    # A baseline names what it ordered on rather than rendering no explanation.
    assert "Alert amount descending" in detail["ranking_explanation"]
    assert detail["ranking_contributions"] == []


def test_triage_routes_reject_malformed_input(monkeypatch, tmp_path):
    client = serve(monkeypatch, tmp_path, app_module.LOCAL_TRIAGE_MODE, UNAPPROVED)
    for path in (
        "/api/triage/queue?ordering=B9",
        "/api/triage/queue?ordering=C2",
        "/api/triage/alerts/not-an-alert",
        "/api/triage/alerts/1",
    ):
        response = client.get(path)
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid request parameters."}
    missing = client.get("/api/triage/alerts/00000000000000000000")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Alert not found in the published review period."}


def test_a_missing_artifact_is_an_honest_state_and_not_a_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "TRIAGE_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(
        app_module,
        "RUNTIME",
        app_module.RuntimeConfig(app_mode=app_module.LOCAL_TRIAGE_MODE, cors_origins=()),
    )
    response = TestClient(app_module.app).get("/api/triage/period")
    assert response.status_code == 503
    assert response.json() == {
        "detail": "No triage artifact is built. The triage surface is not available."
    }
