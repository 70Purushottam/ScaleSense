import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .schema import Graph
from . import rules, capacity, simulate, retrieval, verify

app = FastAPI(title="ScaleSense")

ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit")
def audit(g: Graph):
    return {"findings": rules.run_all(g), "load": capacity.utilization(g)}


class FailureSpec(BaseModel):
    node: str
    replicas_lost: int | None = None   # None = whole node down


class FailureRequest(BaseModel):
    graph: Graph
    failures: list[FailureSpec]


@app.post("/simulate/failure")
def simulate_failure(req: FailureRequest):
    try:
        return simulate.failure_report(req.graph, {f.node: f.replicas_lost for f in req.failures})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/simulate/ramp")
def simulate_ramp(g: Graph):
    try:
        return simulate.ramp(g)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/audit/explain")
def audit_explain(g: Graph):
    idx = retrieval.get_index()
    out = []
    for f in rules.run_all(g):
        q = f.get("retrieval_query", "")
        evidence = idx.search(q, k=2) if q else []
        out.append({**f, "evidence": evidence, "verified": verify.all_verified(evidence, idx)})
    return {"findings": out}