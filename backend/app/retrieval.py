"""Hybrid retrieval over the markdown knowledge base: BM25 + character-trigram
TF-IDF cosine, fused with reciprocal rank fusion (RRF). Pure Python, no downloads."""
import math, pathlib, re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

KB_DIR = pathlib.Path(__file__).parent / "knowledge"
_WORD = re.compile(r"[a-z0-9]+")
STOP = frozenset(
    "a an and are as at be by for from how in is it of on or that the this to under "
    "with without when what into than then their its".split()
)
RRF_K = 60


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokens(text: str) -> list[str]:
    return [_stem(t) for t in _WORD.findall(text.lower()) if t not in STOP]


def _grams(text: str) -> Counter:
    s = " " + " ".join(_WORD.findall(text.lower())) + " "
    return Counter(s[i : i + 3] for i in range(len(s) - 2))


@dataclass(frozen=True)
class Chunk:
    id: str
    title: str
    text: str


def load_chunks(kb_dir=KB_DIR) -> list[Chunk]:
    """One chunk per paragraph. Chunk id = '<file-stem>#<n>'. Heading lines set the title."""
    chunks = []
    for path in sorted(pathlib.Path(kb_dir).glob("*.md")):
        title, n = path.stem, 0
        for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            block = " ".join(block.split())
            if block.startswith("# "):
                title = block[2:].strip()
                continue
            if len(block) < 30:
                continue
            n += 1
            chunks.append(Chunk(f"{path.stem}#{n}", title, block))
    return chunks


class Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.by_id = {c.id: c for c in chunks}
        self.N = len(chunks)
        docs = [c.title + " " + c.text for c in chunks]
        self.toks = [tokens(d) for d in docs]
        self.tf = [Counter(t) for t in self.toks]
        self.avgdl = (sum(len(t) for t in self.toks) / self.N) if self.N else 1.0
        df = Counter(w for t in self.toks for w in set(t))
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        gdocs = [_grams(d) for d in docs]
        gdf = Counter(g for d in gdocs for g in d)
        self.gidf = {g: math.log(1 + self.N / n) for g, n in gdf.items()}
        self.gvec = [self._weigh(d) for d in gdocs]

    def _weigh(self, grams: Counter) -> dict:
        v = {g: (1 + math.log(c)) * self.gidf.get(g, 0.0) for g, c in grams.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {g: x / norm for g, x in v.items()}

    def _bm25(self, q: list[str], i: int, k1=1.5, b=0.75) -> float:
        tf, dl, s = self.tf[i], len(self.toks[i]), 0.0
        for w in set(q):
            f = tf.get(w, 0)
            if f:
                s += self.idf[w] * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / self.avgdl))
        return s

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = tokens(query)
        if not q or not self.N:
            return []
        qv = self._weigh(_grams(query))
        bm = [self._bm25(q, i) for i in range(self.N)]
        cos = [sum(w * self.gvec[i].get(g, 0.0) for g, w in qv.items()) for i in range(self.N)]
        # A chunk is a candidate if it shares a word with the query or is clearly similar by trigrams.
        cand = [i for i in range(self.N) if bm[i] > 0 or cos[i] >= 0.25]
        fused = Counter()
        for scores in (bm, cos):
            ranked = sorted(cand, key=lambda i: -scores[i])
            for r, i in enumerate(ranked):
                fused[i] += 1 / (RRF_K + r + 1)
        top = sorted(cand, key=lambda i: -fused[i])[:k]
        return [
            {"id": self.chunks[i].id, "title": self.chunks[i].title,
             "text": self.chunks[i].text, "score": round(fused[i], 4)}
            for i in top
        ]


@lru_cache(maxsize=1)
def get_index() -> Index:
    return Index(load_chunks())