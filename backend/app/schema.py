"""Canvas graph schema: what the React Flow frontend sends to /audit."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator

NodeType = Literal["client", "load_balancer", "service", "cache", "database", "queue", "cdn"]


class Node(BaseModel):
    id: str
    type: NodeType
    label: str = ""
    replicas: int = Field(1, ge=1)
    capacity_qps: float = Field(1000.0, gt=0)   # per replica
    latency_ms: float = Field(10.0, ge=0)
    hit_rate: float = Field(0.0, ge=0, le=1)    # caches / CDNs only
    qps: float = Field(0.0, ge=0)               # clients only: traffic generated


class Edge(BaseModel):
    source: str
    target: str
    kind: Literal["sync", "async"] = "sync"
    fanout: float = Field(1.0, gt=0)            # downstream calls per incoming request


class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]

    @model_validator(mode="after")
    def _check_refs(self):
        ids = [n.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate node ids")
        known = set(ids)
        for e in self.edges:
            if e.source not in known or e.target not in known:
                raise ValueError(f"edge references unknown node: {e.source}->{e.target}")
        return self