import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Case = { id:string; title:string; score:number; band:string; status:string; time:string; reason:string; signals:string[]; evidence:string[]; note:string };
type Graph = { nodes:{id:string;label:string;kind:string;x:number;y:number}[]; edges:{source:string;target:string}[] };
type Brief = { brief:{title:string;subtitle:string;mode:string;disclaimer:string;updated:string}; governance:string[]; evidence:{fixture:string;source:string;access:string;evaluation:string;limitations:string[]} };

const api = async <T,>(path:string):Promise<T> => { const response = await fetch(`/api${path}`); if (!response.ok) throw new Error("The synthetic casefile could not be loaded. Refresh to retry."); return response.json() as Promise<T>; };

function GraphView({ graph, active, selectedNode, onNodeSelect, error, retry }: {graph:Graph | null; active:Case; selectedNode:string; onNodeSelect:(label:string)=>void; error:string; retry:()=>void}) {
  if (error) return <div className="graph-empty"><p>{error}</p><button onClick={retry}>Retry bounded graph</button></div>;
  if (!graph) return <div className="graph-empty">Loading bounded graph…</div>;
  const lookup = Object.fromEntries(graph.nodes.map(node => [node.id, node]));
  return <svg className="graph" viewBox="0 0 100 100" aria-label={`Bounded graph for ${active.title}`} role="img">
    <defs><pattern id="ticks" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeOpacity=".12" strokeWidth=".25" /></pattern></defs>
    <rect width="100" height="100" fill="url(#ticks)" />
    {graph.edges.map((edge, index) => <line key={index} x1={lookup[edge.source].x} y1={lookup[edge.source].y} x2={lookup[edge.target].x} y2={lookup[edge.target].y} className="edge" />)}
    {graph.nodes.map(node => <g key={node.id} tabIndex={0} role="button" aria-label={`Inspect ${node.label}`} className={`node ${node.kind} ${selectedNode === node.label ? "node-selected" : ""}`} onClick={() => onNodeSelect(node.label)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onNodeSelect(node.label); } }}><circle cx={node.x} cy={node.y} r={node.kind === "focus" ? 4.7 : 3.2} /><text x={node.x} y={node.y + 7}>{node.label}</text></g>)}
  </svg>;
}

function App() {
  const [brief, setBrief] = useState<Brief | null>(null); const [queue, setQueue] = useState<Case[]>([]); const [active, setActive] = useState<Case | null>(null); const [graph, setGraph] = useState<Graph | null>(null); const [error, setError] = useState(""); const [graphError, setGraphError] = useState(""); const [nodeLabel, setNodeLabel] = useState(""); const [reloadGraph, setReloadGraph] = useState(0);
  useEffect(() => { Promise.all([api<Brief>("/brief"), api<{items:Case[]}>("/queue?limit=6")]).then(([b,q]) => { setBrief(b); setQueue(q.items); setActive(q.items[0] ?? null); }).catch(e => setError(e.message)); }, []);
  useEffect(() => { if (!active) return; const controller = new AbortController(); setGraph(null); setGraphError(""); fetch(`/api/graph/${active.id}?depth=2`, {signal:controller.signal}).then(response => { if (!response.ok) throw new Error("The bounded topology could not be loaded."); return response.json() as Promise<Graph>; }).then(value => { setGraph(value); setNodeLabel(value.nodes[0]?.label ?? ""); }).catch(e => { if (e.name !== "AbortError") setGraphError(e.message); }); return () => controller.abort(); }, [active, reloadGraph]);
  if (error) return <main className="state"><p className="stamp">PUBLIC FIXTURE</p><h1>Evidence desk unavailable.</h1><p>{error}</p><button onClick={() => location.reload()}>Retry casefile</button></main>;
  if (!brief) return <main className="state"><p className="stamp">SIGNAL LEDGER</p><h1>Opening the synthetic casefile…</h1><p>Loading precomputed evidence; no model is running in your browser.</p></main>;
  if (!active) return <main className="state"><p className="stamp">PUBLIC FIXTURE</p><h1>No synthetic cases are available.</h1><p>The bounded casefile returned an empty queue. Refresh to retry the public fixture.</p><button onClick={() => location.reload()}>Retry casefile</button></main>;
  return <main>
    <header className="masthead"><div><p className="stamp">{brief.brief.mode}</p><h1>{brief.brief.title}</h1></div><div className="mast-meta"><span className="live-dot" />{brief.brief.updated}</div></header>
    <section className="opening"><div><p className="lede">{brief.brief.subtitle}</p><p className="disclaimer">{brief.brief.disclaimer}</p></div><aside><span>Method boundary</span><strong>Score → inspect → contextualize</strong><small>Never automate a conclusion.</small></aside></section>
    <div className="workbench">
      <nav className="queue" aria-label="Research-ranked synthetic queue"><div className="section-line"><span>Research queue</span><b>{queue.length} illustrated cases</b></div>{queue.map(item => <button key={item.id} className={`case-row ${active.id === item.id ? "selected" : ""}`} onClick={() => setActive(item)}><span className="case-score">{item.score.toFixed(2)}</span><span className="case-copy"><strong>{item.title}</strong><small>{item.time} · {item.band}</small></span><span className="case-status">{item.status}</span></button>)}</nav>
      <section className="investigation" aria-live="polite"><div className="section-line"><span>Bounded topology</span><b>Depth 2 maximum</b></div><div className="graph-wrap"><GraphView graph={graph} active={active} selectedNode={nodeLabel} onNodeSelect={setNodeLabel} error={graphError} retry={() => setReloadGraph(value => value + 1)} /><div className="graph-legend"><i className="focus" /> focus <i className="origin" /> origin / relay <i className="exit" /> exit</div></div><div className="case-summary"><div><p className="stamp">Selected case · {active.id}</p><h2>{active.title}</h2><p>{active.reason} {nodeLabel && `Graph focus: ${nodeLabel}.`}</p></div><div className="score-block"><span>Research rank</span><strong>{active.score.toFixed(2)}</strong><small>{active.band}</small></div></div></section>
      <aside className="evidence"><div className="section-line"><span>Investigation brief</span><b>Illustrative</b></div><h2>What to examine</h2><ul className="signal-list">{active.signals.map(signal => <li key={signal}>{signal}</li>)}</ul><h3>Evidence in this fixture</h3><ul>{active.evidence.map(item => <li key={item}>{item}</li>)}</ul><p className="callout">{active.note}</p></aside>
    </div>
    <section className="method"><div><p className="stamp">Model & evaluation evidence</p><h2>Visible limits are part of the workbench.</h2><p>This public surface intentionally shows no benchmark metric as a product claim. The fixture exists to make the investigation interaction inspectable without exposing research data.</p></div><dl><div><dt>Fixture provenance</dt><dd>{brief.evidence.fixture}</dd></div><div><dt>Source</dt><dd>{brief.evidence.source}</dd></div><div><dt>Access boundary</dt><dd>{brief.evidence.access}</dd></div><div><dt>Evaluation status</dt><dd>{brief.evidence.evaluation}</dd></div></dl></section>
    <footer><div><p className="stamp">Governance notes</p>{brief.governance.map(note => <p key={note}>{note}</p>)}</div><div><p className="stamp">Known limitations</p>{brief.evidence.limitations.map(limit => <p key={limit}>{limit}</p>)}</div></footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<App />);
