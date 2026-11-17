from app import retrieval, verify

idx = retrieval.get_index()


def top_doc(q):
    return idx.search(q, k=1)[0]["id"].split("#")[0]


def test_kb_loads():
    assert len(idx.chunks) >= 15
    assert len({c.id for c in idx.chunks}) == len(idx.chunks)


def test_each_rule_query_finds_its_doc():
    assert top_doc("how to remove single point of failure with replication and failover") == "single-point-of-failure"
    assert top_doc("message queue consumer lag and unbounded backlog growth") == "message-queues"
    assert top_doc("request amplification fan-out and batching to reduce downstream load") == "fanout-amplification"


def test_unrelated_query_returns_nothing():
    assert idx.search("chocolate cake recipe") == []
    assert idx.search("") == []


def test_verifier_accepts_real_and_rejects_fake():
    ev = idx.search("retry storms", k=2)
    assert ev and verify.all_verified(ev, idx)
    assert not verify.snippet_ok({"id": "nope#1", "text": "x"}, idx)
    assert not verify.snippet_ok({"id": ev[0]["id"], "text": "invented claim"}, idx)