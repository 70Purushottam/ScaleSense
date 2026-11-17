"""Hit@k of the retrieval layer on the queries the rule engine emits. Run: python scripts/eval_retrieval.py"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
from app import retrieval

CASES = [  # (retrieval_query used in rules.py, expected knowledge-base file)
    ("how to remove single point of failure with replication and failover", "single-point-of-failure"),
    ("scaling a bottleneck component under overload, backpressure and load shedding", "saturation-and-queueing"),
    ("latency growth near saturation queueing", "saturation-and-queueing"),
    ("long synchronous call chains latency availability microservices", "sync-call-chains"),
    ("retry storms and cascading failures in cyclic service dependencies", "retry-storms-cycles"),
    ("database connection pool exhaustion without cache or message queue", "database-load"),
    ("message queue consumer lag and unbounded backlog growth", "message-queues"),
    ("request amplification fan-out and batching to reduce downstream load", "fanout-amplification"),
    # paraphrases, to avoid grading only on the exact query strings
    ("what happens when my only load balancer dies", "single-point-of-failure"),
    ("why does latency explode at 90 percent cpu", "saturation-and-queueing"),
    ("too many postgres connections from my replicas", "database-load"),
    ("messages piling up with nobody reading them", "message-queues"),
]
idx = retrieval.get_index()
for k in (1, 3):
    hits = sum(any(r["id"].startswith(exp + "#") for r in idx.search(q, k)) for q, exp in CASES)
    print(f"hit@{k} = {hits}/{len(CASES)} = {hits/len(CASES):.2f}")
for q, exp in CASES:
    top = idx.search(q, 1)
    got = top[0]["id"] if top else "-"
    print(("OK  " if got.startswith(exp + "#") else "MISS"), f"{q[:60]!r} -> {got}")