# ADR 0008: Use Temporal for durable workflows

- **Status:** Accepted as architecture baseline
- **Date:** 2026-07-11

## Context

The platform requires a durable design choice that supports safety, scale, traceability, and future evolution.

## Decision

Incident, approval, and execution workflows are long-running and failure-prone.

## Consequences

- Implementation and testing must reflect this decision.
- Deviations require a new ADR.
- The Jira backlog contains work to operationalize the decision.
