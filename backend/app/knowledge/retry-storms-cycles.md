# Retry storms and cyclic dependencies

When services call each other in a cycle, a slowdown can feed on itself. Callers time out and retry, the retries add load to the already slow service, and the failure spreads: a retry storm that causes a cascading failure.

Retries multiply across layers. If each of three layers retries three times, one user request can become 27 calls on the deepest dependency.

Mitigate with a retry budget, exponential backoff with jitter, circuit breakers that stop calling a failing dependency, and timeouts that shrink at each layer. Prefer breaking the cycle in the design, for example by moving shared logic into a library or sending events asynchronously instead of calling back.
