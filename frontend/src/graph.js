export const NODE_TYPES = [
  "client",
  "load_balancer",
  "service",
  "cache",
  "database",
  "queue",
  "cdn",
];

export const DEFAULTS = {
  client: { qps: 1000 },
  load_balancer: { replicas: 2, capacity_qps: 10000, latency_ms: 2 },
  service: { replicas: 2, capacity_qps: 500, latency_ms: 40 },
  cache: { replicas: 2, capacity_qps: 20000, latency_ms: 1, hit_rate: 0.9 },
  database: { replicas: 2, capacity_qps: 800, latency_ms: 8 },
  queue: { replicas: 2, capacity_qps: 5000, latency_ms: 5 },
  cdn: { replicas: 2, capacity_qps: 50000, latency_ms: 5, hit_rate: 0.8 },
};

export function makeCfg(type, extra = {}) {
  return {
    type,
    label: "",
    replicas: 1,
    capacity_qps: 1000,
    latency_ms: 10,
    hit_rate: 0,
    qps: 0,
    ...DEFAULTS[type],
    ...extra,
  };
}

// Convert React Flow state into the payload the backend's Graph schema expects.
// Values are clamped so empty or invalid inputs never cause a 422.
export function toGraph(nodes, edges) {
  return {
    nodes: nodes.map((n) => {
      const c = n.data.cfg;
      return {
        id: n.id,
        type: c.type,
        label: c.label || "",
        replicas: Math.max(1, Math.round(Number(c.replicas) || 1)),
        capacity_qps: Number(c.capacity_qps) > 0 ? Number(c.capacity_qps) : 1,
        latency_ms: Math.max(0, Number(c.latency_ms) || 0),
        hit_rate: Math.min(1, Math.max(0, Number(c.hit_rate) || 0)),
        qps: Math.max(0, Number(c.qps) || 0),
      };
    }),
    edges: edges.map((e) => ({
      source: e.source,
      target: e.target,
      kind: e.data?.kind || "sync",
      fanout: Number(e.data?.fanout) > 0 ? Number(e.data.fanout) : 1,
    })),
  };
}

// Starting canvas: the three-tier example.
export const SEED_NODES = [
  { id: "users", position: { x: 0, y: 120 }, data: { cfg: makeCfg("client", { qps: 2000 }) } },
  { id: "lb", position: { x: 220, y: 120 }, data: { cfg: makeCfg("load_balancer", { replicas: 1 }) } },
  { id: "api", position: { x: 440, y: 120 }, data: { cfg: makeCfg("service", { replicas: 2 }) } },
  { id: "db", position: { x: 660, y: 120 }, data: { cfg: makeCfg("database", { replicas: 1 }) } },
];

export const SEED_EDGES = [
  { id: "e1", source: "users", target: "lb", data: { kind: "sync", fanout: 1 } },
  { id: "e2", source: "lb", target: "api", data: { kind: "sync", fanout: 1 } },
  { id: "e3", source: "api", target: "db", data: { kind: "sync", fanout: 1 } },
];