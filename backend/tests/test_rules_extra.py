from app.schema import Graph
from app import rules


def kinds(d):
    return {f["rule"] for f in rules.run_all(Graph(**d))}


def test_queue_without_consumer():
    d = {"nodes": [{"id": "u", "type": "client", "qps": 10}, {"id": "q", "type": "queue", "replicas": 2}],
         "edges": [{"source": "u", "target": "q"}]}
    assert "queue_without_consumer" in kinds(d)


def test_queue_with_consumer_ok():
    d = {"nodes": [{"id": "u", "type": "client", "qps": 10}, {"id": "q", "type": "queue", "replicas": 2},
                   {"id": "w", "type": "service", "replicas": 2}],
         "edges": [{"source": "u", "target": "q"}, {"source": "q", "target": "w"}]}
    assert "queue_without_consumer" not in kinds(d)


def test_high_fanout():
    d = {"nodes": [{"id": "u", "type": "client", "qps": 10}, {"id": "a", "type": "service", "replicas": 2}],
         "edges": [{"source": "u", "target": "a", "fanout": 8}]}
    assert "high_fanout" in kinds(d)


def test_infra_hops_do_not_count_as_long_chain():
    d = {"nodes": [{"id": "u", "type": "client", "qps": 10}, {"id": "lb", "type": "load_balancer", "replicas": 2},
                   {"id": "a", "type": "service", "replicas": 2}, {"id": "c", "type": "cache", "replicas": 2},
                   {"id": "db", "type": "database", "replicas": 2}],
         "edges": [{"source": "u", "target": "lb"}, {"source": "lb", "target": "a"},
                   {"source": "a", "target": "c"}, {"source": "c", "target": "db"}]}
    assert "long_sync_chain" not in kinds(d)