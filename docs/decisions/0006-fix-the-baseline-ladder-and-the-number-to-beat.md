# 0006 Fix the baseline ladder, and the number a challenger has to beat

## Decision

Four calls, all made at the baseline milestone and all before any model exists.

**The label join lives in `src/pipeline/backtest.py` and nowhere else.** An alert
is a true positive when any of its contributing transactions carries the
laundering flag. Typology attribution is a separate and narrower question,
answered from the injected patterns file rather than inferred from the flag. The
join reads the whole transaction file including the days after the study window,
because an outcome observed later is how a suspicious activity report works.
Features remain bound by `feature_cutoff_ts` and the leakage gate still enforces
that.

**B3's rule hit rates are shrunk toward the pooled prior rate, with a weight of K
alerts.** The unshrunk ladder is published beside the reported one.

**The rung a challenger has to beat is B2, not B3.** Amount descending reaches
120 true positives in the 882 alerts worked across the seven evaluation periods,
a precision of 13.61 percent. Rules only priority reaches 102, a precision of
11.56 percent. B3 stays in the ladder and stays the rules only reference for per
typology reporting, but it is not the top of the ladder and the project does not
report it as though it were.

**This milestone closes on evidence and on this record, and cites no metric.**
The three metrics it was planned to close on are baselined here and resolved at
the challenger milestone.

## Why

The ladder, pooled over seven evaluation periods, 126 alerts worked per period,
882 worked alerts against an evaluation population of 5,715 alerts carrying 223
true positives, a base rate of 3.90 percent:

| Rung | True positives | Precision at K | 95 percent interval | Attempts recovered |
| --- | --- | --- | --- | --- |
| B0 random | 41 | 0.0465 | 0.0340 to 0.0601 | 1 |
| B1 chronological | 100 | 0.1134 | 0.0930 to 0.1349 | 2 |
| B2 amount descending | 120 | 0.1361 | 0.1145 to 0.1599 | 5 |
| B3 rules only priority | 102 | 0.1156 | 0.0930 to 0.1361 | 1 |
| B3 with no shrinkage | 94 | 0.1066 | not reported as a rung | 9 |

Attempts recovered counts the injected laundering attempts with at least one
transaction inside a worked alert, against 25 that the rules engine surfaced at
all and 337 that are live in the evaluation periods.

B3 over B0 is 2.49 with a paired interval of 1.73 to 4.25. B3 over B1 is 1.02,
interval 0.97 to 1.06, which is no difference. B3 over B2 is 0.85, interval 0.75
to 0.96, and the upper bound is below one, so amount descending beats rules only
priority by more than the noise. Calling B3 the number to beat after measuring
that would set the challenger an easier target than the cheapest sort an
institution already runs, which is the definition of a strawman baseline. The
ladder rule in `docs/scope.md` already says each rung must be beaten before the
next is justified, so the binding rung is simply the strongest one.

**Why the hit rates are shrunk.** R6 cannot fire until a full lookback exists
behind the period, so by 2022/09/09 it had three prior alerts and all three had
resolved as suspicious. An unshrunk estimator reads that as a hit rate of 1.0 and
hands the rule the entire top priority band. On that period B3 then worked 126
alerts and found none, against 15 for B2. That is an artefact of estimating a
rate from three observations, not a property of the rules, and leaving it in
would have understated the baseline the whole project is measured against.

The shrinkage weight is set to K, one period of analyst capacity, because that is
the smallest sample an institution could actually have worked before re-banding a
rule. It is anchored to the operating point rather than chosen against the
result, and the unshrunk ladder is published next to the shrunk one so the choice
can be checked rather than taken on trust.

**The two estimators trade against each other, and both numbers are reported.**
Shrinking moves B3 from 94 true positive alerts to 102, and at the same time from
9 recovered attributed attempts to 1. Precision improves and per typology
recovery falls, because the alerts the shrunk ordering promotes are the ones
carrying flagged transactions that no injected attempt claims. Reporting only the
precision gain would be exactly the aggregate that hides a typology, so both
variants are reported as rows of the ladder and neither is dropped.

The choice does not move the challenger's target. B2 beats both variants on
precision at K, 120 true positives against 102 and 94. On attributed attempts it
recovers 5 against the shrunk B3's 1 and the unshrunk B3's 9, out of 25 surfaced
and 337 live, which is a difference of a few attempts on a denominator that
cannot carry it. The challenger has to clear 13.61 percent precision at K and it
has to be read against both B3 variants on per typology recovery.

**Why the milestone cites no metric.** Every threshold on the three metrics is
expressed relative to B3: precision at K must reach 1.3 times B3, per typology
recall must not fall more than 5 points below B3, and lift over the ladder must
exceed every rung. None of them can be satisfied by the ladder that defines B3,
because a rung cannot beat itself by a third. Writing a passing number into any
of them would mean recording a quantity that is not the one the metric defines.
The measured values are recorded as baselines instead, and the challenger
milestone already cites all three.

**The finding that constrains everything downstream.** The rules engine surfaces
25 of the 337 injected attempts live in the evaluation periods, which is 7.4
percent. Per typology recall at K is therefore between zero and one attempt for
every typology and every rung, and no ordering can change that, because ordering
cannot recover an attempt no rule raised an alert on.

The reason is measurable and specific. R3 and R4 require 12 distinct
counterparties for one subject inside one review period. Across all 363 injected
attempts in the window, the largest single day counterparty count reached by any
attempt subject is 9, and the median is between 1 and 4 depending on typology. An
injected fan out of 16 beneficiaries is spread across four days, so it never
presents 12 in a day. The 103 attributed laundering transactions that do land
inside an alert are there because the account was independently busy enough to
fire a rule on its organic traffic, not because the attempt's own structure
triggered anything.

The consequence is that precision at K on this alert population is carried almost
entirely by the flagged transactions that carry no typology attribution: 198 of
the 223 true positive alerts in the evaluation periods are on that line. It is
reported as its own line, in alerts rather than attempts, and it is neither
folded into a typology nor dropped.

## Alternatives rejected

**Leave the hit rate unshrunk.** It is the simpler estimator and it is wrong in a
way that flatters any future challenger. A rule with three observations is not
evidence of a priority band.

**Choose the shrinkage weight by what it does to the ladder.** That is tuning a
baseline against the label, which is the thing this project refuses to do to its
rules. The weight is fixed to the operating point and stated.

**Keep B3 as the number to beat because the plan named it.** The plan named it
before it was measured. What was measured is that a single feature sort beats it,
and the honest response is to raise the bar rather than protect the narrative.

**Re-parameterise R3 and R4 to a multi day window so the rules catch the injected
attempts.** This would change alert volume, invalidate the alert store, the
feature build and every number above, and it would be a rule change motivated by
what the label says rather than by alert volume. The measurement is reported as a
finding and the parameter decision belongs to the owner as its own change.

**Count only attributed transactions as true positives.** That would discard
1,968 labelled laundering transactions on the grounds that the simulator did not
record which pattern produced them, and it would make precision a statement about
the patterns file rather than about laundering.

**Fold the unattributed positives into a typology, or drop them.** The first
invents attribution the data does not carry. The second hides most of the signal
in the alert population.

**Restate the thresholds so the milestone passes.** The thresholds are the
project's ship gates and were written before any measurement. Moving them to fit
a result is the failure mode this project exists to avoid.

## Not done

No model, no feature use, and no training. The ladder reads `fired_rules`, the
contributing transaction timestamps and amounts, and nothing from the feature
table.

No rule re-parameterisation. The parameters that produced the alert store are
unchanged, and the store and feature build are untouched.

No false positive reduction number and no rank stability. Both are challenger
metrics and neither is defined without a challenger.

No LI-Small run. The prevalence sensitivity variant is its own milestone.

B0 is scored on one fixed seed rather than averaged over many. Its expected
precision is the population base rate of 3.90 percent by construction, its
measured value is 4.65 percent, and the interval covers the difference.

## Changed

`src/pipeline/backtest.py`, `scripts/run_baselines.py` and
`tests/test_backtest.py` are new. `README.md`, `docs/scope.md`,
`docs/DELIVERY_PLAN.md` and `docs/CASE_STUDY.md` are corrected, because they said
no metric had a result and the ladder is now measured. The run record is written
to `data/backtest/`, which is gitignored. Nothing on the serving path changes and
nothing the demo serves gains a dependency.
