import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Case = { id: string; outcome: string; transaction_count: number };
type Detail = {
  id: string;
  outcome: string;
  transaction_count: number;
  uncertainty: string;
  rationale: string;
};
type Txn = {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  amount: number;
  currency: string;
  rail: string;
};
type Topology = {
  nodes: { id: string; label: string }[];
  edges: { source: string; target: string }[];
};
type Evidence = { items: { kind: string; statement: string }[]; uncertainty: string };
type Provenance = {
  provider: string;
  version: number;
  retrieved: string;
  license: string;
  source_sha256: string;
  slice_sha256: string;
  label: string;
};
type AuditAction = "Simulated escalation" | "Simulated closure";
type AuditEntry = {
  id: string;
  kind: "example" | "record";
  timestamp: string;
  case_id: string;
  case_outcome: string;
  action: AuditAction;
  rationale: string;
  fixture: { dataset_version: number | null; replay_sha256: string | null };
  visible_evidence: string[];
};

const AUDIT_STORAGE_KEY = "signal-ledger-simulated-audit/v1";
const SEEDED_AUDIT: AuditEntry = {
  id: "example-closure-record",
  kind: "example",
  timestamp: "2026-07-24T09:00:00.000Z",
  case_id: "sim-closure-compare",
  case_outcome: "Simulated closure",
  action: "Simulated closure",
  rationale: "Example only: the bounded replay is reviewed as a synthetic exercise, not a real-world conclusion.",
  fixture: { dataset_version: 8, replay_sha256: "e78b20e8445a7e818c95af6216258487c46cf59ac061c6fcef531f45e10b0160" },
  visible_evidence: ["Precomputed context only", "No request-time inference"],
};

const api = <T,>(path: string) =>
  fetch(`/api${path}`).then((response) =>
    response.ok
      ? (response.json() as Promise<T>)
      : Promise.reject(new Error("The bounded public casefile could not be loaded.")),
  );

function loadLocalAudit(): AuditEntry[] {
  try {
    const saved = window.localStorage.getItem(AUDIT_STORAGE_KEY);
    const parsed: unknown = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) ? parsed.filter((entry): entry is AuditEntry => typeof entry === "object" && entry !== null && "id" in entry && "action" in entry) : [];
  } catch {
    return [];
  }
}

function storeLocalAudit(entries: AuditEntry[]) {
  try {
    window.localStorage.setItem(AUDIT_STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // The simulated record remains visible for this page session if storage is unavailable.
  }
}

function topologyPoint(index: number, count: number) {
  const angle = (Math.PI * 2 * index) / Math.max(count, 1) - Math.PI / 2;
  return { x: 50 + Math.cos(angle) * 37, y: 50 + Math.sin(angle) * 35 };
}

function App() {
  const [cases, setCases] = useState<Case[]>([]);
  const [active, setActive] = useState<Case | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [timeline, setTimeline] = useState<Txn[]>([]);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [query, setQuery] = useState("");
  const [rail, setRail] = useState("all");
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [caseLoading, setCaseLoading] = useState(false);
  const [error, setError] = useState("");
  const [rationale, setRationale] = useState("");
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>(loadLocalAudit);
  const [auditMessage, setAuditMessage] = useState("");

  const loadCatalogue = () => {
    setLoading(true);
    setError("");
    Promise.all([api<{ items: Case[] }>("/cases"), api<Provenance>("/provenance")])
      .then(([catalogue, record]) => {
        setCases(catalogue.items);
        setActive(catalogue.items[0] ?? null);
        setProvenance(record);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCatalogue();
  }, []);

  useEffect(() => {
    if (!active) return;
    setCaseLoading(true);
    setCursor(0);
    setPlaying(false);
    setSelectedNode(null);
    setError("");
    const railQuery = rail === "all" ? "" : `&rail=${encodeURIComponent(rail)}`;
    Promise.all([
      api<Detail>(`/cases/${active.id}`),
      api<{ items: Txn[] }>(`/cases/${active.id}/timeline?limit=18${railQuery}`),
      api<Topology>(`/cases/${active.id}/graph?depth=2`),
      api<Evidence>(`/cases/${active.id}/evidence`),
    ])
      .then(([caseDetail, replay, graph, caseEvidence]) => {
        setDetail(caseDetail);
        setTimeline(replay.items);
        setTopology(graph);
        setEvidence(caseEvidence);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setCaseLoading(false));
  }, [active, rail]);

  useEffect(() => {
    if (!playing || timeline.length === 0) return;
    const timer = window.setInterval(() => {
      setCursor((current) => (current >= timeline.length - 1 ? 0 : current + 1));
    }, 1100);
    return () => window.clearInterval(timer);
  }, [playing, timeline.length]);

  const rails = useMemo(
    () => Array.from(new Set(timeline.map((item) => item.rail))).sort(),
    [timeline],
  );
  const visibleTimeline = timeline.slice(0, cursor + 1);
  const matchingCases = cases.filter((item) =>
    item.outcome.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const points = useMemo(
    () =>
      new Map(
        (topology?.nodes ?? []).map((node, index, nodes) => [
          node.id,
          topologyPoint(index, nodes.length),
        ]),
      ),
    [topology],
  );
  const auditHistory = [SEEDED_AUDIT, ...auditEntries];

  const recordSimulatedDecision = (action: AuditAction) => {
    if (!active || !detail) return;
    const entry: AuditEntry = {
      id: window.crypto.randomUUID(),
      kind: "record",
      timestamp: new Date().toISOString(),
      case_id: active.id,
      case_outcome: detail.outcome,
      action,
      rationale: rationale.trim() || "No rationale entered.",
      fixture: { dataset_version: provenance?.version ?? null, replay_sha256: provenance?.slice_sha256 ?? null },
      visible_evidence: evidence?.items.map((item) => item.statement) ?? [],
    };
    const next = [entry, ...auditEntries];
    setAuditEntries(next);
    storeLocalAudit(next);
    setRationale("");
    setAuditMessage(`${action} saved in this browser only.`);
  };

  const resetLocalAudit = () => {
    setAuditEntries([]);
    setRationale("");
    setAuditMessage("Your browser-local simulated records were cleared. The read-only example remains.");
    try {
      window.localStorage.removeItem(AUDIT_STORAGE_KEY);
    } catch {
      // The reset still applies to this page session if browser storage is unavailable.
    }
  };

  const exportLocalAudit = () => {
    const payload = {
      format: "signal-ledger-simulated-audit/v1",
      exported_at: new Date().toISOString(),
      local_only: true,
      records: auditHistory,
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "signal-ledger-simulated-audit.json";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setAuditMessage("Exported a local JSON copy. Nothing was sent to Signal Ledger.");
  };

  if (error && !active) {
    return (
      <main className="state" aria-live="polite">
        <p className="stamp">Public replay unavailable</p>
        <h1>Casefile unavailable.</h1>
        <p>{error}</p>
        <button type="button" onClick={loadCatalogue}>Retry public replay</button>
      </main>
    );
  }

  return (
    <main>
      <header className="masthead">
        <div>
          <p className="stamp">Public · realistic synthetic banking data</p>
          <h1>Signal Ledger</h1>
        </div>
        <p className="mast-meta"><i /> Deterministic replay · no live feed · no visitor inference</p>
      </header>

      <section className="opening" aria-labelledby="workbench-title">
        <div>
          <p className="stamp">Research workbench</p>
          <h2 id="workbench-title">Inspect the sequence before the simulated human record.</h2>
          <p>Six bounded cases make the time, counterparties, evidence, and limits inspectable. They do not identify people, produce a finding, or recommend a compliance action.</p>
        </div>
        <ol className="flow" aria-label="Investigation flow">
          <li><b>01</b><span>Select a synthetic case</span></li>
          <li><b>02</b><span>Replay time and topology</span></li>
          <li><b>03</b><span>Read evidence and limits</span></li>
          <li><b>04</b><span>Proceed to simulated record</span></li>
        </ol>
      </section>

      <section className="workbench" aria-label="Synthetic case investigation">
        <aside className="queue">
          <div className="panel-heading">
            <div><p className="stamp">Case queue</p><h2>Guided review</h2></div>
            <span>{cases.length} cases</span>
          </div>
          <label className="search-label" htmlFor="case-search">Filter simulated cases</label>
          <input id="case-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search escalation or closure" />
          <div className="case-list" aria-live="polite">
            {loading ? <p className="empty">Loading approved public cases…</p> : matchingCases.length === 0 ? <p className="empty">No simulated case matches that filter.</p> : matchingCases.map((item) => (
              <button className={`case-row ${active?.id === item.id ? "selected" : ""}`} type="button" key={item.id} onClick={() => setActive(item)} aria-pressed={active?.id === item.id}>
                <span className="case-index">{String.fromCharCode(65 + matchingCases.indexOf(item))}</span>
                <span className="case-copy"><strong>{item.outcome}</strong><small>{item.transaction_count} bounded transactions</small></span>
                <span aria-hidden="true">→</span>
              </button>
            ))}
          </div>
          <p className="queue-note">Precomputed illustrative ordering only. It is not a score or recommendation.</p>
        </aside>

        <section className="replay-panel" aria-labelledby="replay-title">
          <div className="panel-heading">
            <div><p className="stamp">Time-bound replay</p><h2 id="replay-title">{detail?.outcome ?? "Loading case…"}</h2></div>
            <span>{timeline.length ? `${cursor + 1} / ${timeline.length}` : "—"}</span>
          </div>
          <div className="replay-controls" aria-label="Replay controls">
            <button type="button" className="primary" onClick={() => setPlaying((value) => !value)} disabled={!timeline.length}>{playing ? "Pause replay" : "Play replay"}</button>
            <button type="button" onClick={() => { setPlaying(false); setCursor(0); }} disabled={!timeline.length}>Reset</button>
            <label htmlFor="rail-filter">Payment rail</label>
            <select id="rail-filter" value={rail} onChange={(event) => setRail(event.target.value)}>
              <option value="all">All rails</option>
              {rails.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          {caseLoading ? <div className="timeline-skeleton" aria-label="Loading replay" /> : timeline.length === 0 ? <p className="empty replay-empty">No transactions use this rail in the bounded replay.</p> : <ol className="timeline" aria-label="Replay timeline">
            {timeline.map((item, index) => (
              <li key={item.id} className={index <= cursor ? "shown" : ""}>
                <button type="button" onClick={() => setCursor(index)} aria-label={`Show transaction ${index + 1}: ${item.from} to ${item.to}`}>
                  <time>{item.timestamp}</time><span className="timeline-dot" /><span className="transaction"><b>{item.from} → {item.to}</b><small>{item.rail} · {item.id}</small></span><strong>{item.amount.toLocaleString(undefined, { maximumFractionDigits: 2 })} {item.currency}</strong>
                </button>
              </li>
            ))}
          </ol>}
          <p className="replay-status" aria-live="polite">{visibleTimeline.length ? `Showing the first ${visibleTimeline.length} event${visibleTimeline.length === 1 ? "" : "s"} in the bounded sequence.` : "Choose a rail to begin."}</p>
        </section>

        <aside className="evidence-panel" aria-label="Evidence and limitations">
          <div className="panel-heading"><div><p className="stamp">Context, not conclusion</p><h2>Evidence brief</h2></div></div>
          <p className="uncertainty">{detail?.uncertainty ?? "Loading limitations…"}</p>
          <ul className="evidence-list">
            {evidence?.items.map((item) => <li key={item.kind}><span>{item.kind}</span>{item.statement}</li>)}
          </ul>
          <div className="next-step"><p className="stamp">Simulated record</p><strong>Browser-private audit trail</strong><p>Any rationale and simulated decision stay in this browser and are never sent to this API.</p></div>
          {error && <div className="inline-error" role="alert"><span>{error}</span><button type="button" onClick={() => setActive(active)}>Retry case</button></div>}
        </aside>
      </section>

      <section className="audit-section" aria-labelledby="audit-title">
        <div className="section-intro"><p className="stamp">Simulated human record</p><h2 id="audit-title">Record a review exercise, not a compliance action.</h2><p>Your rationale, simulated disposition, and export remain browser-private. The approved fixture, visible evidence, action, rationale, and timestamp are captured locally.</p></div>
        <div className="audit-workspace">
          <form className="audit-form" onSubmit={(event) => event.preventDefault()}>
            <div className="panel-heading"><div><p className="stamp">Local-only entry</p><h2>{detail?.outcome ?? "Select a case"}</h2></div><span>{provenance ? `v${provenance.version}` : "—"}</span></div>
            <label htmlFor="rationale">Simulated reviewer rationale</label>
            <textarea id="rationale" value={rationale} onChange={(event) => setRationale(event.target.value)} placeholder="What did the bounded synthetic replay make easier or harder to understand?" />
            <p className="field-note">Optional. If blank, the local record states that no rationale was entered. Visible evidence: {evidence?.items.length ?? 0} items.</p>
            <div className="audit-actions"><button type="button" className="primary" onClick={() => recordSimulatedDecision("Simulated escalation")} disabled={!detail}>Simulate escalation</button><button type="button" onClick={() => recordSimulatedDecision("Simulated closure")} disabled={!detail}>Simulate closure</button></div>
            <p className="local-notice">No server record · no training · no inference · no compliance action</p>
          </form>
          <aside className="audit-history" aria-label="Browser-private simulated audit history">
            <div className="panel-heading"><div><p className="stamp">Local history</p><h2>Audit shape</h2></div><span>{auditHistory.length} entries</span></div>
            <p className="history-intro">A seeded example explains the format. New entries are stored only in this browser until you reset them.</p>
            <ol>
              {auditHistory.map((entry) => <li key={entry.id}><div><span className={entry.kind === "example" ? "example-badge" : "local-badge"}>{entry.kind === "example" ? "Read-only example" : "Local record"}</span><strong>{entry.action}</strong><time>{new Date(entry.timestamp).toLocaleString()}</time></div><p>{entry.rationale}</p><small>{entry.case_outcome} · {entry.visible_evidence.length} visible evidence items</small></li>)}
            </ol>
            <div className="history-actions"><button type="button" onClick={exportLocalAudit}>Export local JSON</button><button type="button" onClick={resetLocalAudit} disabled={auditEntries.length === 0}>Reset my local records</button></div>
            <p className="audit-message" aria-live="polite">{auditMessage}</p>
          </aside>
        </div>
      </section>

      <section className="topology-section" aria-labelledby="topology-title">
        <div className="section-intro"><p className="stamp">Bounded topology</p><h2 id="topology-title">Counterparties in this replay—not a network of real people.</h2><p>Use the keyboard or pointer to inspect a pseudonymous party. This view contains only the currently selected public synthetic case.</p></div>
        <div className="topology-frame">
          {caseLoading || !topology ? <div className="graph-empty">Loading bounded topology…</div> : <svg className="graph" viewBox="0 0 100 100" role="group" aria-label="Interactive bounded transaction topology">
            {topology.edges.map((edge, index) => {
              const source = points.get(edge.source); const target = points.get(edge.target);
              return source && target ? <line key={`${edge.source}-${edge.target}-${index}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} /> : null;
            })}
            {topology.nodes.map((node) => {
              const point = points.get(node.id)!; const isSelected = selectedNode === node.id;
              return <g key={node.id} className={isSelected ? "node selected-node" : "node"} role="button" tabIndex={0} aria-label={`Inspect ${node.label}`} aria-pressed={isSelected} onClick={() => setSelectedNode(node.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setSelectedNode(node.id); } }}><circle cx={point.x} cy={point.y} r="3.4" /><text x={point.x} y={point.y + 7}>{node.label.replace("Party-", "")}</text></g>;
            })}
          </svg>}
          <p className="graph-caption">{selectedNode ? `Selected ${topology?.nodes.find((node) => node.id === selectedNode)?.label}.` : "Select a party to inspect its pseudonymous label."}</p>
        </div>
      </section>

      <section className="method" aria-labelledby="provenance-title">
        <div><p className="stamp">Provenance & limits</p><h2 id="provenance-title">Data lineage stays in view.</h2><p>{provenance?.label}. This approved public slice is a deterministic IBM AML-Data v{provenance?.version} replay, not anonymized customer data.</p></div>
        <dl><div><dt>Provider</dt><dd>{provenance?.provider}</dd></div><div><dt>Source checksum</dt><dd>{provenance?.source_sha256}</dd></div><div><dt>Replay checksum</dt><dd>{provenance?.slice_sha256}</dd></div><div><dt>Research boundary</dt><dd>Elliptic rows, graphs, models, and reports remain local-only. This workbench exposes none of them.</dd></div></dl>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
