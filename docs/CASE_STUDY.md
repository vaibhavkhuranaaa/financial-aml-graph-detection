# Signal Ledger technical case study

Signal Ledger demonstrates a bounded research workflow: timeline → topology → precomputed research context → simulated human decision → browser-memory audit note. It is not a production system, compliance recommendation, or statement about a real entity.

The public fixture is a deterministic IBM AML-Data v8 HI-Small slice under CDLA-Sharing-1.0. Its embedded provenance records IBM/Erik Altman attribution, retrieval date, source checksum, slice checksum, and selection: one FAN-OUT pattern sequence for a simulated escalation and five chronological non-laundering ACH transactions for a simulated closure. Parties are deterministically pseudonymized.

The FastAPI API limits case catalogue, timeline, and graph responses; it has no local Elliptic route. Scores and explanations are precomputed. Elliptic evaluation remains local-only and requires provenance gating, chronological splitting, unknown-label handling, baseline/GNN comparison, PR-AUC, precision/recall, calibration, review-capacity analysis, and operational error analysis before any claim.

Reproduce the public fixture with `python3 scripts/generate_public_fixture.py <local HI-Small_Trans.csv>`; the source checksum must match. Verify with `uv run pytest -q`, `cd frontend && npm run build`, and `docker compose -f docker/docker-compose.yml config`.
