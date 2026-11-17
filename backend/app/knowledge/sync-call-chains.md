# Long synchronous call chains

In a synchronous chain each service waits for the next one, so end-to-end latency is the sum of every hop's latency, and the tail latency of the slowest hop dominates.

Availability multiplies down along the chain. Three services that are each 99.9 percent available give roughly 99.7 percent for the request path, and every added hop lowers it further.

To shorten a chain, merge services that always call each other, replace a blocking call with an asynchronous message, cache data closer to the caller, or call independent dependencies in parallel. Set timeouts on every hop so one slow service cannot hold the whole chain.
