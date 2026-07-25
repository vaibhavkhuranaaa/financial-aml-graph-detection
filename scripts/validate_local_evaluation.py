"""Validate local-only Elliptic evaluation evidence without publishing it."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline.evaluation_contract import validate_evaluation_files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Local, untracked source and protocol manifest.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Local, aggregate-only evaluation report.",
    )
    args = parser.parse_args()
    validate_evaluation_files(
        args.manifest, args.report, Path(__file__).resolve().parents[1]
    )
    print(
        "Local-only evaluation evidence is structurally valid; it remains unapproved for public use."
    )


if __name__ == "__main__":
    main()
