# 0004 Keep the baseline priority out of the alert store

## Decision

The alert store does not carry a `rules_priority` field. The planned record
contract said it should, and this amends that contract.

B3, the rules only baseline, orders alerts by the rules that fired weighted by
each rule's historical hit rate. That value is computed in the backtest harness
from periods strictly before the one being scored, alongside every other place
the label is read. The alert store carries `fired_rules`, which is the only
input B3 needs that is not a function of the label.

## Why

A hit rate is the share of a rule's past alerts that resolved as suspicious. It
is a function of the outcome, so computing it means reading the label. The store
was specified to hold no label, and the two requirements cannot both be met by
storing the value.

The contract wanted the field stored to stop B3 being computed at evaluation time
from the period it is scoring, which would make the baseline leak and the
comparison worthless. That property does not come from where the value is kept.
It comes from the value being computed over prior periods only, which the
backtest enforces at the one point where the label is joined.

Keeping the field would also have put a label-derived quantity in a file the
feature build reads. The feature build is forbidden from seeing the label, and
the cheapest way to guarantee that is for the label never to reach the file at
all rather than for a later reader to remember to exclude a column.

## Alternatives rejected

**Store a label free proxy priority instead**, such as a score weighted by each
rule's prior period rarity. That is a different baseline from the one `spec.md`
section 8 defines, and shipping it under the name B3 would misreport what was
beaten. It is also unused by anything today.

**Store the hit rate weighted value and accept the label in the store**,
excluding the column by convention wherever it must not be read. Conventions of
that shape are what leakage gates exist to catch, and this project has one
because it does not trust them.

**Compute B3 at evaluation time from the scored period.** This is the leak the
original contract was written to prevent, and it stays rejected.

## Not done

No change to any other field. The store still carries a deterministic
`alert_id`, the fired rule set, per rule trigger evidence, the contributing
transaction identifiers, and `feature_cutoff_ts` held separately from
`period_end`.

The backtest harness does not exist yet. It is milestone M4, and this decision
records where B3 belongs when it is written.

## Changed

`src/pipeline/alert_store.py`, `scripts/build_alert_store.py` and
`tests/test_alert_store.py`. The system design's alert record contract is
amended by this record rather than rewritten in place, so the reasoning stays
visible.
