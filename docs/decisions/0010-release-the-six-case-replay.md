# 0010: Release the six-case replay as the portfolio product

## Decision

Treat the approved public six-case replay as Signal Ledger's portfolio product.
The wider rules, ranking, and triage work remain supporting research. The larger
triage artifact stays local and unapproved for public distribution.

## Why

The replay has a complete and enforceable public contract: six bounded cases,
55 selected and pseudonymized transactions, deterministic construction, an
approved distribution decision, read-only GET routes, no request-time inference,
and no server-side visitor persistence. Its deployed artifact identity matches
the fixture in the public repository.

The triage artifact carries a materially larger selection from the same source.
Its distribution decision remains pending, so presenting it as the public
product would cross the recorded evidence and licensing boundary. The negative
model result remains valuable supporting evidence and does not need promotion to
be portfolio-worthy.

## Alternatives rejected

- Publish the triage artifact. Rejected because no approval covers that data
  scope.
- Expand or retune the alert population before release. Rejected because it
  would invalidate the measured pipeline and create a new research project.
- Present the ranker as shipped because it beats every baseline. Rejected
  because it misses the precommitted ship gate on both dataset variants.
- Keep the repository marked as building. Rejected because the public replay is
  complete and the local research plan is closed.

## Not done

No public data scope was expanded. No model was promoted. No triage row was
published. No deployment, push, release, visibility change, or paid resource was
authorized by this decision.

## Changed

The default dashboard now leads with the replay and keeps the local triage desk
behind an explicit local surface switch. Public documentation names the replay
boundary first. A versioned release manifest, source and deployment identity
verifier, code license, data-license notice, and release checks now define the
candidate release.
