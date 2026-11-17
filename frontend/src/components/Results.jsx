const pct = (x) => `${Math.round(x * 100)}%`;

export function UtilTable({ rows }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Node</th>
          <th>QPS in</th>
          <th>Capacity</th>
          <th>Util</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr
            key={r.node}
            className={r.utilization >= 1 ? "bad" : r.utilization >= 0.8 ? "warn" : ""}
          >
            <td>{r.node}</td>
            <td>{r.incoming_qps}</td>
            <td>{r.capacity_qps}</td>
            <td>{pct(r.utilization)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function Findings({ result }) {
  if (!result) return <p className="muted">Run “Audit” to see findings.</p>;
  const { findings, load } = result;

  return (
    <div>
      <h3>Findings ({findings.length})</h3>
      {findings.length === 0 && <p className="ok">No issues found.</p>}
      {findings.map((f, i) => (
        <div key={i} className={`finding sev-${f.severity}`}>
          <b>{f.rule}</b> <span className="tag">{f.severity}</span>
          <div>{f.message}</div>
        </div>
      ))}
      <h3>Utilization</h3>
      <UtilTable rows={load} />
    </div>
  );
}

export function FailureResult({ result }) {
  if (!result) return null;

  return (
    <div>
      <h3>Failure result</h3>
      <p className={result.service_available ? "ok" : "bad-text"}>
        Service {result.service_available ? "still available" : "UNAVAILABLE"}
      </p>
      {result.data_stores_lost.length > 0 && (
        <p>
          Data stores cut off: <b>{result.data_stores_lost.join(", ")}</b>
        </p>
      )}
      {result.newly_overloaded.length > 0 && (
        <p>
          Newly overloaded: <b>{result.newly_overloaded.join(", ")}</b>
        </p>
      )}
      <UtilTable rows={result.utilization_after} />
    </div>
  );
}

export function RampResult({ result }) {
  if (!result) return null;
  const maxU = Math.max(...result.curve.map((c) => c.max_utilization), 1);

  return (
    <div>
      <h3>Load ramp</h3>
      <p>
        Bottleneck: <b>{result.bottleneck}</b> · max sustainable ≈{" "}
        <b>{result.max_sustainable_qps}</b> QPS (current {result.current_qps})
      </p>
      {result.curve.map((c) => (
        <div key={c.multiplier} className="bar-row">
          <span className="bar-label">
            {c.multiplier}× ({c.total_qps})
          </span>
          <div className="bar-track">
            <div
              className={`bar ${
                c.max_utilization >= 1
                  ? "bar-bad"
                  : c.max_utilization >= 0.8
                  ? "bar-warn"
                  : ""
              }`}
              style={{ width: `${Math.min(100, (c.max_utilization / maxU) * 100)}%` }}
            />
          </div>
          <span className="bar-val">
            {pct(c.max_utilization)} · {c.node}
          </span>
        </div>
      ))}
      <p className="muted">
        Predicted by an analytical model: it ignores queueing, retries and cache warm-up.
      </p>
    </div>
  );
}

export function Explain({ result }) {
  if (!result) return null;
  const { findings } = result;

  return (
    <div>
      <h3>Explanations ({findings.length})</h3>
      {findings.length === 0 && <p className="ok">Nothing to explain.</p>}
      {findings.map((f, i) => (
        <div key={i} className={`finding sev-${f.severity}`}>
          <b>{f.rule}</b> <span className="tag">{f.severity}</span>
          <div>{f.message}</div>
          {f.evidence.length === 0 && <p className="muted">No reference found.</p>}
          {f.evidence.map((e) => (
            <blockquote key={e.id} className="evidence">
              <div className="muted">
                {e.title} · <code>{e.id}</code> {f.verified ? "· verified" : "· NOT verified"}
              </div>
              {e.text}
            </blockquote>
          ))}
        </div>
      ))}
    </div>
  );
}