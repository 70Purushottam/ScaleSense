# ScaleSense

Design a system on a canvas, then get an automatic review: single points of failure,
overloaded components, risky call chains, plus what-if simulation and cited explanations.

**Live demo:** <LIVE_URL> (free-tier backend, the first request may take up to a minute)

## What it does

- **Audit**: a rule engine over the architecture graph finds single points of failure
  (graph reachability), saturation (QPS propagated through load balancers, caches and
  fan-out), long synchronous chains, cycles (Tarjan SCC), unbuffered databases,
  consumer-less queues and request amplification.
- **Failure injection**: kill a node or some of its replicas and see which data stores
  become unreachable and which nodes become newly overloaded.
- **Load ramp**: find the bottleneck and the maximum sustainable QPS.
- **Explain**: each finding is matched to a short knowledge-base passage with a citation id,
  using hybrid retrieval (BM25 + character-trigram similarity, fused with reciprocal rank
  fusion) and a verifier that checks every cited snippet exists in its source chunk.

## Architecture

- `backend/` FastAPI. `analyzer.py` (graph algorithms), `capacity.py` (analytical load model,
  Little's Law), `rules.py` (rule engine), `simulate.py` (failure and ramp),
  `retrieval.py` and `verify.py` (knowledge base search and citation check).
- `frontend/` React + React Flow canvas.
- `loadtest/` Docker Compose stack (nginx, API replicas, Redis, Postgres) and k6 scripts
  used to validate the model against a real system.

## Run locally

```bash
pip install -r requirements.txt
cd backend && python -m pytest -q          # 19 tests
uvicorn app.main:app --reload              # http://localhost:8000/docs

cd frontend && npm install && npm run dev  # http://localhost:5173
```

## Evaluation

**Rule engine** on a seeded-flaw benchmark of 7 designs: precision 1.00, recall 1.00, 0 false
alarms on the clean design. The cases were written by me, so this shows the rules do what
I intended, not that they generalize.

**Retrieval** (12 queries, 7-document knowledge base): hit@1 = 12/12. This is a smoke test:
the knowledge base and queries were written together.

**Model vs. a real load test.** One API replica was calibrated (0.5 CPU cap, 350 requests/s
used as its capacity), then the model's predictions were compared with k6 measurements on
a 2-replica Docker stack behind nginx. "Last clean rate" means 0% failures and no dropped
iterations.

| Scenario | Predicted | Measured | Error |
|---|---|---|---|
| 2 replicas, all cached, capacity | 700 req/s | last clean 600, collapse at 700 | about 17% over |
| 1 replica, all cached | 350 (calibration) | last clean 400, collapse at 500 | calibration about 13% low |
| Lose 1 of 2 replicas at 500 req/s | api overloaded (143%) | 1 replica collapses (71% failures) | direction and point of failure match |
| 2 replicas, 90% cache hit rate | 700 req/s | last clean 400 | about 75% over |

Notes: the single-replica knee varied between 300 and 400 across repeated runs, so
differences under about 15% are within measurement noise. One 2-replica run at 500 req/s
failed while 600 passed, which I treat as a transient, so the 2-replica knee is a range of
600 to 700.

## Limitations

- The capacity model assumes every request costs the same. A cache miss in the real stack
  cost the API far more than a hit, so the model over-predicts capacity when the hit rate
  is below 100%.
- The model is steady-state: no queueing delay, retries, cache warm-up or autoscaling.
- Load tests ran on one laptop where the load generator, nginx, Redis and Postgres share
  the host with the API replicas.
- Retrieval is lexical and trigram-based, not neural, and the knowledge base is small.
- The citation verifier currently guards extractive snippets. It becomes more important
  if generated summaries are added.

## Lessons from the load test

- `docker compose run` silently scaled the API back to one replica, which made the first
  2-replica results meaningless. Replica counts are now checked before and after every
  measurement and the run is marked INVALID if they change.