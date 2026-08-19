# 0005 Make the leakage gate prove itself, and split the feature horizons

## Decision

The feature build computes every value from transactions dated strictly before
the alert's `feature_cutoff_ts`, and the leakage gate that enforces it ships with
a test that deliberately introduces a leak and asserts the gate fails.

Features are computed over two separated horizons. History is everything strictly
before the period start. The period is the alert's own review period, and it
stops at the cutoff. Both are derived from the same pre cutoff input, and neither
can reach past it.

The laundering flag is rejected at the entry point rather than merely unused. A
build whose input carries a column matching the flag raises before any feature is
computed.

## Why

A gate that has only ever passed is not evidence of anything. It could be
asserting that two identical code paths agree, which is what a leakage check
degenerates into when the build filters its own input and the check re-filters
the same way. The only way to know the gate works is to make it fail on purpose,
so the test suite substitutes a period builder that ignores the cutoff and
asserts the gate reports the offending column by name.

The two horizons are separated because they answer different questions and a
single aggregate would blur them. History distinguishes a long standing busy
account from one that appeared this week, which is most of what tells a benign
high volume subject from a suspicious one. The period is what the rules actually
fired on. Collapsing them into one window would lose the comparison that makes
the ratios meaningful, and the ratios are the features most likely to carry
signal.

Rejecting the label at the entry point costs one line and removes a class of
mistake that no reviewer reliably catches. The alert store already excludes it,
so the check is defence against a future caller passing a different frame, which
is exactly the caller that would not think about it.

## Alternatives rejected

**Trust the build and skip the gate.** The project's own risk table lists leakage
through a feature reading post decision transactions as a named risk, and
`spec.md` section 8 makes the gate non negotiable. A build without one cannot
report a number.

**Check the gate by inspection instead of by test.** Inspection does not survive
the next feature someone adds. The failing test does.

**One combined horizon with a longer window.** Simpler and less informative. The
period over history ratios would not exist, and those are the features that
express the deviation the typologies are about.

**Per alert cutoffs.** Every alert in a period shares a cutoff, so the build runs
once per period rather than once per alert. This is an implementation choice and
not a contract change; if a reporting lag ever moves `feature_cutoff_ts` away
from `period_end`, the build groups by the cutoff instead.

## Not done

No feature selection, no importance analysis, and no scaling. Thirty nine feature
columns are built and all of them are handed to the baseline ladder and the
ranker as they are. Gradient boosted trees split on order rather than magnitude,
so the heavy tails in the ratio features are left alone rather than clipped or
logged, which would be a modelling decision made before any model exists.

No calibration and no probability. The product ranks.

## Changed

`src/pipeline/features.py`, `scripts/build_features.py` and
`tests/test_features.py`. The feature table is written to `data/features/`, which
is gitignored, and nothing about the deployed surface changes.
