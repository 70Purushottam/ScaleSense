"""What-if simulation: failure injection and load ramp. Uses the same analytical model as capacity.py."""
from .schema import Graph
from . import analyzer, capacity


def apply_failure(g: Graph, failures: dict[str, int | None]) -> Graph:
    """failures maps node id -> replicas lost (None = all). Nodes with no replicas left are removed."""
    known = {n.id: n for n in g.nodes}
    for nid in failures:
        if nid not in known:
            raise ValueError(f"unknown node: {nid}")
        if known[nid].type == "client":
            raise ValueError("cannot fail a client node")
    g2 = g.model_copy(deep=True)
    dead = set()
    for n in g2.nodes:
        if n.id in failures:
            lost = failures[n.id]
            left = 0 if lost is None else n.replicas - lost
            if left <= 0:
                dead.add(n.id)
            else:
                n.replicas = left
    g2.nodes = [n for n in g2.nodes if n.id not in dead]
    g2.edges = [e for e in g2.edges if e.source not in dead and e.target not in dead]
    return g2


def _stores_reachable(g: Graph) -> set[str]:
    clients = [n.id for n in g.nodes if n.type == "client"]
    stores = {n.id for n in g.nodes if n.type == "database"}
    return analyzer.reachable(analyzer.adjacency(g), clients) & stores


def failure_report(g: Graph, failures: dict[str, int | None]) -> dict:
    before = {r["node"]: r for r in capacity.utilization(g)}
    g2 = apply_failure(g, failures)
    after = {r["node"]: r for r in capacity.utilization(g2)}
    stores_before, stores_after = _stores_reachable(g), _stores_reachable(g2)
    newly_overloaded = sorted(
        n for n, r in after.items()
        if r["utilization"] >= 1.0 and before.get(n, {"utilization": 0})["utilization"] < 1.0)
    return {
        "failed": {k: ("all" if v is None else v) for k, v in failures.items()},
        "data_stores_lost": sorted(stores_before - stores_after),
        "newly_overloaded": newly_overloaded,
        "utilization_after": list(after.values()),
        "service_available": bool(stores_after) or not stores_before,
    }


def ramp(g: Graph, multipliers=(0.5, 1, 1.5, 2, 3, 5)) -> dict:
    """Capacity is linear in client QPS here, so headroom per node = capacity / load."""
    sources = {e.source for e in g.edges}
    total = sum(n.qps for n in g.nodes if n.type == "client" and n.id in sources)
    if total <= 0:
        raise ValueError("no client traffic to ramp")
    rows = [r for r in capacity.utilization(g) if r["incoming_qps"] > 0]
    ranked = sorted(({"node": r["node"], "headroom": round(r["capacity_qps"] / r["incoming_qps"], 3)}
                     for r in rows), key=lambda x: x["headroom"])
    bottleneck = ranked[0]
    curve = []
    for m in multipliers:
        worst = max(rows, key=lambda r: r["utilization"])
        curve.append({"multiplier": m, "total_qps": total * m,
                      "max_utilization": round(worst["utilization"] * m, 3), "node": worst["node"]})
    return {"current_qps": total, "bottleneck": bottleneck["node"],
            "max_sustainable_qps": round(total * bottleneck["headroom"], 1),
            "ranking": ranked, "curve": curve}