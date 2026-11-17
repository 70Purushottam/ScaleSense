"""Deterministic graph analysis: SCCs (cycles), reachability, single points of failure."""
from collections import defaultdict, deque
from .schema import Graph


def adjacency(g: Graph) -> dict[str, list[str]]:
    adj = defaultdict(list)
    for n in g.nodes:
        adj[n.id]
    for e in g.edges:
        adj[e.source].append(e.target)
    return adj


def tarjan_scc(g: Graph) -> list[list[str]]:
    """Tarjan's algorithm. Returns every SCC (single nodes included)."""
    adj = adjacency(g)
    index, low, on_stack, stack, out = {}, {}, set(), [], []
    counter = [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in adj[v]:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(comp)

    for n in g.nodes:
        if n.id not in index:
            visit(n.id)
    return out


def cyclic_sccs(g: Graph) -> list[list[str]]:
    """SCCs that are real cycles (size > 1, or a self-loop)."""
    selfloops = {e.source for e in g.edges if e.source == e.target}
    return [c for c in tarjan_scc(g) if len(c) > 1 or c[0] in selfloops]


def reachable(adj, starts, removed: str | None = None) -> set[str]:
    seen = {s for s in starts if s != removed}
    q = deque(seen)
    while q:
        v = q.popleft()
        for w in adj[v]:
            if w != removed and w not in seen:
                seen.add(w)
                q.append(w)
    return seen


def single_points_of_failure(g: Graph) -> list[dict]:
    """A non-client node with one replica whose loss cuts clients off from data stores."""
    adj = adjacency(g)
    clients = [n.id for n in g.nodes if n.type == "client"]
    stores = {n.id for n in g.nodes if n.type == "database"}
    base = reachable(adj, clients) & stores
    result = []
    for n in g.nodes:
        if n.type == "client" or n.replicas > 1:
            continue
        lost = base - (reachable(adj, clients, removed=n.id) & stores)
        if lost:
            result.append({"node": n.id, "cuts_off": sorted(lost)})
    return result


def longest_sync_path(g: Graph) -> list[str]:
    """Longest simple path over sync edges (graphs are small, so DFS is fine)."""
    adj = defaultdict(list)
    for e in g.edges:
        if e.kind == "sync":
            adj[e.source].append(e.target)
    best: list[str] = []

    def dfs(v, path, on_path):
        nonlocal best
        if len(path) > len(best):
            best = path[:]
        for w in adj[v]:
            if w not in on_path:
                on_path.add(w); path.append(w)
                dfs(w, path, on_path)
                path.pop(); on_path.discard(w)

    for n in g.nodes:
        dfs(n.id, [n.id], {n.id})
    return best