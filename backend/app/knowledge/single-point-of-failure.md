# Single points of failure

A single point of failure is any component whose loss stops the whole system. The standard fix is replication: run at least two copies of the component so that one can fail without taking the service down.

Replication only helps if failover works. A load balancer needs health checks that remove a dead replica quickly, and a database needs a standby that can be promoted, either automatically or by a tested runbook. Two replicas that share one disk, one rack or one availability zone are still a single point of failure.

Redundancy must be capacity-aware: if two replicas each run at 70 percent utilization, losing one pushes the survivor past 100 percent. Plan N+1 capacity so the remaining replicas can absorb the failed one's traffic.
