# ADR 0010: Create a connector SDK before multiple connectors

- **Status:** Accepted as architecture baseline
- **Date:** 2026-07-11

## Context

The platform requires a durable design choice that supports safety, scale, traceability, and future evolution.

## Decision

Prevent incompatible one-off integrations.

## Consequences

- Implementation and testing must reflect this decision.
- Deviations require a new ADR.
- The Jira backlog contains work to operationalize the decision.
