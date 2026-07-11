# ADR 0003: Use an event-driven data plane

- **Status:** Accepted as architecture baseline
- **Date:** 2026-07-11

## Context

The platform requires a durable design choice that supports safety, scale, traceability, and future evolution.

## Decision

Support replay, backpressure, and independent consumers.

## Consequences

- Implementation and testing must reflect this decision.
- Deviations require a new ADR.
- The Jira backlog contains work to operationalize the decision.
