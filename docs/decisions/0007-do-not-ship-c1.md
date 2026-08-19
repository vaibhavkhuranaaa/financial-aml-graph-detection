# 0007 Do not ship C1. It beats every rung and misses the gate

## Decision

**No model ships.** C1, a LightGBM lambdarank ranker over the 39 alert features
grouped by review period and trained on prior periods only, beats every rung of
the ladder and does not clear the threshold the project set before it existed.

| Ordering | True positives | Precision at K | 95 percent interval | Attempts recovered |
| --- | --- | --- | --- | --- |
| B0 random | 41 | 0.0465 | 0.0340 to 0.0601 | 1 |
| B1 chronological | 100 | 0.1134 | 0.0930 to 0.1349 | 2 |
| B2 amount descending | 120 | 0.1361 | 0.1145 to 0.1599 | 5 |
| B3 rules only priority | 102 | 0.1156 | 0.0930 to 0.1361 | 1 |
| C1 learned ranker | 148 | 0.1678 | 0.1451 to 0.1916 | 8 |

The gate in `docs/scope.md` is a lift of 1.3 times the baseline with the interval
lower bound above 1.0. Against the binding rung, B2, C1's lift is **1.2333** with
an interval of 1.1045 to 1.3967. The lower bound clears 1.0, so the improvement
is real and not noise. The point estimate does not reach 1.3, so the gate is not
met and the model is not promoted.

Everything else C1 was measured on is recorded and passes: rank stability
averages 0.9141 across six retrain pairs against a threshold of 0.70, no
supported typology falls below B3 at the same K, and holding B2's coverage costs
C1 fewer worked alerts than B2 needs.

**The headline metric is measured in true positive alerts, not in attempts.** Its
definition said attempts, and at 25 surfaced attempts across seven periods the
attempt criterion is not estimable: five periods carry a target of one attempt,
one period carries a target of zero, and two periods need C1 to work deeper than
K to match a single attempt. The threshold is unchanged at 20 percent and the
business meaning is unchanged. Only the unit of the held coverage changed, and
the attempt depths are published beside it.

**This milestone cites no metric either.** M4 did the same for the same reason:
the kit's rule is that a cited metric must pass its threshold before the
milestone closes, and this milestone closes on a failed gate by design.

## Why

**The improvement is real and it is not enough.** C1 finds 148 true positives in
the 882 alerts a team of six can work across seven periods, against 120 for
sorting by amount. That is 28 more alerts worth opening, and the paired interval
against B2 excludes 1.0 in every bootstrap resample below its lower bound. It is
also 1.2333 rather than 1.3, and the threshold was written at P4 before any model
existed, precisely so that this call could not be argued afterwards. Moving it
now, or reporting the 1.451 lift against B3 as though B3 were still the number to
beat, would be choosing the flattering comparison after seeing both.

**The rung the gate is measured against is B2.** Decision record 0006 fixed that
on measurement, and it costs C1 the promotion. Reporting the lift against B3
instead would clear 1.3 and would be a comparison against a rung that is itself
beaten by a single feature sort.

**What C1 actually learned, and why it is a modest edge.** By gain, the model
splits on contributing transaction count, in period payment count, currency
count, and in period amount aggregates. Those are size and busyness, which is the
same family of signal B2 exploits through amount. The model adds discrimination
inside that family rather than a new one, which is consistent with a lift near
1.2 and not near 2.

**It does not abandon a typology to win.** C1 recovers 8 of the 25 attempts the
rules surfaced against B2's 5 and B3's 1, and it recovers something in four
typologies where B3 recovers in one. No supported typology is below B3, so the
worst drop is 0.0 points against a permitted 5.

**The queue is operable.** Spearman between the orderings two successive
retrains assign to the same period sits between 0.9034 and 0.9299. A queue that
reshuffles on every retrain cannot be run whatever the headline says, and this
one does not.

**The rules and the model contribution split.** Rules only priority accounts for
102 of C1's 148 true positives, so 68.9 percent of what C1 finds at K is
available from the rule set alone and the learned score adds 46 alerts, 5.22
precision points. Reported because the fraud domain rules require it and because
it is the honest answer to the obvious challenge.

**The ceiling is still the alert population, not the ranking.** The rules engine
surfaces 25 of the 337 attempts live in the evaluation periods, so 8 recovered
attempts is 32 percent of what any ordering could possibly reach and 2.4 percent
of what is there. 139 of C1's 148 true positives carry no typology attribution.
The largest available gain in this project is not a better ranker.

## Alternatives rejected

**Tune C1 until it clears 1.3.** There are ten periods and three of them are the
minimum training window, so there is no validation split that is not the
evaluation set. Any search would be fitted to the periods the number is reported
on. The parameter set is stated in `src/pipeline/ranker.py`, chosen for the data
size, and was not searched.

**Report the lift against B3 and promote.** 1.451 against B3 clears the gate.
B3 is beaten by B2, so a challenger that clears a rung nothing should be
measured against has cleared nothing.

**Lower the threshold to 1.2.** The threshold is the ship gate and predates the
measurement. Moving it after seeing 1.2333 is the failure mode the project was
built to avoid.

**Promote on the interval instead of the point estimate.** The interval on the
lift reaches 1.3967, so a reader could argue the true lift might clear the gate.
It might also be 1.1045. The gate is written on the point estimate with an
interval condition attached, and both halves have to hold.

**Call the milestone failed.** `spec.md` section 13 item 5 is explicit that a
measured negative closes the milestone. The deliverable is the rules engine, the
ladder, the challenger's measured result and this record.

**Drop the headline metric because its unit does not work.** Reporting nothing
would hide a result that is measurable in the unit the business case actually
uses. Both the attempt depths and the alert depths are published.

## Not done

No hyperparameter search, no feature selection, no early stopping against the
evaluation periods, no calibration, and no probability. The product ranks.

No change to the rules engine, the alert store or the feature build. C1 reads the
feature table as it was built at M3.

No LI-Small run. The prevalence sensitivity variant is M6, and given this result
it now tests whether a negative finding survives halved prevalence rather than
whether a positive one does.

No inference route and nothing on the serving path. LightGBM is pinned in
`requirements-dev.txt` only.

## Changed

`src/pipeline/ranker.py`, `scripts/run_challenger.py` and `tests/test_ranker.py`
are new. `src/pipeline/backtest.py` gains the scored ordering path and the depth
to held coverage calculation, both of which the ladder rungs and the challenger
share so that the comparison runs through one code path.
`requirements-dev.txt` pins LightGBM. `README.md`, `docs/scope.md`,
`docs/architecture.md`, `docs/DELIVERY_PLAN.md` and `docs/CASE_STUDY.md` carry
the result. The run record is written to `data/backtest/`, which is gitignored.
