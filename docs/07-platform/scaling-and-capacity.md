# Scaling and Capacity

## Scale dimensions

- Number of assets and relationships.
- Metrics and log volume.
- Event rate.
- Concurrent incidents.
- Graph query complexity.
- Retrieval corpus.
- Model concurrency and context size.
- Automation executions.

## Strategy

Partition collectors by source, use stream backpressure, downsample metrics, tier log retention, cache graph traversals, batch embeddings, separate interactive and batch inference, and enforce per-tenant quotas.
