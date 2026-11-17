# Saturation and queueing

A component is saturated when incoming load reaches its capacity. Latency does not grow linearly with load: in a simple single-server queue the average wait is proportional to utilization divided by one minus utilization, so waiting is about 4 times the service time at 80 percent, 9 times at 90 percent and 19 times at 95 percent.

Because of this queueing effect, keep steady-state utilization well below 100 percent, commonly under 70 to 80 percent, and treat anything above 80 percent as a warning that latency will rise sharply.

When a bottleneck is overloaded, add capacity by scaling out replicas or scaling up the node. Protect it meanwhile with backpressure, which tells callers to slow down, and load shedding, which rejects excess requests early with a fast error instead of letting every request time out.
