# ADR-008: Zero-Code Delay Pattern for RabbitMQ Retry Loops

## Status

Accepted

## Context

The `fhir-export-worker` must be resilient against transient network failures when the destination FHIR server drops connections or returns HTTP 5xx/429. Originally, the worker utilized the `tenacity` library to execute exponential backoff retries via `asyncio.sleep` while still holding the RabbitMQ message inside the consumer.

This created a severe "Stateful Sinner" anti-pattern. While the Python event loop was sleeping, the unacknowledged message remained in the worker's RAM, blocking a prefetch slot, and tying the state of the timeout explicitly to the lifespan of the worker container. If the container crashed, the timer was lost, and the message reverted to the broker. This approach did not scale horizontally and violated Tier 1 Cloud-Native architecture, where state must reside in the broker, not the application layer.

## Decision

We mandate the **Zero-Code Delay Pattern** for all asynchronous wait states and retry loops involving message queues.
Instead of sleeping in the consumer, the worker calculates the delay, rejects the transiently failed message by pushing it manually to a dedicated retry Dead-Letter Exchange (`fhir_retry.dlx`), and acknowledges the original message in the main queue. The newly published message is heavily configured via the broker:

- It includes the `x-retry-count` header to track attempt history.
- It specifies a TTL (`expiration`) exactly equal to the calculated delay.
- The retry queue does **not** have a consumer. It routes dead messages (TTL expired) back to the original queue.

## Consequences

- **Positive:** Absolute resilience. Worker containers can be destroyed instantly; the delays are stored safely on the broker's disk. Workers consume 0 memory for sleeping tasks. No prefetch slots are wasted.
- **Negative:** Marginally increased complexity in the RabbitMQ topology (requires dedicated retry exchanges and queues for each delayed queue) and slight overhead to manually reconstruct aio_pika messages for publishing instead of relying on simple Python decorators like `@retry`.
