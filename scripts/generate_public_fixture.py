"""Retired unsafe fixture generator.

Use ``scripts/build_public_replay.py`` instead. It requires a verified source
manifest and owner-approved CDLA-Sharing-1.0 distribution decision before it
can write a public artifact.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "This generator is retired. Use scripts/build_public_replay.py with "
        "--source-manifest and --distribution-decision."
    )


if __name__ == "__main__":
    main()
