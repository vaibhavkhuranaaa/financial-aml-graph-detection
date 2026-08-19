# 0008 The negative survives lower prevalence, and one more criterion fails

## Decision

**The result on LI-Small is the same result.** The parameter set, the operating
point and every metric definition were held fixed, the whole pipeline was rerun
on the lower prevalence variant of IBM AML-Data v8, and C1 again beats every rung
of the ladder and again misses the ship gate. The measured negative in decision
record 0007 is not an artifact of HI-Small's prevalence.

| Ordering | True positives | Precision at K | 95 percent interval | Attempts recovered |
| --- | --- | --- | --- | --- |
| B0 random | 33 | 0.0374 | 0.0249 to 0.0499 | 1 |
| B1 chronological | 101 | 0.1145 | 0.0941 to 0.1349 | 2 |
| B2 amount descending | 110 | 0.1247 | 0.1043 to 0.1463 | 2 |
| B3 rules only priority | 97 | 0.1100 | 0.0896 to 0.1315 | 2 |
| C1 learned ranker | 141 | 0.1599 | 0.1361 to 0.1848 | 0 |

Against the binding rung, which is B2 on this variant as it was on HI-Small,
C1's lift is **1.2818** with an interval of 1.1981 to 1.3761. The lower bound
clears 1.0, so the improvement is real. The point estimate does not reach 1.3, so
the gate is not met and the model is not promoted. That is the same verdict
reached on the same arithmetic as HI-Small's 1.2333.

**A second criterion fails here that held on HI-Small.** The per typology floor
permits a supported typology to sit at most 5 recall points below B3. On
LI-Small, B3 recovers one CYCLE attempt of twelve and one SCATTER-GATHER attempt
of twelve, each 8.3333 recall points, and C1 recovers neither. C1 recovers no
attempt in any typology at all. The worst drop is **8.3333 points against a
permitted 5**, where on HI-Small it was 0.0 points. On LI-Small C1 therefore
fails two of the three ship criteria rather than one.

The remaining criteria pass, as they did on HI-Small. False positive reduction at
held coverage is 51.47 percent against a threshold of 20 percent. Rank stability
between successive retrains averages 0.9222 across six pairs against a threshold
of 0.70.

**This milestone cites one metric and it passes.** Unlike M4 and M5, which cited
none because every threshold they touched is a ratio against a rung, M6 closes on
false positive reduction at held coverage, which is 46.26 percent on HI-Small and
51.47 percent on LI-Small against a threshold of 20 percent. The metric that
fails, precision at K against the 1.3 gate, is not cited here for the same reason
it was not cited at M5, and it carries its measured result on both variants.

## Why

**What was actually varied, and by how much.** LI-Small is the low illicit
variant. In the study window, after self transfers are dropped, 3,428 of
6,119,424 transactions carry the laundering flag, a rate of 0.05602 percent,
against HI-Small's 4,514 of 4,486,418 at 0.10061 percent. That is a cut to 0.557
of HI-Small's transaction level prevalence, close to halved but not exactly
halved, and the honest figure is the measured one.

**The perturbation attenuates by the time it reaches the alert population, and
that bounds how strong this test is.** A 44 percent cut in transaction level
prevalence becomes a 21 percent cut in the alert population base rate: 3.101
percent on LI-Small against 3.902 percent on HI-Small. The rules select for
structure, and structure survives the variant, so the population the ranker is
scored on is less different than the raw file is. This test says the negative
holds across the prevalence range the two Small variants span. It does not say
the negative holds at an arbitrary prevalence.

**A second thing moved with it, and it was right to let it move.** The same
parameter set produces 12,030 alerts across the ten periods on LI-Small against
9,171 on HI-Small, and 7,449 against 5,715 in the seven evaluation periods. K is
held at 126 alerts per period because K is a statement about analyst hours, not
about the data, so the queue C1 works is a shallower slice of a deeper pile:
11.8 percent of the mean evaluation period against 15.4 percent on HI-Small.
Re-parameterising the rules to match HI-Small's alert volume would have made the
comparison single variable and would have meant tuning the alert population per
dataset, which is the thing decision record 0003 refused to do. The confound is
recorded rather than engineered away.

**The ladder ordering is unchanged, which is the load bearing part.** B2 beats
B3 again, 0.1247 against 0.1100. The finding in decision record 0006, that the
rung a ranker has to beat is a single feature sort and not rules only priority,
is reproduced on an independent variant. Had B3 been strongest here, the choice
of reference rung would have been dataset specific and the gate would have been
arguing with itself.

**The ranker learned the same thing again.** By gain the last model splits on in
period outgoing payment count, contributing transaction count, and in period
incoming amount aggregates. Those are size and busyness, the family B2 exploits
through amount, and the same family the HI-Small model split on.
Two datasets, the same family, the same modest edge near 1.2 rather than near 2.

**Why the typology floor broke.** It is not that C1 got worse at typologies. It
is that the denominator got smaller. The rules surface 8 of the 108 attempts live
in the evaluation periods on LI-Small; on HI-Small they surfaced 25 of 337. Every
per typology recall on this variant is zero or one attempt out of ten to nineteen
live, so the floor is decided by whether a single attempt lands above or below
the cut line. C1 lost two such coin flips and B3 won them. The criterion is
written on point values and it fails on point values, and that is reported as a
failure rather than argued down. It is also, on a denominator of 8 surfaced
attempts, barely estimable, which is the same objection decision record 0007
raised against the headline metric's attempt unit. Both facts are published.

**The constraint the project keeps finding is invariant.** The rules engine
surfaces 7.41 percent of live attempts on LI-Small and 7.42 percent on HI-Small.
Two variants, two independently injected attempt sets, the same fraction to two
decimal places. No injected attempt presents the counterparty count the fan in
and fan out rules require inside a single day, on either variant. The largest
available gain in this project is a better alert population, and lower prevalence
does not change that.

**The rules and model contribution split is also reproduced.** Rules only
priority accounts for 97 of C1's 141 true positives, so 68.79 percent of what C1
finds at K is available from the rule set alone and the learned score adds 44
alerts, 4.99 precision points. On HI-Small the same figures were 68.9 percent, 46
alerts and 5.22 points.

**Both variants reproduce to the digit on rerun.** The HI-Small ladder and
challenger were rerun alongside the LI-Small ones and returned every number in
decision record 0007 unchanged, so the comparison is between two runs of one
pipeline rather than between a fresh run and a remembered one.

## Alternatives rejected

**Re-parameterise the rules for LI-Small to match HI-Small's alert volume.**
This would isolate prevalence as the single varying quantity, which is the
cleaner experiment. It would also mean the alert population is tuned per dataset,
and the parameter set is what decision record 0003 fixed against measured volume
once. A sensitivity run that moves the parameters is a sensitivity run on the
parameters.

**Read the LI-Small lift of 1.2818 as trending toward the gate.** It is higher
than HI-Small's 1.2333 and its interval reaches 1.3761. Two points are not a
trend, the intervals overlap across almost their whole range, and the gate is a
point estimate with an interval condition. Neither variant meets it.

**Promote on LI-Small because the interval is tighter here.** The interval
condition is that the lower bound exceeds 1.0, and it did on HI-Small too. A
tighter interval around a point estimate that misses the gate is a better
measured miss, not a pass.

**Report the typology floor failure as noise and hold the criterion at 0.0
points.** The criterion is arithmetic on measured recall and it fails. Declaring
a failed criterion unestimable after it fails, having accepted it when it passed
on the other variant, is choosing the reading after seeing the number.

**Drop the LI-Small run because it changes no decision.** It changes no decision
and that is the finding. A negative that only holds on the dataset it was
discovered on is a weaker claim than one that holds on two, and the run is cheap
compared to the claim it supports.

**Tune C1 on LI-Small.** Same objection as decision record 0007. Ten periods,
three of them the minimum training window, and no validation split that is not
the evaluation set.

## Not done

No public surface for LI-Small. The variant has its own verified source manifest
in `data/provenance/ibm_aml_data_v8_li_small_source.json` and its checksum was
re-verified before the run. It has **no distribution decision and needs none**,
because no row of it reaches the deployed artifact. The public fixture remains
the approved HI-Small slice. See `docs/DATA_GOVERNANCE.md`.

No change to the rules engine, the alert store, the feature build, the backtest
harness or the ranker. The LI-Small run uses the code as it stood at M5, which is
the only way the two results are comparable.

No third variant. The Medium and Large releases would make this a data
engineering exercise, which `docs/scope.md` records as a trade the project
declines to take quietly.

No re-selection of the deployed variant, and no claim that either variant's
numbers transfer to real world detection performance.

## Changed

`scripts/run_baselines.py` and `scripts/run_challenger.py` write a `source` block
and a `store_digest` into the run record. The parameter set is held fixed across
variants, so `engine_version` and `param_set_hash` are byte identical on
HI-Small and LI-Small and cannot tell two records apart; the source file names
and the store digest can. This is the only code change in the milestone.

`README.md`, `docs/scope.md`, `docs/architecture.md`, `docs/DELIVERY_PLAN.md`,
`docs/CASE_STUDY.md`, `docs/data-dictionary.md` and `docs/DATA_GOVERNANCE.md`
carry the result and stop describing the sensitivity run as planned. The LI-Small
alert store, feature table and run records are written under `data/li-small/`,
which is gitignored, alongside the HI-Small artifacts rather than over them.
