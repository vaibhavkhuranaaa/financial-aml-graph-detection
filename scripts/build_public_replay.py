"""Record verified local IBM provenance or materialize a bounded replay artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.public_replay import record_source_manifest, write_artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--distribution-decision", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--record-manifest", type=Path)
    parser.add_argument("--retrieved-at")
    parser.add_argument("--source-ref", default="https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml/versions/8")
    args = parser.parse_args()
    if args.record_manifest:
        if not args.retrieved_at:
            parser.error("--retrieved-at is required with --record-manifest")
        manifest = record_source_manifest(args.source, args.retrieved_at, args.source_ref)
        args.record_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return
    if not args.source_manifest or not args.distribution_decision or not args.output:
        parser.error("--source-manifest, --distribution-decision, and --output are required to build an artifact")
    artifact = write_artifact(args.source, args.source_manifest, args.distribution_decision, args.output)
    print(json.dumps({"pipeline_run_id": artifact["provenance"]["pipeline_run_id"], "artifact_sha256": artifact["artifact_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
