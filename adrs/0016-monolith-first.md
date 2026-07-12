# ADR 0016: Monolith-first; defer the event backbone and dedicated stores

- **Status:** Accepted (supersedes the 17-service decomposition; defers Redpanda/Kafka, OpenSearch, Thanos/Mimir, Qdrant, Keycloak, MinIO)
- **Date:** 2026-07-12

## Context

The original architecture decomposed the platform into 17 services on a streaming backbone
with five specialized data stores. At MVP scale (single-digit clients, 2,000-VM estates)
this is operational burden without benefit, and it delays first user-visible value by
quarters.

## Decision

One FastAPI application (`boip-core`) plus collector jobs, backed by PostgreSQL (metadata,
state, evidence, diffs, pgvector if needed). Metrics and logs are queried from the client's
existing Prometheus/Zabbix and log stack rather than owned. Services are split only when a
concrete seam hurts in production.

## Consequences

- Deployment is one Helm chart with demo/pilot/sovereign profiles, plus docker-compose for
  clients without spare Kubernetes capacity.
- Evidence bundles live in PostgreSQL until volume (~50GB) justifies object storage.
- The canonical data model from ADR 0002 survives as seven PostgreSQL tables.
