import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import { NODE_TYPES, makeCfg, toGraph, SEED_NODES, SEED_EDGES } from "./graph.js";
import * as api from "./api.js";
import Inspector from "./components/Inspector.jsx";
import { Findings, FailureResult, RampResult, Explain } from "./components/Results.jsx";

const SEV_COLOR = { high: "#d92d20", medium: "#f79009", low: "#98a2b3" };
const RANK = { high: 3, medium: 2, low: 1 };

const withArrow = (e) => ({ ...e, markerEnd: { type: MarkerType.ArrowClosed } });

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(SEED_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(SEED_EDGES.map(withArrow));
  const [selected, setSelected] = useState(null);
  const [auditRes, setAuditRes] = useState(null);
  const [failRes, setFailRes] = useState(null);
  const [rampRes, setRampRes] = useState(null);
  const [explainRes, setExplainRes] = useState(null);
  const [lost, setLost] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("theme");
      if (saved) return saved;
    } catch {}
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {}
  }, [theme]);

  // Worst severity per node, used to color node borders after an audit.
  const worstByNode = useMemo(() => {
    const m = {};
    (auditRes?.findings || []).forEach((f) =>
      f.nodes.forEach((id) => {
        if (!m[id] || RANK[f.severity] > RANK[m[id]]) m[id] = f.severity;
      })
    );
    return m;
  }, [auditRes]);

  // Nodes as displayed: label text and border color derived from config + audit.
  const shownNodes = useMemo(
    () =>
      nodes.map((n) => {
        const c = n.data.cfg;
        const sev = worstByNode[n.id];
        const body = c.type === "client" ? `${c.qps} QPS` : `×${c.replicas}`;
        return {
          ...n,
          data: { ...n.data, label: `${c.label || n.id} · ${c.type}\n${body}` },
          style: {
            whiteSpace: "pre-line",
            textAlign: "center",
            borderRadius: 8,
            border: `2px solid ${sev ? SEV_COLOR[sev] : "var(--node-border)"}`,
            background: "var(--node-bg)",
            color: "var(--text)",
            fontSize: 12,
            width: 150,
          },
        };
      }),
    [nodes, worstByNode]
  );

  const onConnect = useCallback(
    (conn) =>
      setEdges((es) =>
        addEdge(
          withArrow({ ...conn, id: `e${Date.now()}`, data: { kind: "sync", fanout: 1 } }),
          es
        )
      ),
    [setEdges]
  );

  const addNode = (type) => {
    let i = 1;
    while (nodes.some((n) => n.id === `${type}${i}`)) i++;
    const id = `${type}${i}`;
    setNodes((ns) => [
      ...ns,
      {
        id,
        position: { x: 80 + ns.length * 20, y: 260 + (ns.length % 4) * 30 },
        data: { cfg: makeCfg(type) },
      },
    ]);
  };

  const patchNode = (id, patch) =>
    setNodes((ns) =>
      ns.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, cfg: { ...n.data.cfg, ...patch } } } : n
      )
    );

  const patchEdge = (id, patch) =>
    setEdges((es) =>
      es.map((e) => (e.id === id ? { ...e, data: { ...e.data, ...patch } } : e))
    );

  const deleteSelected = () => {
    if (!selected) return;
    if (selected.kind === "node") {
      setNodes((ns) => ns.filter((n) => n.id !== selected.id));
      setEdges((es) => es.filter((e) => e.source !== selected.id && e.target !== selected.id));
    } else {
      setEdges((es) => es.filter((e) => e.id !== selected.id));
    }
    setSelected(null);
  };

  const run = async (fn) => {
    setBusy(true);
    setError("");
    try {
      await fn(toGraph(nodes, edges));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const doAudit = () => run(async (g) => setAuditRes(await api.audit(g)));
  const doRamp = () => run(async (g) => setRampRes(await api.simulateRamp(g)));
  const doExplain = () => run(async (g) => setExplainRes(await api.explain(g)));
  const doFailure = () => {
    if (selected?.kind !== "node") return setError("Select a node to fail first.");
    const n = lost.trim() === "" ? null : Math.max(1, parseInt(lost, 10) || 1);
    run(async (g) =>
      setFailRes(await api.simulateFailure(g, [{ node: selected.id, replicas_lost: n }]))
    );
  };

  return (
    <div className="app">
      <header>
        <h1>ScaleSense</h1>
        <div className="palette">
          {NODE_TYPES.map((t) => (
            <button key={t} onClick={() => addNode(t)}>
              + {t}
            </button>
          ))}
        </div>
        <div className="actions">
          <button className="primary" disabled={busy} onClick={doAudit}>
            Audit
          </button>
          <button disabled={busy} onClick={doRamp}>
            Load ramp
          </button>
          <button disabled={busy} onClick={doExplain}>
            Explain
          </button>
          <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
        </div>
      </header>

      <main>
        <div className="canvas">
          <ReactFlow
            nodes={shownNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, n) => setSelected({ kind: "node", id: n.id })}
            onEdgeClick={(_, e) => setSelected({ kind: "edge", id: e.id })}
            onPaneClick={() => setSelected(null)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap pannable zoomable />
          </ReactFlow>
        </div>

        <aside>
          {error && <div className="error">{error}</div>}

          <section>
            <Inspector
              selected={selected}
              nodes={nodes}
              edges={edges}
              onNodeChange={patchNode}
              onEdgeChange={patchEdge}
              onDelete={deleteSelected}
            />
          </section>

          <section>
            <h3>Failure injection</h3>
            <p className="muted">
              Select a node, then choose how many replicas to lose (blank = whole node).
            </p>
            <div className="row">
              <input
                type="number"
                min="1"
                placeholder="all"
                value={lost}
                onChange={(e) => setLost(e.target.value)}
              />
              <button className="danger" disabled={busy} onClick={doFailure}>
                Fail {selected?.kind === "node" ? selected.id : "…"}
              </button>
            </div>
            <FailureResult result={failRes} />
          </section>

          <section>
            <RampResult result={rampRes} />
          </section>

          <section>
            <Findings result={auditRes} />
          </section>

          <section>
            <Explain result={explainRes} />
          </section>
        </aside>
      </main>
    </div>
  );
}