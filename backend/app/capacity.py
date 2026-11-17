"""Analytical capacity model: propagate QPS through the graph, compute utilization.
Assumptions: steady state, independent requests, LBs split evenly, caches forward only
misses, edges inside a cycle are ignored (and flagged by the rules)."""
from collections import defaultdict, deque
from .schema import Graph
from .analyzer import tarjan_scc


def propagate(g: Graph) -> dict[str, float]:
    comp_of = {}
    for i, comp in enumerate(tarjan_scc(g)):
        for v in comp:
            comp_of[v] = i
    nodes = {n.id: n for n in g.nodes}
    out_edges = defaultdict(list)
    indeg = {n.id: 0 for n in g.nodes}
    for e in g.edges:
        if comp_of[e.source] == comp_of[e.target]:
            continue
        out_edges[e.source].append(e)
        indeg[e.target] += 1

    incoming = {n.id: (n.qps if n.type == "client" else 0.0) for n in g.nodes}
    q = deque(v for v, d in indeg.items() if d == 0)
    while q:
        v = q.popleft()
        node = nodes[v]
        forwarded = incoming[v]
        if node.type in ("cache", "cdn"):
            forwarded *= 1 - node.hit_rate
        edges = out_edges[v]
        for e in edges:
            share = forwarded / len(edges) if node.type == "load_balancer" else forwarded
            incoming[e.target] += share * e.fanout
            indeg[e.target] -= 1
            if indeg[e.target] == 0:
                q.append(e.target)
    return incoming


def utilization(g: Graph) -> list[dict]:
    load = propagate(g)
    rows = []
    for n in g.nodes:
        if n.type == "client":
            continue
        cap = n.replicas * n.capacity_qps
        rows.append({
            "node": n.id,
            "incoming_qps": round(load[n.id], 2),
            "capacity_qps": cap,
            "utilization": round(load[n.id] / cap, 3),
            "concurrency_needed": round(load[n.id] * n.latency_ms / 1000, 2),  # Little's Law
        })
    return rows