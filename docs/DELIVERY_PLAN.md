# Signal Ledger delivery record

This records what is delivered and serving today. The approved six-case replay
is the portfolio product. The wider alert-triage research is supporting evidence
and remains local where its data scope is not approved for distribution.

## Product boundary

Signal Ledger's deployed surface is anonymous and read only, over bounded
realistic synthetic banking data: a deterministic replay workbench and an alert
triage desk for one review period. It is a portfolio research demonstration, not
a compliance product, production monitor, accusation, or statement about real
people or organisations.

The public service has no authentication, telemetry, server side visitor
persistence, request time inference, live feed, or write API. Browser local
simulated notes are never sent to the server.

## Delivered scope

- Typed FastAPI GET contracts for health and readiness, case catalogue and
  detail, timeline, bounded topology, evidence, provenance, and methodology.
- Six deterministic IBM AML-Data v8 cases covering 55 transactions, materialised
  from the owner approved checksum bound source.
- An accessible React investigation desk with timeline replay, bounded topology,
  provenance, uncertainty, and browser private simulated review records.
- GitHub Actions verification, Docker portability checks, and one public review
  Vercel production deployment.
- A versioned release manifest and verifier that bind the fixture, runtime pins,
  source and distribution records, route boundary, and deployed artifact
  identity.

- A typology rules engine implementing R1 through R8, each with a measured base
  rate and alert volume, parameterised against target alert volume and never
  against the laundering flag.
- An alert store to a fixed record contract, Parquet partitioned by review
  period, rebuilding byte for byte from the same source and parameter set.
- An alert level feature build whose leakage gate ships with a test that
  introduces a leak on purpose and asserts the gate catches it.

The pipeline runs locally only. It is not served, and the deployed function
imports none of it.

- A backtest harness holding the label join, and the baseline ladder B0 to B3
  scored across the seven evaluation periods with absolute counts, per typology
  attempt counts and bootstrap intervals.

- A LightGBM lambdarank challenger trained on prior periods only across the
  expanding walk forward, scored through the same metric code as the ladder.

- A prevalence sensitivity run of the whole pipeline on the low prevalence
  LI-Small variant, with the parameter set, the operating point and every metric
  definition held fixed, and its result written up against the HI-Small run.

- A public case study, `docs/CASE_STUDY.md`, stating in its first paragraph that
  no model shipped, and carrying the per typology table with the five structural
  zeros at an attempt count of zero, the unattributed positives as their own
  line, the truncated attempt count, the interval on every headline number, and
  the claims boundary.

- An evidence block on the triage artifact and a fourth typed GET contract over
  it, carrying the measured run per period, per typology and per attempt: the
  funnel from attempts live to surfaced to reached, both recall denominators on
  every typology, the unattributed line as its own block, per period alert volume
  and coverage at a fixed capacity, the volume claim unpooled with its signs kept,
  rank stability, and the model's feature gains bounded to 15 of 39. See decision
  record 0013.

- Queue view controls and a local review record export on the triage desk. The
  view narrows by typology and by disposition status without touching the
  ordering: positions, the cut line and every capacity number stay computed on
  the whole period, and a narrowed view states how many alerts it is not showing
  and that they remain workable. The export writes the browser held review record
  to a local file carrying the review period, the ordering on screen and the
  claims boundary. See decision record 0011.

- A triage workbench: a bounded, pseudonymised artifact for one review period,
  three typed GET contracts over it, and a desk carrying the capacity control,
  the cut line drawn in the queue, the ordering switch across every rung and the
  challenger, alert detail down to the contributing transactions, and both the
  structural zero and baseline wins states. It is published under an owner
  recorded distribution decision covering one review period of the HI-Small
  variant, and the public service admits only its pinned release.

## Not delivered

**No model.** The challenger reaches 16.78 percent precision at K against the
strongest rung's 13.61 percent, a lift of 1.2333 with an interval of 1.1045 to
1.3967 against a ship gate of 1.3, so it is measured and not promoted. On
LI-Small the same challenger reaches 15.99 percent against 12.47 percent, a lift
of 1.2818 with an interval of 1.1981 to 1.3761 against the same gate, and it also
falls 8.33 recall points below rules only priority on two supported typologies
against a permitted 5. The deliverable is the rules engine, its measured volumes,
the baseline ladder, and the written account in decision records 0007 and 0008.

**Nothing beyond the one approved review period.** The distribution decision in
`data/provenance/ibm_aml_data_v8_triage_distribution.json` covers one review
period of the HI-Small variant against the exact verified source checksum. It
does not cover another period, the LI-Small variant, the alert store, the feature
table, or the tuned rule parameter values, and none of those reaches a public
URL. See decision records 0009 and 0012.

**No filter across review periods.** The triage artifact carries exactly one
review period, so there is nothing to select across periods and the view control
says so rather than offering a selector with one entry. A cross period filter
needs a multi period artifact, which is a rebuild and a new pinned digest rather
than an interface change. The typology and disposition status filters from the
design language's product behaviour list are delivered.

## Evidence and governance

| Item | Record |
| --- | --- |
| IBM source checksum | held in the private delivery records, not published here |
| Approved artifact digests | pinned in `src/app.py`, and refused when they do not match |
| Distribution decision | `data/provenance/ibm_aml_data_v8_distribution.json` |
| Source manifest | `data/provenance/ibm_aml_data_v8_source.json` |
| Sensitivity variant manifest, local only, no distribution decision | `data/provenance/ibm_aml_data_v8_li_small_source.json` |
| Triage distribution decision, approved for one review period | `data/provenance/ibm_aml_data_v8_triage_distribution.json` |
| Public URL | `https://signal-ledger-workbench.vercel.app` |
| Delivery state, phase and gates | private delivery records in the sibling ops folder |

The full IBM source is neither committed nor served.

## Acceptance checks

- Deterministic fixture rebuild matches the committed artifact.
- The alert store rebuilds byte for byte from the same source and parameter set.
- The leakage gate passes, and its own test proves it fails when a feature reads
  a transaction at or after the cutoff.
- The baseline ladder is scored on the same alert population for every rung, with
  absolute counts before rates, per typology attempt counts including the
  structural zeros, and bootstrap intervals. B3's rule hit rates read prior
  periods only.
- The HI-Small ladder and challenger reproduce every published number on rerun,
  and each run record carries the source file names and the alert store digest,
  because the engine version and the parameter hash are identical across variants
  and cannot tell two records apart.
- API and configuration tests pass. Malformed input receives a safe error, and
  write requests are rejected.
- The tuned rule parameter values do not appear anywhere in the triage artifact,
  asserted against both the parameter names and their distinctive values.
- Every ordering in the triage artifact covers the whole period with no gap, so
  the cut line is a rule drawn in a queue rather than a filter.
- The public application mode refuses an unapproved triage artifact, and also
  refuses an approved one that is not the pinned release, while keeping the
  replay artifact serving in both cases. The local mode drops the pin alone, so
  an operator can run an artifact they just built.
- Frontend lint and production build pass.
- Public browser checks show rendered content without errors. The triage journey
  additionally confirms the cut line is drawn with deferred alerts still visible
  and openable, that every rank cell computes to one colour, that the disposition
  control carries no default, and that both honest states render.
- A narrowed queue view still draws the cut line, states the count it is not
  showing, leaves every capacity number computed on the whole period, and puts no
  suppression word anywhere on the surface.
- Deployment readiness reports approved artifact delivery with no inference and
  no visitor persistence.
- The release verifier proves the local fixture contract and can compare the
  deployed artifact identity with the fixture on the public repository.
- The delivery graph is refreshed after committed code changes.

## Adding a case

Add a case only with a documented selection rule, provenance evidence, a
deterministic rebuild, bounded API and interface tests, browser verification, and
explicit owner approval. A case that cannot be rebuilt byte for byte from the
approved source does not ship.
