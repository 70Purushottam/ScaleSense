"""Rule engine. Each finding carries a retrieval_query used by the RAG layer (week 4)."""
from .schema import Graph
from . import analyzer, capacity

SYNC_CHAIN_LIMIT = 3   # max service hops in one synchronous call path
UTIL_WARN, UTIL_CRIT = 0.8, 1.0


def f(rule, severity, nodes, message, query):
    return {"rule": rule, "severity": severity, "nodes": nodes,
            "message": message, "retrieval_query": query}


def rule_spof(g):
    for s in analyzer.single_points_of_failure(g):
        yield f("single_point_of_failure", "high", [s["node"]],
                f"'{s['node']}' has one replica; its failure cuts clients off from {s['cuts_off']}.",
                "how to remove single point of failure with replication and failover")


def rule_saturation(g):
    for u in capacity.utilization(g):
        if u["utilization"] >= UTIL_CRIT:
            yield f("saturation", "high", [u["node"]],
                    f"'{u['node']}' is overloaded: {u['incoming_qps']} QPS vs {u['capacity_qps']} capacity.",
                    "scaling a bottleneck component under overload, backpressure and load shedding")
        elif u["utilization"] >= UTIL_WARN:
            yield f("near_saturation", "medium", [u["node"]],
                    f"'{u['node']}' is at {u['utilization']:.0%} utilization; latency rises sharply near capacity.",
                    "latency growth near saturation queueing")


def rule_long_sync_chain(g):
    types = {n.id: n.type for n in g.nodes}
    path = analyzer.longest_sync_path(g)
    hops = [v for v in path if types[v] == "service"]
    if len(hops) > SYNC_CHAIN_LIMIT:
        yield f("long_sync_chain", "medium", path,
                f"Synchronous chain through {len(hops)} services: latency adds up and availability multiplies down.",
                "long synchronous call chains latency availability microservices")


def rule_cycle(g):
    for comp in analyzer.cyclic_sccs(g):
        yield f("cycle", "medium", sorted(comp),
                f"Cycle among {sorted(comp)}: retries or feedback can amplify load.",
                "retry storms and cascading failures in cyclic service dependencies")


def rule_unbuffered_db(g):
    has_buffer = any(n.type in ("cache", "queue") for n in g.nodes)
    types = {n.id: n.type for n in g.nodes}
    for n in g.nodes:
        if n.type != "database":
            continue
        direct = [e for e in g.edges if e.target == n.id and e.kind == "sync" and types[e.source] == "service"]
        if direct and not has_buffer:
            yield f("unbuffered_database", "medium", [n.id],
                    f"'{n.id}' takes synchronous traffic from services with no cache or queue in the design.",
                    "database connection pool exhaustion without cache or message queue")


def rule_orphans(g):
    touched = {e.source for e in g.edges} | {e.target for e in g.edges}
    for n in g.nodes:
        if n.id not in touched:
            yield f("disconnected_node", "low", [n.id], f"'{n.id}' is not connected to anything.", "")


def rule_queue_without_consumer(g):
    has_out = {e.source for e in g.edges}
    for n in g.nodes:
        if n.type == "queue" and n.id not in has_out:
            yield f("queue_without_consumer", "medium", [n.id],
                    f"Queue '{n.id}' has no consumer; messages will pile up unbounded.",
                    "message queue consumer lag and unbounded backlog growth")


def rule_high_fanout(g):
    for e in g.edges:
        if e.fanout > 5:
            yield f("high_fanout", "medium", [e.source, e.target],
                    f"Each request to '{e.source}' triggers {e.fanout:g} calls to '{e.target}'; load is amplified.",
                    "request amplification fan-out and batching to reduce downstream load")


RULES = [rule_queue_without_consumer, rule_high_fanout, rule_spof, rule_saturation,
         rule_long_sync_chain, rule_cycle, rule_unbuffered_db, rule_orphans]


def run_all(g: Graph) -> list[dict]:
    return [x for r in RULES for x in r(g)]