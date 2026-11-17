const NUM_FIELDS = [
  ["replicas", "Replicas", 1, 1],
  ["capacity_qps", "Capacity QPS / replica", 1, 100],
  ["latency_ms", "Latency (ms)", 0, 1],
];

export default function Inspector({
  selected,
  nodes,
  edges,
  onNodeChange,
  onEdgeChange,
  onDelete,
}) {
  if (!selected) {
    return <p className="muted">Select a node or edge to edit it.</p>;
  }

  if (selected.kind === "node") {
    const node = nodes.find((n) => n.id === selected.id);
    if (!node) return null;
    const c = node.data.cfg;

    return (
      <div className="inspector">
        <h3>
          {node.id} <span className="tag">{c.type}</span>
        </h3>

        <label>
          Label
          <input
            value={c.label}
            onChange={(e) => onNodeChange(node.id, { label: e.target.value })}
          />
        </label>

        {c.type === "client" ? (
          <label>
            Traffic QPS
            <input
              type="number"
              min="0"
              value={c.qps}
              onChange={(e) => onNodeChange(node.id, { qps: e.target.value })}
            />
          </label>
        ) : (
          NUM_FIELDS.map(([k, name, min, step]) => (
            <label key={k}>
              {name}
              <input
                type="number"
                min={min}
                step={step}
                value={c[k]}
                onChange={(e) => onNodeChange(node.id, { [k]: e.target.value })}
              />
            </label>
          ))
        )}

        {(c.type === "cache" || c.type === "cdn") && (
          <label>
            Hit rate (0–1)
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={c.hit_rate}
              onChange={(e) => onNodeChange(node.id, { hit_rate: e.target.value })}
            />
          </label>
        )}

        <button className="danger" onClick={onDelete}>
          Delete node
        </button>
      </div>
    );
  }

  const edge = edges.find((e) => e.id === selected.id);
  if (!edge) return null;
  const d = edge.data || {};

  return (
    <div className="inspector">
      <h3>
        {edge.source} → {edge.target}
      </h3>

      <label>
        Kind
        <select
          value={d.kind || "sync"}
          onChange={(e) => onEdgeChange(edge.id, { kind: e.target.value })}
        >
          <option value="sync">sync</option>
          <option value="async">async</option>
        </select>
      </label>

      <label>
        Fanout (calls per request)
        <input
          type="number"
          min="0.1"
          step="0.5"
          value={d.fanout ?? 1}
          onChange={(e) => onEdgeChange(edge.id, { fanout: e.target.value })}
        />
      </label>

      <button className="danger" onClick={onDelete}>
        Delete edge
      </button>
    </div>
  );
}