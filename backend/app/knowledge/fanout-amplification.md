# Fan-out and request amplification

Fan-out means one incoming request triggers several downstream calls. Load is amplified: if each request to a service makes 8 calls to a dependency, the dependency sees 8 times the traffic.

Reduce amplification by batching many small calls into one, caching repeated lookups within a request, fetching only the fields needed, and moving non-urgent calls to asynchronous processing.

Amplification also hurts latency, because a request that fans out to many calls is only as fast as the slowest of them. Hedged requests and per-call timeouts limit that tail effect.
