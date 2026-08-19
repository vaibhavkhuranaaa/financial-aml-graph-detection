"""Verify the local replay release and, optionally, its deployed identity."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.app import (
    APPROVED_PUBLIC_ARTIFACT_SHA256,
    APPROVED_PUBLIC_PIPELINE_RUN_ID,
    APPROVED_TRIAGE_ARTIFACT_SHA256,
    app,
)
from src.public_replay import approved_public_artifact
from src.triage_artifact import admitted_triage_artifact

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "release-manifest.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    require(
        path.is_relative_to(ROOT), f"Release path escapes the repository: {relative}"
    )
    return path


def validate_local(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    require(
        manifest.get("schema") == "signal-ledger-release/v1",
        "Unknown release manifest schema.",
    )
    require(
        manifest.get("product") == "public-replay-and-approved-triage-period",
        "Release product is not the approved replay and triage period.",
    )
    require(
        manifest.get("publication_gate") == "project-owner-approval",
        "Publication gate is not explicit.",
    )
    require(repo_path(manifest["release_notes"]).is_file(), "Release notes are missing.")
    require(
        manifest.get("runtime_mode") == "public-synthetic-fixture",
        "Release runtime mode is not public replay mode.",
    )

    release = manifest["artifact"]
    require(
        release["sha256"] == APPROVED_PUBLIC_ARTIFACT_SHA256,
        "Release digest and runtime pin differ.",
    )
    require(
        release["pipeline_run_id"] == APPROVED_PUBLIC_PIPELINE_RUN_ID,
        "Release run and runtime pin differ.",
    )
    artifact = approved_public_artifact(
        repo_path(release["path"]),
        expected_sha256=release["sha256"],
        expected_pipeline_run_id=release["pipeline_run_id"],
    )
    cases = artifact["cases"]
    transactions = sum(len(case["transactions"]) for case in cases)
    require(
        len(cases) == release["cases"] == 6, "Release must contain exactly six cases."
    )
    require(
        transactions == release["transactions"] == 55,
        "Release must contain exactly 55 transactions.",
    )

    source_contract = manifest["source"]
    source = load_json(repo_path(source_contract["manifest"]))
    distribution = load_json(repo_path(source_contract["distribution_decision"]))
    provenance = artifact["provenance"]
    require(
        source.get("verification_status") == "verified",
        "Source manifest is not verified.",
    )
    require(
        source.get("dataset_version") == source_contract["dataset_version"] == 8,
        "Source version differs from release.",
    )
    require(
        source.get("license") == source_contract["license"],
        "Source license differs from release.",
    )
    require(
        source.get("source_sha256") == provenance.get("source_sha256"),
        "Artifact and source manifest differ.",
    )
    require(
        distribution.get("public_distribution_status") == "approved",
        "Replay distribution is not approved.",
    )
    require(
        distribution.get("approved_source_sha256") == source.get("source_sha256"),
        "Distribution approval covers a different source.",
    )
    require(
        distribution.get("source_metadata_checked_at")
        == source_contract["metadata_checked_at"],
        "Source metadata verification is stale.",
    )

    # The triage slice carries its own approval and its own pin. Approval is a
    # statement about a source, and any rebuild reading that source inherits the
    # flag, so the digest is checked against the runtime pin as well.
    triage_release = manifest["triage_artifact"]
    triage = load_json(repo_path(triage_release["distribution_decision"]))
    require(
        triage.get("public_distribution_status") == "approved",
        "Triage distribution is not approved.",
    )
    require(
        triage.get("approved_source_sha256") == source.get("source_sha256"),
        "Triage approval covers a different source.",
    )
    require(triage.get("owner_approval") is not None, "Triage approval is unrecorded.")
    require(
        triage_release["sha256"] == APPROVED_TRIAGE_ARTIFACT_SHA256,
        "Triage release digest and runtime pin differ.",
    )
    triage_artifact = admitted_triage_artifact(
        repo_path(triage_release["path"]),
        require_approval=True,
        expected_sha256=triage_release["sha256"],
    )
    require(
        triage_artifact["period"]["start"] == triage_release["period_start"],
        "Triage release period differs from the artifact.",
    )
    require(
        triage_artifact["period"]["alerts"]
        == triage_release["alerts"]
        == len(triage_artifact["alerts"]),
        "Triage release alert bound differs from the artifact.",
    )
    require(
        app.version == manifest["version"], "API version differs from release version."
    )
    require(
        load_json(ROOT / "frontend/package.json")["version"] == manifest["version"],
        "Frontend version differs from release version.",
    )
    return {
        "manifest": manifest,
        "artifact": artifact,
        "cases": len(cases),
        "transactions": transactions,
        "triage_alerts": triage_artifact["period"]["alerts"],
        "periods": len(triage_artifact["evidence"]["per_period"]),
    }


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"User-Agent": "signal-ledger-release-verifier"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def validate_remote(
    base_url: str, repository_fixture_url: str | None, local: dict[str, Any]
) -> None:
    base = base_url.rstrip("/")
    readiness = fetch_json(f"{base}/api/readiness")
    require(
        readiness
        == {
            "status": "ready",
            "artifact_delivery": "approved",
            "request_inference": False,
            "visitor_persistence": False,
        },
        "Deployment readiness contract differs.",
    )
    provenance = fetch_json(f"{base}/api/provenance")
    require(
        provenance.get("slice_sha256") == local["artifact"]["artifact_sha256"],
        "Deployment serves a different replay artifact.",
    )
    catalogue = fetch_json(f"{base}/api/cases")
    require(
        catalogue.get("maximum") == 6 and len(catalogue.get("items", [])) == 6,
        "Deployment case catalogue differs.",
    )
    require(
        sum(item["transaction_count"] for item in catalogue["items"]) == 55,
        "Deployment transaction bound differs.",
    )
    triage = fetch_json(f"{base}/api/triage/period")
    require(
        triage.get("delivery", {}).get("status") == "approved"
        and triage["delivery"].get("published") is True,
        "Deployment does not serve the triage artifact as approved.",
    )
    require(
        triage.get("request_inference") is False,
        "Deployment triage route reports request time inference.",
    )
    require(
        triage.get("period", {}).get("start")
        == local["manifest"]["triage_artifact"]["period_start"],
        "Deployment serves a different triage review period.",
    )
    queue = fetch_json(f"{base}/api/triage/queue?ordering=B2")
    require(
        len(queue.get("items", [])) == local["manifest"]["triage_artifact"]["alerts"],
        "Deployment triage queue does not carry the period whole.",
    )
    # The evidence block is what makes the result readable rather than quotable,
    # so the deployment is checked for the two facts a pooled figure would hide.
    evidence = fetch_json(f"{base}/api/triage/evidence")["evidence"]
    require(
        evidence["funnel"]["lost_before_ordering"]
        == evidence["funnel"]["attempts_live"] - evidence["funnel"]["attempts_surfaced"],
        "Deployment funnel arithmetic does not hold.",
    )
    require(
        len(evidence["per_period"]) == local["periods"],
        "Deployment evidence does not carry every evaluation period.",
    )
    require(
        any(row["attempts_freed"] < 0 for row in evidence["volume_reduction"]["per_period"]),
        "Deployment volume reduction has lost the periods that cost volume.",
    )
    if repository_fixture_url:
        remote_fixture = fetch_json(repository_fixture_url)
        require(
            remote_fixture.get("artifact_sha256")
            == local["artifact"]["artifact_sha256"],
            "Repository and deployment artifact identities differ.",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--base-url")
    parser.add_argument("--repository-fixture-url")
    args = parser.parse_args()
    local = validate_local(args.manifest)
    if args.base_url:
        validate_remote(args.base_url, args.repository_fixture_url, local)
    print(
        json.dumps(
            {
                "cases": local["cases"],
                "release": local["manifest"]["version"],
                "status": "pass",
                "transactions": local["transactions"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
