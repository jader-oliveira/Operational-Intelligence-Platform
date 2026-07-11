# ADR 0001: Use advisory-first human-approved operations

- **Status:** Accepted as architecture baseline
- **Date:** 2026-07-11

## Context

The platform requires a durable design choice that supports safety, scale, traceability, and future evolution.

## Decision

Avoid autonomous production changes until safety and accuracy are proven.

## Consequences

- Implementation and testing must reflect this decision.
- Deviations require a new ADR.
- The Jira backlog contains work to operationalize the decision.
