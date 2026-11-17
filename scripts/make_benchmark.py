import json, pathlib

OUT = pathlib.Path("examples/benchmark")
OUT.mkdir(parents=True, exist_ok=True)


def N(id, t, **k): return {"id": id, "type": t, **k}
def E(a, b, **k): return {"source": a, "target": b, **k}
def tail(): return [N("cache", "cache", replicas=2, hit_rate=0.9),
                    N("db", "database", replicas=2, capacity_qps=800)]


cases = {
 "b01_single_lb": (["single_point_of_failure:lb", "unbuffered_database:db"],
  [N("u", "client", qps=500), N("lb", "load_balancer"),
   N("api", "service", replicas=3, capacity_qps=500), N("db", "database", replicas=2, capacity_qps=800)],
  [E("u", "lb"), E("lb", "api"), E("api", "db")]),
 "b02_overloaded_db": (["saturation:db", "unbuffered_database:db"],
  [N("u", "client", qps=3000), N("lb", "load_balancer", replicas=2, capacity_qps=10000),
   N("api", "service", replicas=4, capacity_qps=1000), N("db", "database", replicas=2, capacity_qps=800)],
  [E("u", "lb"), E("lb", "api"), E("api", "db")]),
 "b03_clean": ([],
  [N("u", "client", qps=1000), N("lb", "load_balancer", replicas=2),
   N("api", "service", replicas=3, capacity_qps=500)] + tail(),
  [E("u", "lb"), E("lb", "api"), E("api", "cache"), E("cache", "db")]),
 "b04_long_chain": (["long_sync_chain"],
  [N("u", "client", qps=100)] + [N(x, "service", replicas=2) for x in ["gw", "a", "b", "c", "d"]] + tail(),
  [E("u", "gw"), E("gw", "a"), E("a", "b"), E("b", "c"), E("c", "d"), E("d", "cache"), E("cache", "db")]),
 "b05_cycle": (["cycle"],
  [N("u", "client", qps=200), N("api", "service", replicas=2), N("pay", "service", replicas=2)] + tail(),
  [E("u", "api"), E("api", "pay"), E("pay", "api"), E("api", "cache"), E("cache", "db")]),
 "b06_dead_queue": (["queue_without_consumer:q"],
  [N("u", "client", qps=200), N("api", "service", replicas=2), N("q", "queue", replicas=2)] + tail(),
  [E("u", "api"), E("api", "q"), E("api", "cache"), E("cache", "db")]),
 "b07_orphan": (["disconnected_node:logger"],
  [N("u", "client", qps=500), N("api", "service", replicas=3, capacity_qps=500),
   N("logger", "service", replicas=2)] + tail(),
  [E("u", "api"), E("api", "cache"), E("cache", "db")]),
}
for name, (expected, nodes, edges) in cases.items():
    (OUT / f"{name}.json").write_text(json.dumps(
        {"graph": {"nodes": nodes, "edges": edges}, "expected_findings": expected}, indent=1))
print(f"wrote {len(cases)} cases")