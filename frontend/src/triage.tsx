import { useEffect, useMemo, useState } from "react";

/**
 * The triage desk.
 *
 * Everything here is arithmetic over a precomputed artifact. The capacity
 * control moves a depth, and the consequence block recomputes counts from the
 * ordering that is already on the page. Nothing is scored, nothing is sent, and
 * no visitor supplied value reaches a rule or a model.
 *
 * Two rules from the design language are load bearing and are easy to undo by
 * accident. Rank carries no colour anywhere: no bar, no heat scale, no gradient,
 * because a colour scale invites rank to be read as a probability or a severity
 * and it is neither. And the cut line is a ruled separator inside the queue, so
 * every alert below it stays visible and openable at any depth.
 *
 * The filters are subordinate to both. They narrow what is on screen and they
 * never touch the ordering: a position is always the alert's position in the
 * whole period, the cut line is always drawn at the capacity depth, and a
 * narrowed view says how many alerts it is not showing and clears in one control.
 * The copy calls them a view, never a filter that removes or clears an alert,
 * because nothing on this surface disposes of anything without a human.
 */

type Delivery = { status: "approved" | "local-only"; published: boolean; statement: string };
type Ordering = { id: string; label: string; kind: "baseline" | "challenger"; ordered_on: string };
type MeasuredOrdering = {
  ordering: string;
  periods: number;
  worked: number;
  true_positives: number;
  precision: number;
  interval: number[];
};
type Gate = {
  metric: string;
  threshold: number;
  reference_rung: string;
  lift: number;
  interval: number[];
  met: boolean;
  promoted: boolean;
  statement: string;
};
type RuleParameter = { name: string; unit: string; effect: string };
type RuleSummary = {
  rule_id: string;
  name: string;
  meaning: string;
  parameters: RuleParameter[];
  alerts_in_store: number;
  alerts_in_period: number;
  supported: boolean;
  typologies: string[];
  attempts: number;
};
type TypologyCounts = { attempts_live: number; attempts_surfaced: number };
type TypologySummary = {
  typology: string;
  in_period: TypologyCounts;
  across_evaluation: TypologyCounts;
};
type PeriodAttempt = { attempt_id: number; typology: string; surfaced: boolean };
type PeriodResponse = {
  delivery: Delivery;
  claims: string;
  period: { start: string; alerts: number; true_positives: number; base_rate: number; label: string };
  operating_point: {
    analysts: number;
    productive_hours_per_analyst: number;
    handling_minutes_per_alert: number;
    k_alerts_worked_per_period: number;
    assumption_note: string;
  };
  orderings: Ordering[];
  result: { gate: Gate; measured: MeasuredOrdering[]; evaluation_periods: number; k: number };
  rules: RuleSummary[];
  typologies: TypologySummary[];
  period_attempts: PeriodAttempt[];
};
type QueueRow = {
  position: number;
  alert_id: string;
  subject: string;
  fired_rules: string[];
  first_transaction_at: string | null;
  alert_amount: number;
  contributing_transaction_count: number;
  is_true_positive: boolean;
  unattributed_only: boolean;
  typologies: string[];
  attempt_ids: number[];
};
type QueueResponse = {
  delivery: Delivery;
  ordering: Ordering;
  period_start: string;
  alerts: number;
  cut_line: number;
  cut_line_copy: string;
  items: QueueRow[];
};
type TriggerQuantity = { key: string; label: string; unit: string; value: number };
type Detail = {
  alert_id: string;
  subject: string;
  period_start: string;
  fired_rules: string[];
  alert_amount: number;
  ranks: Record<string, number>;
  trigger_evidence: { rule_id: string; quantities: TriggerQuantity[] }[];
  ranking_explanation: string;
  ranking_contributions: { feature: string; value: number; contribution: number }[];
  contributing_transaction_count: number;
  contributing_transactions: {
    id: string;
    timestamp: string;
    from: string;
    to: string;
    amount: number;
    currency: string;
    rail: string;
  }[];
  transaction_bound_note: string;
  is_true_positive: boolean;
  typologies: string[];
  disposition: string;
  disposition_storage: string;
};
type Reached = Record<string, number>;
type EvidenceResponse = {
  delivery: Delivery;
  claims: string;
  reference_rung: string;
  k: number;
  evidence: {
    funnel: {
      attempts_live: number;
      attempts_surfaced: number;
      attempts_reached: Reached;
      lost_before_ordering: number;
      statement: string;
    };
    typology_detail: {
      typology: string;
      attempts_live: number;
      attempts_surfaced: number;
      reached: Reached;
      recall_of_live: number;
      recall_of_surfaced: number;
      interval: number[];
    }[];
    unattributed: { alerts_in_population: number; reached: Reached; statement: string };
    per_period: {
      period_start: string;
      alerts: number;
      worked: number;
      coverage: number;
      true_positives: Reached;
      precision: Record<string, number>;
    }[];
    volume_reduction: {
      pooled: number;
      reference_rung: string;
      per_period: {
        period_start: string;
        alerts_target: number;
        alerts_depth: number;
        alerts_freed: number;
        attempts_target: number;
        attempts_depth: number;
        attempts_freed: number;
        target_was_zero: boolean;
      }[];
    };
    rank_stability: { threshold: number; pairs: { period_start: string; alerts: number; spearman: number }[] };
    feature_importance: {
      features_in_model: number;
      carried: number;
      bound_note: string;
      top: { feature: string; gain: number }[];
    };
  };
};
type Disposition = "Escalate" | "Close" | "Request more information";
type ReviewRecord = {
  id: string;
  alert_id: string;
  position: number;
  ordering: string;
  disposition: Disposition;
  rationale: string;
  recorded_at: string;
};

const DISPOSITIONS: Disposition[] = ["Escalate", "Close", "Request more information"];
const REVIEW_STORAGE_KEY = "signal-ledger-triage-review/v1";
const QUEUE_RENDER_LIMIT = 400;
/**
 * Series colours for the evidence charts.
 *
 * The desk's accent and status colours are chartreuse and archive orange, and
 * they stay that everywhere text carries the meaning too. They cannot both
 * encode series identity: as adjacent marks they collapse under deuteranopia to
 * an OKLab delta E of 1.8, so a red-green colourblind analyst could not separate
 * the binding baseline from the challenger. The challenger keeps a chartreuse
 * stepped into the dark lightness band, the baseline moves to blue, and orange
 * stays a labelled status colour for the capacity line rather than a series.
 */
const SERIES_CHALLENGER = "#7f9c22";
const SERIES_BASELINE = "#3987e5";
const SERIES_CAPACITY = "#c96a2e";

const ANY_TYPOLOGY = "any";
const NO_TYPOLOGY = "unattributed";
const ANY_DISPOSITION = "any";
const NO_DISPOSITION = "none";
const EXPORT_BOUNDARY =
  "Simulated dispositions recorded against realistic synthetic banking data. This is not a compliance record, not a suspicious activity report, and not a statement about any real person or organisation.";

const api = <T,>(path: string) =>
  fetch(`/api${path}`).then(async (response) => {
    const body: unknown = await response.json().catch(() => ({}));
    if (response.ok) return body as T;
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : "The triage artifact could not be loaded.";
    throw new Error(detail);
  });

function loadReviews(): ReviewRecord[] {
  try {
    const saved = window.localStorage.getItem(REVIEW_STORAGE_KEY);
    const parsed: unknown = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) ? (parsed as ReviewRecord[]) : [];
  } catch {
    return [];
  }
}

function storeReviews(entries: ReviewRecord[]) {
  try {
    window.localStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // The record stays visible for this page session if storage is unavailable.
  }
}

const count = (value: number) => value.toLocaleString();
const share = (value: number) => `${(value * 100).toFixed(1)} percent`;
const amount = (value: number) =>
  value.toLocaleString(undefined, { maximumFractionDigits: 0 });

/**
 * Attempts recovered by typology at a given depth, plus the depth each typology
 * needs before it recovers anything.
 *
 * The second number is what answers "which typology loses coverage first as
 * capacity falls": it is the typology whose first recovery sits deepest in the
 * queue, because that is the one the next cut removes.
 */
function coverage(rows: QueueRow[], attempts: PeriodAttempt[], depth: number) {
  const typologyOf = new Map(attempts.map((item) => [item.attempt_id, item.typology]));
  const firstDepth = new Map<number, number>();
  for (const row of rows) {
    for (const attempt of row.attempt_ids) {
      const current = firstDepth.get(attempt);
      if (current === undefined || row.position < current) firstDepth.set(attempt, row.position);
    }
  }
  const byTypology = new Map<string, { recovered: number; deepest: number | null }>();
  for (const attempt of attempts) {
    const typology = typologyOf.get(attempt.attempt_id) ?? attempt.typology;
    const entry = byTypology.get(typology) ?? { recovered: 0, deepest: null };
    const reached = firstDepth.get(attempt.attempt_id);
    if (reached !== undefined && reached <= depth) {
      entry.recovered += 1;
      entry.deepest = entry.deepest === null ? reached : Math.max(entry.deepest, reached);
    }
    byTypology.set(typology, entry);
  }
  return byTypology;
}

/**
 * The measured run, in the units the work happens in.
 *
 * This sits above the queue because it answers whether the queue is worth
 * trusting, and because the pooled figures it replaces hid the three facts that
 * actually bound the result: where the attempts are lost, that the flagged
 * alerts are overwhelmingly ones no typology claims, and that the periods are
 * not alike.
 */
function Evidence({ data, referenceRung, k }: { data: EvidenceResponse["evidence"]; referenceRung: string; k: number }) {
  const { funnel, typology_detail, unattributed, per_period, volume_reduction } = data;
  const stability = data.rank_stability;
  const importance = data.feature_importance;
  const peak = Math.max(...per_period.map((row) => row.alerts));
  const gainTop = importance.top[0]?.gain ?? 1;
  const negativePeriods = volume_reduction.per_period.filter((row) => row.attempts_freed < 0);
  const worst = per_period.reduce((low, row) => (row.coverage < low.coverage ? row : low), per_period[0]);
  const best = per_period.reduce((high, row) => (row.coverage > high.coverage ? row : high), per_period[0]);

  return (
    <div className="evidence">
      <div className="panel-heading">
        <div>
          <p className="stamp">Where the alerts go</p>
          <h3>The measured run, per period and per typology</h3>
        </div>
        <span className="monospace">{per_period.length} periods · K = {count(k)}</span>
      </div>

      <div className="funnel" aria-label="Attempt funnel">
        <div>
          <p className="stamp">Attempts live</p>
          <p className="figure monospace">{count(funnel.attempts_live)}</p>
          <p className="field-note">Laundering attempts in the evaluation window.</p>
        </div>
        <div>
          <p className="stamp">Surfaced by the rules</p>
          <p className="figure monospace surfaced">{count(funnel.attempts_surfaced)}</p>
          <p className="drop monospace">
            minus {count(funnel.lost_before_ordering)} ·{" "}
            {share(funnel.lost_before_ordering / funnel.attempts_live)} lost here
          </p>
        </div>
        <div>
          <p className="stamp">Reached at K by C1</p>
          <p className="figure monospace reached">{count(funnel.attempts_reached.C1 ?? 0)}</p>
          <p className="field-note">
            {referenceRung} reaches {count(funnel.attempts_reached[referenceRung] ?? 0)} of the same{" "}
            {count(funnel.attempts_surfaced)}.
          </p>
        </div>
      </div>
      <p className="limitation">{funnel.statement}</p>

      <h4>Every week is a different week</h4>
      <table className="typology-table">
        <caption>
          Alert volume against a capacity that does not move. Coverage is what a fixed team actually
          sees of that period.
        </caption>
        <thead>
          <tr>
            <th scope="col">Period</th>
            <th scope="col">Alerts</th>
            <th scope="col">Coverage at K</th>
            <th scope="col">{referenceRung} found</th>
            <th scope="col">C1 found</th>
          </tr>
        </thead>
        <tbody>
          {per_period.map((row) => (
            <tr key={row.period_start}>
              <th scope="row" className="monospace">{row.period_start}</th>
              <td className="monospace">
                <span className="volume-bar" style={{ width: `${(row.alerts / peak) * 100}%` }} />
                {count(row.alerts)}
              </td>
              <td className="monospace">{share(row.coverage)}</td>
              <td className="monospace">{row.true_positives[referenceRung]}</td>
              <td className="monospace reached">{row.true_positives.C1}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="limitation">
        Volume swings {count(Math.min(...per_period.map((r) => r.alerts)))} to {count(peak)} alerts.
        At a capacity that does not move, that is {share(worst.coverage)} of the {worst.period_start}{" "}
        period against {share(best.coverage)} of {best.period_start}. A pooled figure averages those
        together and hides the week that costs the most.
      </p>

      <h4>Two denominators, because they answer different questions</h4>
      <table className="typology-table">
        <caption>
          Recall against every live attempt scores the rules. Recall of what the rules surfaced
          scores the ordering. Reporting only the first blames the ranking for a population it never
          had.
        </caption>
        <thead>
          <tr>
            <th scope="col">Typology</th>
            <th scope="col">Live</th>
            <th scope="col">Surfaced</th>
            <th scope="col">C1 reached</th>
            <th scope="col">Recall of live</th>
            <th scope="col">Recall of surfaced</th>
          </tr>
        </thead>
        <tbody>
          {typology_detail.map((row) => (
            <tr key={row.typology} className={row.attempts_surfaced === 0 ? "unsurfaced" : ""}>
              <th scope="row">{row.typology}</th>
              <td className="monospace">{row.attempts_live}</td>
              <td className="monospace surfaced">{row.attempts_surfaced}</td>
              <td className="monospace reached">{row.reached.C1 ?? 0}</td>
              <td className="monospace">{share(row.recall_of_live)}</td>
              <td className="monospace strong">
                {row.attempts_surfaced === 0 ? "no denominator" : share(row.recall_of_surfaced)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h4>The line that carries the result</h4>
      <table className="typology-table">
        <caption>
          Flagged alerts no injected attempt claims. The population is the same{" "}
          {count(unattributed.alerts_in_population)} for every ordering, and per typology recall
          cannot see them at all.
        </caption>
        <thead>
          <tr>
            <th scope="col">Ordering</th>
            <th scope="col">Recovered</th>
            <th scope="col">Of {count(unattributed.alerts_in_population)}</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(unattributed.reached).map(([rung, value]) => (
            <tr key={rung} className={rung === "C1" ? "highlight" : ""}>
              <th scope="row">{rung}</th>
              <td className="monospace">{count(value)}</td>
              <td className="monospace">{share(value / unattributed.alerts_in_population)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="limitation">{unattributed.statement}</p>

      <h4>The volume claim, unpooled</h4>
      <table className="typology-table">
        <caption>
          Volume freed against {volume_reduction.reference_rung} at equal coverage. A negative figure
          means the challenger cost more, not less, and the sign is kept rather than smoothed away.
        </caption>
        <thead>
          <tr>
            <th scope="col">Period</th>
            <th scope="col">Alerts freed</th>
            <th scope="col">Attempt target</th>
            <th scope="col">Attempt depth</th>
            <th scope="col">Attempts freed</th>
          </tr>
        </thead>
        <tbody>
          {volume_reduction.per_period.map((row) => (
            <tr key={row.period_start} className={row.attempts_freed < 0 ? "costlier" : ""}>
              <th scope="row" className="monospace">{row.period_start}</th>
              <td className="monospace">{row.alerts_freed}</td>
              <td className="monospace">
                {row.attempts_target}
                {row.target_was_zero ? " · target was zero" : ""}
              </td>
              <td className="monospace">{row.attempts_depth}</td>
              <td className="monospace strong">{row.attempts_freed}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="limitation">
        Pooled, the alert based reduction is {share(volume_reduction.pooled)}. Per period the attempt
        based measure is negative in {negativePeriods.length} of{" "}
        {volume_reduction.per_period.length} periods. Both are shown, because the pooled figure alone
        would be the most misleading number this project could publish.
      </p>

      <div className="model-card">
        <div>
          <h4>What the ordering keys on</h4>
          <ul className="gain-list">
            {importance.top.map((row) => (
              <li key={row.feature}>
                <span className="monospace">{row.feature}</span>
                <span className="gain-bar" style={{ width: `${(row.gain / gainTop) * 100}%` }} />
                <span className="monospace gain-value">{row.gain.toFixed(1)}</span>
              </li>
            ))}
          </ul>
          <p className="field-note">{importance.bound_note}</p>
        </div>
        <div>
          <h4>Would the queue reshuffle on retrain</h4>
          <ul className="stability-list">
            {stability.pairs.map((pair) => (
              <li key={pair.period_start} className="monospace">
                {pair.period_start} · {pair.spearman.toFixed(4)}
              </li>
            ))}
          </ul>
          <p className="field-note">
            Spearman correlation between consecutive orderings across{" "}
            {stability.pairs.length} pairs, against a threshold of {stability.threshold.toFixed(2)}.
            A queue that reshuffled every retrain would not be workable whatever its precision.
          </p>
        </div>
      </div>
    </div>
  );
}

export function TriageDesk() {
  const [period, setPeriod] = useState<PeriodResponse | null>(null);
  const [queue, setQueue] = useState<QueueResponse | null>(null);
  const [ordering, setOrdering] = useState("C1");
  const [handling, setHandling] = useState(20);
  const [hours, setHours] = useState(42);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [unavailable, setUnavailable] = useState("");
  const [loading, setLoading] = useState(true);
  const [rationale, setRationale] = useState("");
  const [chosen, setChosen] = useState<Disposition | "">("");
  const [reviews, setReviews] = useState<ReviewRecord[]>(loadReviews);
  const [notice, setNotice] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [typologyView, setTypologyView] = useState(ANY_TYPOLOGY);
  const [dispositionView, setDispositionView] = useState(ANY_DISPOSITION);
  const [exportNotice, setExportNotice] = useState("");

  useEffect(() => {
    setLoading(true);
    api<PeriodResponse>("/triage/period")
      .then((response) => {
        setPeriod(response);
        setHandling(response.operating_point.handling_minutes_per_alert);
        setHours(
          response.operating_point.analysts *
            response.operating_point.productive_hours_per_analyst,
        );
        setUnavailable("");
      })
      .catch((reason: Error) => setUnavailable(reason.message))
      .finally(() => setLoading(false));
  }, []);

  // The evidence answers whether the queue is worth trusting, so a failure here
  // must not take the queue down with it. It renders when it arrives.
  useEffect(() => {
    if (!period) return;
    api<EvidenceResponse>("/triage/evidence")
      .then(setEvidence)
      .catch(() => setEvidence(null));
  }, [period]);

  useEffect(() => {
    if (!period) return;
    api<QueueResponse>(`/triage/queue?ordering=${encodeURIComponent(ordering)}`)
      .then((response) => {
        setQueue(response);
        setShowAll(false);
      })
      .catch((reason: Error) => setUnavailable(reason.message));
  }, [period, ordering]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    api<Detail>(`/triage/alerts/${selected}?ordering=${encodeURIComponent(ordering)}`)
      .then(setDetail)
      .catch((reason: Error) => setUnavailable(reason.message));
  }, [selected, ordering]);

  const capacity = period
    ? period.operating_point.analysts * period.operating_point.productive_hours_per_analyst
    : 0;
  // The control is expressed in analyst hours, which is the stakeholder's unit,
  // and the alert count is derived from it. Handling time is the conversion and
  // is an assumption rather than a measurement, so it is adjustable and says so.
  const depth = useMemo(() => {
    if (!period) return 0;
    const derived = Math.floor((hours * 60) / Math.max(handling, 1));
    return Math.max(1, Math.min(derived, period.period.alerts));
  }, [period, hours, handling]);

  const rows = queue?.items ?? [];
  // Every consequence number below is computed on the whole period, never on the
  // narrowed view. A view that changed the capacity arithmetic would let a
  // reader move a filter and believe the queue got shorter.
  const worked = rows.filter((row) => row.position <= depth);
  const found = worked.filter((row) => row.is_true_positive).length;
  // The most recent disposition wins, and entries are stored newest first.
  const dispositionOf = useMemo(() => {
    const latest = new Map<string, Disposition>();
    for (const entry of reviews) {
      if (!latest.has(entry.alert_id)) latest.set(entry.alert_id, entry.disposition);
    }
    return latest;
  }, [reviews]);
  const narrowed = typologyView !== ANY_TYPOLOGY || dispositionView !== ANY_DISPOSITION;
  const filtered = useMemo(
    () =>
      rows.filter((row) => {
        const typologyMatch =
          typologyView === ANY_TYPOLOGY ||
          (typologyView === NO_TYPOLOGY
            ? row.unattributed_only
            : row.typologies.includes(typologyView));
        const recorded = dispositionOf.get(row.alert_id);
        const dispositionMatch =
          dispositionView === ANY_DISPOSITION ||
          (dispositionView === NO_DISPOSITION ? !recorded : recorded === dispositionView);
        return typologyMatch && dispositionMatch;
      }),
    [rows, typologyView, dispositionView, dispositionOf],
  );
  const byTypology = useMemo(
    () => coverage(rows, period?.period_attempts ?? [], depth),
    [rows, period, depth],
  );
  const surfacedTypologies = (period?.typologies ?? []).filter(
    (item) => item.in_period.attempts_surfaced > 0,
  );
  const losesFirst = surfacedTypologies
    .map((item) => ({ typology: item.typology, deepest: byTypology.get(item.typology)?.deepest ?? null }))
    .filter((item) => item.deepest !== null)
    .sort((left, right) => (right.deepest ?? 0) - (left.deepest ?? 0))[0];

  const recordReview = () => {
    if (!detail || !chosen) return;
    const entry: ReviewRecord = {
      id: window.crypto.randomUUID(),
      alert_id: detail.alert_id,
      position: detail.ranks[ordering] ?? 0,
      ordering,
      disposition: chosen,
      rationale: rationale.trim() || "No rationale entered.",
      recorded_at: new Date().toISOString(),
    };
    const next = [entry, ...reviews];
    setReviews(next);
    storeReviews(next);
    setChosen("");
    setRationale("");
    setNotice(`${entry.disposition} recorded in this browser only. Nothing was sent to the server.`);
  };

  /**
   * Write the browser held review record to a file the operator keeps.
   *
   * The export travels with the identity of what was reviewed and with the same
   * claims boundary the surface carries, because a file outlives the page it
   * came from and a bare list of dispositions would read as a compliance record.
   */
  const exportReviewRecord = () => {
    if (!period || !reviews.length) return;
    const payload = {
      export_kind: "signal-ledger-triage-review-record",
      export_schema: 1,
      exported_at: new Date().toISOString(),
      review_period: period.period.start,
      ordering_on_screen: ordering,
      delivery: period.delivery.statement,
      claims: period.claims,
      boundary: EXPORT_BOUNDARY,
      record_count: reviews.length,
      records: reviews,
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = `signal-ledger-review-record-${period.period.start}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setExportNotice(
      `${reviews.length} review records written to a file by this browser. Nothing was sent to the server.`,
    );
  };

  if (loading) {
    return (
      <section className="triage" aria-labelledby="triage-title">
        <h2 id="triage-title">Loading the review period…</h2>
      </section>
    );
  }

  if (unavailable || !period || !queue) {
    return (
      <section className="triage" aria-labelledby="triage-title">
        <div className="section-intro">
          <p className="stamp">Triage queue</p>
          <h2 id="triage-title">The triage queue is not being served here.</h2>
          <p>
            {unavailable || "No triage artifact is available on this surface."} A triage artifact is
            admitted only when it matches its own content checksum, carries an owner recorded
            distribution decision against the exact verified source checksum, and is the pinned
            release that decision was recorded against. Anything else is refused rather than served,
            which is why this state exists and renders at full weight. The approved replay workbench
            is unaffected and continues to serve.
          </p>
        </div>
      </section>
    );
  }

  const gate = period.result.gate;
  const reference = period.result.measured.find((item) => item.ordering === gate.reference_rung);
  const challenger = period.result.measured.find((item) => item.ordering === "C1");
  const active = period.orderings.find((item) => item.id === ordering)!;
  const visible = showAll ? filtered : filtered.slice(0, Math.max(QUEUE_RENDER_LIMIT, depth + 20));
  // The cut line is drawn before the first row on screen that sits past the
  // capacity depth. Anchoring it to the row at depth + 1 would let a narrowed
  // view drop the separator, and the constraint it draws is not optional.
  const cutIndex = visible.findIndex((row) => row.position > depth);

  return (
    <section className="triage" aria-labelledby="triage-title">
      <div className="section-intro">
        <p className="stamp">Triage queue · {period.period.label}</p>
        <h2 id="triage-title">
          At the capacity you have, what do you get and what do you give up?
        </h2>
        <p className="claims">{period.claims}</p>
        <p className={period.delivery.published ? "delivery" : "delivery delivery-local"}>
          {period.delivery.statement}
        </p>
      </div>

      <div className="baseline-wins" role="note">
        <p className="stamp">Measured result</p>
        <h3>{gate.met ? "The learned ranker cleared the gate." : "The baseline holds. No model ships."}</h3>
        <p>{gate.statement}</p>
        <p className="monospace">
          {gate.metric}: lift {gate.lift.toFixed(4)} against a gate of {gate.threshold.toFixed(2)}, 95
          percent interval {gate.interval[0].toFixed(4)} to {gate.interval[1].toFixed(4)}, measured
          against {gate.reference_rung} over {period.result.evaluation_periods} evaluation periods at K
          = {period.result.k}.
        </p>
        {reference && challenger && (
          <p className="monospace">
            {gate.reference_rung} found {count(reference.true_positives)} true positives in{" "}
            {count(reference.worked)} worked alerts, {share(reference.precision)}. C1 found{" "}
            {count(challenger.true_positives)} in the same volume, {share(challenger.precision)}.
          </p>
        )}
        <p className="limitation">
          Definition: true positives inside the worked depth, as a count first and a rate second.
          Direction: higher is better. Baseline: the strongest rung of the ladder. Limitation: the
          outcome is a simulator flag, so this says nothing about real world detection.
        </p>
      </div>

      <div className="capacity" aria-label="Capacity control">
        <div className="capacity-control">
          <p className="stamp">Capacity</p>
          <h3>
            {period.operating_point.analysts} analysts, {period.operating_point.productive_hours_per_analyst}{" "}
            productive hours each
          </h3>
          <label htmlFor="hours">Analyst hours spent on this period</label>
          <input
            id="hours"
            type="range"
            min={1}
            max={Math.round(capacity)}
            step={1}
            value={Math.round(hours)}
            onChange={(event) => setHours(Number(event.target.value))}
          />
          <p className="monospace">
            {hours.toFixed(0)} of {capacity.toFixed(0)} available analyst hours ·{" "}
            {count(depth)} alerts reached
          </p>
          <label htmlFor="handling">Handling time per alert, minutes</label>
          <input
            id="handling"
            type="range"
            min={5}
            max={60}
            step={1}
            value={handling}
            onChange={(event) => setHandling(Number(event.target.value))}
          />
          <p className="monospace">{handling} minutes per alert</p>
          <p className="field-note">{period.operating_point.assumption_note}</p>
          <fieldset className="ordering-switch">
            <legend>Order the queue by</legend>
            {period.orderings.map((item) => (
              <label key={item.id}>
                <input
                  type="radio"
                  name="ordering"
                  value={item.id}
                  checked={ordering === item.id}
                  onChange={() => setOrdering(item.id)}
                />
                <span>
                  {item.id} {item.label}
                  {item.kind === "challenger" ? " · not promoted" : ""}
                </span>
              </label>
            ))}
          </fieldset>
          <p className="field-note">{active.ordered_on}</p>
        </div>

        <div className="consequence" aria-live="polite">
          <p className="stamp">At this capacity</p>
          <dl>
            <div>
              <dt>Alerts included</dt>
              <dd className="monospace">
                {count(depth)} of {count(period.period.alerts)} · {share(depth / period.period.alerts)}
              </dd>
            </div>
            <div>
              <dt>Analyst hours implied</dt>
              <dd className="monospace">
                {((depth * handling) / 60).toFixed(1)} of {capacity.toFixed(0)} available at{" "}
                {handling} minutes per alert
              </dd>
            </div>
            <div>
              <dt>True positive alerts reached</dt>
              <dd className="monospace">
                {count(found)} of {count(period.period.true_positives)} in the period
              </dd>
            </div>
            <div>
              <dt>Not reached at this capacity</dt>
              <dd className="monospace">
                {count(period.period.alerts - depth)} alerts, still open and workable
              </dd>
            </div>
            <div>
              <dt>Loses coverage first as capacity falls</dt>
              <dd>
                {losesFirst
                  ? `${losesFirst.typology}, whose deepest recovered attempt sits at position ${losesFirst.deepest}.`
                  : "No typology is recovered at this depth, so there is no coverage to lose."}
              </dd>
            </div>
          </dl>
          <table className="typology-table">
            <caption>
              Attempts recovered at this depth, by injected typology. Live and surfaced counts are
              for this review period.
            </caption>
            <thead>
              <tr>
                <th scope="col">Typology</th>
                <th scope="col">Recovered</th>
                <th scope="col">Surfaced by rules</th>
                <th scope="col">Live in period</th>
              </tr>
            </thead>
            <tbody>
              {period.typologies.map((item) => {
                const entry = byTypology.get(item.typology);
                // Not a structural zero. The simulator does generate these
                // typologies; the rules raised no alert on them in this period,
                // which is a different statement and gets a different mark.
                const unsurfaced = item.in_period.attempts_surfaced === 0;
                return (
                  <tr key={item.typology} className={unsurfaced ? "unsurfaced" : ""}>
                    <th scope="row">{item.typology}</th>
                    <td className="monospace">{entry?.recovered ?? 0}</td>
                    <td className="monospace">{item.in_period.attempts_surfaced}</td>
                    <td className="monospace">{item.in_period.attempts_live}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="limitation">
            No rule raised an alert on the typologies showing zero surfaced attempts in this period,
            so no ordering can recover them. That is a property of the alert population, not of the
            ranking.
          </p>
        </div>
      </div>

      {evidence && (
        <Evidence
          data={evidence.evidence}
          referenceRung={evidence.reference_rung}
          k={evidence.k}
        />
      )}

      <div className="queue-frame">
        <div className="panel-heading">
          <div>
            <p className="stamp">Review period {queue.period_start}</p>
            <h3>
              {active.id} {active.label}
            </h3>
          </div>
          <span className="monospace">{count(period.period.alerts)} alerts</span>
        </div>

        <div className="queue-view" aria-label="Queue view">
          <div className="view-controls">
            <div>
              <label htmlFor="typology-view">Typology</label>
              <select
                id="typology-view"
                value={typologyView}
                onChange={(event) => {
                  setTypologyView(event.target.value);
                  setShowAll(false);
                }}
              >
                <option value={ANY_TYPOLOGY}>Any typology</option>
                {period.typologies.map((item) => (
                  <option key={item.typology} value={item.typology}>
                    {item.typology}
                  </option>
                ))}
                <option value={NO_TYPOLOGY}>No typology attribution</option>
              </select>
            </div>
            <div>
              <label htmlFor="disposition-view">Disposition status</label>
              <select
                id="disposition-view"
                value={dispositionView}
                onChange={(event) => {
                  setDispositionView(event.target.value);
                  setShowAll(false);
                }}
              >
                <option value={ANY_DISPOSITION}>Any status</option>
                <option value={NO_DISPOSITION}>No disposition recorded</option>
                {DISPOSITIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            {narrowed && (
              <button
                type="button"
                className="clear-view"
                onClick={() => {
                  setTypologyView(ANY_TYPOLOGY);
                  setDispositionView(ANY_DISPOSITION);
                  setShowAll(false);
                }}
              >
                Show the whole period
              </button>
            )}
          </div>
          <p className="field-note" aria-live="polite">
            {narrowed
              ? `Showing ${count(filtered.length)} of ${count(rows.length)} alerts. This narrows the view only. Positions and the cut line are computed on the whole period, and the ${count(rows.length - filtered.length)} alerts not on screen are still in the queue and still workable.`
              : `Showing the whole period. Review period ${queue.period_start}; the artifact carries this one period, so there is nothing to select across periods.`}
          </p>
        </div>

        <a className="skip-queue" href="#past-the-queue">
          Skip past {count(visible.length)} alerts to{" "}
          {detail ? "the open alert detail" : "the review record"}. Every one of them stays in the
          queue.
        </a>

        <ol className="triage-queue" aria-label="Ranked alert queue">
          {visible.map((row, index) => (
            <li key={row.alert_id}>
              {index === cutIndex && (
                <p className="cut-line" role="separator">
                  Cut line at {count(depth)} alerts. {queue.cut_line_copy}
                </p>
              )}
              <button
                type="button"
                className={`queue-row ${selected === row.alert_id ? "selected" : ""} ${
                  row.position > depth ? "deferred" : ""
                }`}
                onClick={() => setSelected(row.alert_id === selected ? null : row.alert_id)}
                aria-pressed={selected === row.alert_id}
              >
                <span className="rank monospace">{row.position}</span>
                <span className="alert-id monospace">{row.alert_id}</span>
                <span className="rule-pills">
                  {row.fired_rules.map((rule) => {
                    const meta = period.rules.find((item) => item.rule_id === rule);
                    return (
                      <abbr key={rule} title={meta ? meta.name : rule}>
                        {rule}
                      </abbr>
                    );
                  })}
                </span>
                <span className="subject monospace">{row.subject}</span>
                <span className="amount monospace">{amount(row.alert_amount)}</span>
                <span className="status">
                  {dispositionOf.get(row.alert_id) ??
                    (row.position > depth ? "Not reached at this capacity" : "No disposition")}
                </span>
              </button>
            </li>
          ))}
        </ol>
        {visible.length > 0 && cutIndex === -1 && (
          <p className="cut-line" role="separator">
            Cut line at {count(depth)} alerts. {queue.cut_line_copy} Every alert in this view sits
            above it.
          </p>
        )}
        {visible.length === 0 && (
          <p className="queue-empty">
            No alert in this period matches this view. The {count(rows.length)} alerts of the period
            are unchanged and still workable. Widen the view to reach them.
          </p>
        )}
        {!showAll && filtered.length > visible.length && (
          <button type="button" className="show-all" onClick={() => setShowAll(true)}>
            Show the remaining {count(filtered.length - visible.length)} alerts. None is hidden by
            rank.
          </button>
        )}
      </div>

      {detail && (
        <div
          className="alert-detail"
          aria-label="Alert detail"
          id="past-the-queue"
          tabIndex={-1}
        >
          <div className="panel-heading">
            <div>
              <p className="stamp">Alert {detail.alert_id}</p>
              <h3>{detail.subject}</h3>
            </div>
            <button type="button" onClick={() => setSelected(null)}>
              Close detail
            </button>
          </div>

          <h4>Why this alert exists</h4>
          {detail.trigger_evidence.map((item) => {
            const meta = period.rules.find((rule) => rule.rule_id === item.rule_id);
            return (
              <div className="evidence-block" key={item.rule_id}>
                <p>
                  <b>
                    {item.rule_id} {meta?.name}
                  </b>{" "}
                  {meta?.meaning}
                </p>
                <ul>
                  {item.quantities.map((quantity) => (
                    <li key={quantity.key} className="monospace">
                      {quantity.label}: {quantity.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}{" "}
                      {quantity.unit}
                    </li>
                  ))}
                </ul>
                <p className="field-note">
                  Parameters:{" "}
                  {meta?.parameters
                    .map((parameter) => `${parameter.name} in ${parameter.unit}, ${parameter.effect}`)
                    .join("; ")}
                  . The tuned values are held privately and are not published here.
                </p>
              </div>
            );
          })}

          <h4>Why it is here in the queue</h4>
          <p>{detail.ranking_explanation}</p>
          {detail.ranking_contributions.length > 0 ? (
            <ul className="contributions">
              {detail.ranking_contributions.map((item) => (
                <li key={item.feature} className="monospace">
                  {item.feature} at {item.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}{" "}
                  {item.contribution >= 0 ? "lifted" : "lowered"} the score by{" "}
                  {Math.abs(item.contribution).toFixed(4)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="field-note">
              This ordering is a baseline, so there is no model contribution to show. It sorts on the
              quantity named above and nothing else.
            </p>
          )}

          <h4>Contributing transactions</h4>
          <p className="field-note">{detail.transaction_bound_note}</p>
          <table className="txn-table">
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Amount</th>
                <th scope="col">Rail</th>
              </tr>
            </thead>
            <tbody>
              {detail.contributing_transactions.map((txn) => (
                <tr key={txn.id}>
                  <td className="monospace">{txn.timestamp}</td>
                  <td className="monospace">{txn.from}</td>
                  <td className="monospace">{txn.to}</td>
                  <td className="monospace amount">
                    {amount(txn.amount)} {txn.currency}
                  </td>
                  <td>{txn.rail}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h4>Simulated outcome</h4>
          <p>
            {detail.is_true_positive
              ? "At least one contributing transaction carries the simulator's laundering flag."
              : "No contributing transaction carries the simulator's laundering flag."}{" "}
            {detail.typologies.length
              ? `Attributed typologies: ${detail.typologies.join(", ")}.`
              : "No injected attempt claims these transactions, so this alert carries no typology attribution."}{" "}
            This outcome is known because the source is a labelled simulation replayed after the
            fact. It is not a prediction and it was not available to the ordering.
          </p>

          <h4>Disposition</h4>
          <p className="field-note">{detail.disposition}</p>
          <fieldset className="disposition">
            <legend>Record a simulated disposition</legend>
            {DISPOSITIONS.map((option) => (
              <label key={option}>
                <input
                  type="radio"
                  name="disposition"
                  value={option}
                  checked={chosen === option}
                  onChange={() => setChosen(option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </fieldset>
          <label htmlFor="triage-rationale">Rationale</label>
          <textarea
            id="triage-rationale"
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            placeholder="What in the evidence decided it?"
          />
          <button type="button" className="primary" disabled={!chosen} onClick={recordReview}>
            Record this disposition
          </button>
          <p className="local-notice">{detail.disposition_storage}</p>
          <p className="audit-message" aria-live="polite">
            {notice}
          </p>
        </div>
      )}

      <div
        className="review-record"
        aria-label="Review record"
        id={detail ? undefined : "past-the-queue"}
        tabIndex={detail ? undefined : -1}
      >
        <div className="panel-heading">
          <div>
            <p className="stamp">Review record</p>
            <h3>What this browser holds, and how to take it with you</h3>
          </div>
          <span className="monospace">{count(reviews.length)} recorded</span>
        </div>
        {reviews.length === 0 ? (
          <p className="field-note">
            No disposition has been recorded in this browser. Open an alert, choose a disposition and
            write a rationale, and it will appear here.
          </p>
        ) : (
          <ol className="record-list">
            {reviews.slice(0, 12).map((entry) => (
              <li key={entry.id}>
                <span className="monospace">{entry.recorded_at}</span>
                <span className="monospace">{entry.alert_id}</span>
                <span>
                  {entry.disposition} at position {entry.position} under {entry.ordering}
                </span>
                <span className="rationale">{entry.rationale}</span>
              </li>
            ))}
          </ol>
        )}
        {reviews.length > 12 && (
          <p className="field-note">
            Showing the 12 most recent of {count(reviews.length)}. The export carries all of them.
          </p>
        )}
        <button
          type="button"
          className="primary"
          disabled={reviews.length === 0}
          onClick={exportReviewRecord}
        >
          Export the review record
        </button>
        <p className="field-note">
          The file is written by this browser and carries the review period, the ordering on screen,
          and the claims boundary. {EXPORT_BOUNDARY}
        </p>
        <p className="local-notice">
          Dispositions live in this browser alone. They are never sent to this API, and exporting
          writes a local file rather than uploading anything.
        </p>
        <p className="audit-message" aria-live="polite">
          {exportNotice}
        </p>
      </div>

      <div className="rule-catalogue">
        <div className="panel-heading">
          <div>
            <p className="stamp">Rule catalogue</p>
            <h3>What each rule means, what it costs, and what it can reach</h3>
          </div>
        </div>
        <table className="typology-table">
          <caption>
            Alert volume is a measured cost. A rule with no injected counterpart carries an attempt
            count of zero by construction.
          </caption>
          <thead>
            <tr>
              <th scope="col">Rule</th>
              <th scope="col">Meaning</th>
              <th scope="col">Alerts in period</th>
              <th scope="col">Alerts in store</th>
              <th scope="col">Attempts available</th>
            </tr>
          </thead>
          <tbody>
            {period.rules.map((rule) => (
              <tr key={rule.rule_id} className={rule.supported ? "" : "structural"}>
                <th scope="row">
                  {rule.rule_id} {rule.name}
                </th>
                <td>
                  {rule.meaning}
                  {!rule.supported && (
                    <span className="structural-note">
                      Structural zero. The simulator generates no counterpart for this rule, so its
                      recall is zero by construction and not by failure. Its alert volume is a real
                      analyst cost and is the finding.
                    </span>
                  )}
                </td>
                <td className="monospace">{count(rule.alerts_in_period)}</td>
                <td className="monospace">{count(rule.alerts_in_store)}</td>
                <td className="monospace">{count(rule.attempts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
