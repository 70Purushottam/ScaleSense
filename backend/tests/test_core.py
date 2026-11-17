import json, pathlib, pytest
from app.schema import Graph, Node, Edge
from app import analyzer, capacity, rules

EX = pathlib.Path(__file__).parents[2] / "examples" / "three_tier.json"


def load():
    return Graph(**json.loads(EX.read_text()))


def test_no_cycle_in_three_tier():
    assert analyzer.cyclic_sccs(load()) == []


def test_detects_cycle():
    g = load()
    g.edges.append(Edge(source="db", target="api"))
    assert any(set(c) == {"api", "db"} for c in analyzer.cyclic_sccs(g))


def test_spof_found():
    nodes = {s["node"] for s in analyzer.single_points_of_failure(load())}
    assert {"lb", "db"} <= nodes and "api" not in nodes


def test_load_propagation():
    m = capacity.propagate(load())
    assert m["api"] == 2000 and m["db"] == 2000


def test_utilization_and_littles_law():
    rows = {r["node"]: r for r in capacity.utilization(load())}
    assert rows["api"]["utilization"] == 2.0
    assert rows["api"]["concurrency_needed"] == 80.0   # 2000 qps * 0.040 s


def test_cache_cuts_db_load():
    g = load()
    g.nodes.append(Node(id="cache", type="cache", hit_rate=0.9, replicas=2))
    g.edges = [e for e in g.edges if e.target != "db"]
    g.edges += [Edge(source="api", target="cache"), Edge(source="cache", target="db")]
    assert capacity.propagate(g)["db"] == pytest.approx(200)


def test_rules_flag_expected():
    kinds = {f["rule"] for f in rules.run_all(load())}
    assert {"single_point_of_failure", "saturation", "unbuffered_database"} <= kinds