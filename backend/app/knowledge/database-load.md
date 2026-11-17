# Database load, connection pools and caching

A database that takes every request directly from application services is usually the first thing to run out of capacity. Each connection consumes memory, and servers cap them: PostgreSQL defaults to 100 connections, so many service replicas with large connection pools can exhaust the limit and cause connection pool exhaustion.

A cache in front of the database absorbs repeated reads. With a 90 percent hit rate the database sees only a tenth of the read traffic. Remember that cold caches and cache failures send the full load back to the database.

A message queue helps with writes: services enqueue work and a consumer writes to the database at a rate it can sustain. Also use a shared connection pooler and read replicas for scaling reads.
