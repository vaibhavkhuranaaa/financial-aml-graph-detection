"""Admission checks for the triage artifact. Standard library only.

This module sits on the serving path, so it imports nothing from
`src/pipeline/`. The pipeline needs Polars and LightGBM and the deployed function
must not gain either, which is a property the import graph enforces rather than a
promise the documentation makes.

Two admission levels, because approval and integrity are different questions.

- `require_approval=True` is what the public service uses. It demands an owner
  approved distribution decision recorded in the artifact, and the triage slice
  does not carry one, so the public surface refuses it.
- `require_approval=False` is what a local analyst workbench uses. Every other
  check still runs: the schema, the content checksum, and the release digest when
  one is pinned. What it drops is the publication gate, and the response says so
  on every route rather than in a footnote.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.public_replay import canonical_bytes

ARTIFACT_SCHEMA = "signal-ledger-public-triage/v1"

APPROVED_STATEMENT = (
    "This triage artifact carries an owner approved distribution decision and is "
    "published under CDLA-Sharing-1.0 with its modification notice."
)
LOCAL_ONLY_STATEMENT = (
    "This triage artifact is not approved for publication. It is served to a "
    "local analyst workbench only, the public service refuses it, and no row of "
    "it reaches a public URL."
)


def content_digest(artifact: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def delivery(artifact: dict[str, Any]) -> dict[str, Any]:
    """The publication state, stated on every triage response."""
    approved = (
        artifact.get("provenance", {}).get("distribution", {}).get("status") == "approved"
    )
    return {
        "status": "approved" if approved else "local-only",
        "published": approved,
        "statement": APPROVED_STATEMENT if approved else LOCAL_ONLY_STATEMENT,
    }


def admitted_triage_artifact(
    path: Path,
    *,
    require_approval: bool,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Load the triage artifact or refuse it, with the reason in the exception."""
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    if artifact.get("artifact_schema") != ARTIFACT_SCHEMA:
        raise ValueError("Triage artifact is not a Signal Ledger triage artifact.")
    if artifact.get("artifact_sha256") != content_digest(artifact):
        raise ValueError("Triage artifact checksum does not match its content.")
    if expected_sha256 and artifact.get("artifact_sha256") != expected_sha256:
        raise ValueError("Triage artifact does not match the approved release digest.")
    if require_approval and delivery(artifact)["status"] != "approved":
        raise ValueError("Triage artifact carries no approved distribution decision.")
    return artifact
