"""Citation verifier: every evidence snippet must point at a real chunk and its text must
appear in that chunk. This is the guard to keep when generated summaries are added later."""
from .retrieval import Index


def _norm(s: str) -> str:
    return " ".join(s.split())


def snippet_ok(snippet: dict, idx: Index) -> bool:
    chunk = idx.by_id.get(snippet.get("id"))
    text = _norm(snippet.get("text", ""))
    return chunk is not None and bool(text) and text in chunk.text


def all_verified(evidence: list[dict], idx: Index) -> bool:
    return all(snippet_ok(s, idx) for s in evidence)