"""Predict the stack's limits with the simulator. Run from the project root:
python scripts/predict.py --api-qps 350 --replicas 2 --load 500
"""
import argparse, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
from app.schema import Graph
from app import simulate

ap = argparse.ArgumentParser()
ap.add_argument("--api-qps", type=float, required=True, help="measured capacity of ONE api replica")
ap.add_argument("--replicas", type=int, default=2)
ap.add_argument("--load", type=float, default=500, help="client QPS for the failure scenario")
ap.add_argument("--hit-rate", type=float, default=1.0, help="1.0 matches HOT_RATIO=1")
ap.add_argument("--db-qps", type=float, default=2000, help="rough Postgres capacity")
ap.add_argument("--redis-qps", type=float, default=20000, help="rough Redis capacity")
a = ap.parse_args()

g = Graph(
    nodes=[
        {"id": "users", "type": "client", "qps": a.load},
        {"id": "nginx", "type": "load_balancer", "capacity_qps": 10000},
        {"id": "api", "type": "service", "replicas": a.replicas, "capacity_qps": a.api_qps},
        {"id": "cache", "type": "cache", "capacity_qps": a.redis_qps, "hit_rate": a.hit_rate},
        {"id": "db", "type": "database", "capacity_qps": a.db_qps},
    ],
    edges=[
        {"source": "users", "target": "nginx"},
        {"source": "nginx", "target": "api"},
        {"source": "api", "target": "cache"},
        {"source": "cache", "target": "db"},
    ],
)

r = simulate.ramp(g)
print(f"[{a.replicas} replicas, hit_rate={a.hit_rate}]")
print(f"  bottleneck: {r['bottleneck']}")
print(f"  predicted max sustainable QPS: {r['max_sustainable_qps']}")

if a.replicas > 1:
    f = simulate.failure_report(g, {"api": 1})
    api = next(u for u in f["utilization_after"] if u["node"] == "api")
    print(f"[lose 1 api replica at {a.load:g} QPS]")
    print(f"  api utilization after: {api['utilization']:.0%}")
    print(f"  newly overloaded: {f['newly_overloaded']}  service_available: {f['service_available']}")