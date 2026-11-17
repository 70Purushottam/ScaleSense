# Message queues, consumers and backlog

A queue decouples producers from consumers, but it only works if consumers exist and keep up. A queue with no consumer accumulates messages without limit until storage runs out.

The backlog grows at the arrival rate minus the consumer processing rate. Watch consumer lag, the number of messages waiting or the age of the oldest message, and alert when it keeps growing.

Scale consumers horizontally, set a retention or maximum length, route repeatedly failing messages to a dead-letter queue, and make processing idempotent because most queues deliver at least once.
