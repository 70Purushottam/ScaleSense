"""Creates backend/app/knowledge/*.md. Run once from the project root: python scripts\\make_kb.py"""
import pathlib

OUT = pathlib.Path(__file__).parents[1] / "backend" / "app" / "knowledge"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
"single-point-of-failure.md": """# Single points of failure

A single point of failure is any component whose loss stops the whole system. The standard fix is replication: run at least two copies of the component so that one can fail without taking the service down.

Replication only helps if failover works. A load balancer needs health checks that remove a dead replica quickly, and a database needs a standby that can be promoted, either automatically or by a tested runbook. Two replicas that share one disk, one rack or one availability zone are still a single point of failure.

Redundancy must be capacity-aware: if two replicas each run at 70 percent utilization, losing one pushes the survivor past 100 percent. Plan N+1 capacity so the remaining replicas can absorb the failed one's traffic.
""",
"saturation-and-queueing.md": """# Saturation and queueing

A component is saturated when incoming load reaches its capacity. Latency does not grow linearly with load: in a simple single-server queue the average wait is proportional to utilization divided by one minus utilization, so waiting is about 4 times the service time at 80 percent, 9 times at 90 percent and 19 times at 95 percent.

Because of this queueing effect, keep steady-state utilization well below 100 percent, commonly under 70 to 80 percent, and treat anything above 80 percent as a warning that latency will rise sharply.

When a bottleneck is overloaded, add capacity by scaling out replicas or scaling up the node. Protect it meanwhile with backpressure, which tells callers to slow down, and load shedding, which rejects excess requests early with a fast error instead of letting every request time out.
""",
"sync-call-chains.md": """# Long synchronous call chains

In a synchronous chain each service waits for the next one, so end-to-end latency is the sum of every hop's latency, and the tail latency of the slowest hop dominates.

Availability multiplies down along the chain. Three services that are each 99.9 percent available give roughly 99.7 percent for the request path, and every added hop lowers it further.

To shorten a chain, merge services that always call each other, replace a blocking call with an asynchronous message, cache data closer to the caller, or call independent dependencies in parallel. Set timeouts on every hop so one slow service cannot hold the whole chain.
""",
"retry-storms-cycles.md": """# Retry storms and cyclic dependencies

When services call each other in a cycle, a slowdown can feed on itself. Callers time out and retry, the retries add load to the already slow service, and the failure spreads: a retry storm that causes a cascading failure.

Retries multiply across layers. If each of three layers retries three times, one user request can become 27 calls on the deepest dependency.

Mitigate with a retry budget, exponential backoff with jitter, circuit breakers that stop calling a failing dependency, and timeouts that shrink at each layer. Prefer breaking the cycle in the design, for example by moving shared logic into a library or sending events asynchronously instead of calling back.
""",
"database-load.md": """# Database load, connection pools and caching

A database that takes every request directly from application services is usually the first thing to run out of capacity. Each connection consumes memory, and servers cap them: PostgreSQL defaults to 100 connections, so many service replicas with large connection pools can exhaust the limit and cause connection pool exhaustion.

A cache in front of the database absorbs repeated reads. With a 90 percent hit rate the database sees only a tenth of the read traffic. Remember that cold caches and cache failures send the full load back to the database.

A message queue helps with writes: services enqueue work and a consumer writes to the database at a rate it can sustain. Also use a shared connection pooler and read replicas for scaling reads.
""",
"message-queues.md": """# Message queues, consumers and backlog

A queue decouples producers from consumers, but it only works if consumers exist and keep up. A queue with no consumer accumulates messages without limit until storage runs out.

The backlog grows at the arrival rate minus the consumer processing rate. Watch consumer lag, the number of messages waiting or the age of the oldest message, and alert when it keeps growing.

Scale consumers horizontally, set a retention or maximum length, route repeatedly failing messages to a dead-letter queue, and make processing idempotent because most queues deliver at least once.
""",
"fanout-amplification.md": """# Fan-out and request amplification

Fan-out means one incoming request triggers several downstream calls. Load is amplified: if each request to a service makes 8 calls to a dependency, the dependency sees 8 times the traffic.

Reduce amplification by batching many small calls into one, caching repeated lookups within a request, fetching only the fields needed, and moving non-urgent calls to asynchronous processing.

Amplification also hurts latency, because a request that fans out to many calls is only as fast as the slowest of them. Hedged requests and per-call timeouts limit that tail effect.
""",
}

for name, body in FILES.items():
    (OUT / name).write_text(body, encoding="utf-8", newline="\n")
print(f"wrote {len(FILES)} files to {OUT}")