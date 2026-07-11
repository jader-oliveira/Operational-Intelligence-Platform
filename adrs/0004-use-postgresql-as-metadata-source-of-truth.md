# ADR 0004: Use PostgreSQL as metadata source of truth

- **Status:** Accepted as architecture baseline
- **Date:** 2026-07-11

## Context

The platform requires a durable design choice that supports safety, scale, traceability, and future evolution.

## Decision

Minimize early platform sprawl and preserve transactions.

## Consequences

- Implementation and testing must reflect this decision.
- Deviations require a new ADR.
- The Jira backlog contains work to operationalize the decision.
