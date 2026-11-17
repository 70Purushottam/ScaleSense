const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(
      typeof d === "string" ? d : d ? JSON.stringify(d) : res.statusText
    );
  }
  return data;
}

export const audit = (graph) => post("/audit", graph);

export const simulateFailure = (graph, failures) =>
  post("/simulate/failure", { graph, failures });

export const simulateRamp = (graph) => post("/simulate/ramp", graph);
export const explain = (graph) => post("/audit/explain", graph);