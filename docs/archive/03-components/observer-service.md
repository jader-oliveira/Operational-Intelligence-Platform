# Observer Service

## Purpose

Provide the observer service capability as an independently deployable, observable, and policy-controlled service.

## Responsibilities

- Discover inventory and relationships.
- Collect configuration, metrics references, logs, events, alarms, and changes.
- Use adaptive polling and subscriptions.
- Publish canonical envelopes with checkpoints and provenance.

## Inputs

- Canonical asset, incident, evidence, policy, and organization context.
- Authenticated requests through the API gateway or durable workflow engine.
- Versioned configuration and schemas.

## Outputs

- Structured, schema-validated records.
- Provenance and audit metadata.
- Service metrics, logs, and traces.
- Domain events for downstream consumers.

## Constraints and safety

- Read-only credentials by default.
- Per-connector isolation, rate limits, retries, and circuit breakers.
- Coverage, freshness, error, and duplicate metrics.

## Scaling and failure behavior

- Horizontally scalable workers where applicable.
- Backpressure and bounded concurrency.
- Retry only idempotent operations.
- Dead-letter or quarantine invalid work.
- Degrade per source or capability rather than failing the whole platform.

## Required telemetry

- Request and workflow latency.
- Success, error, timeout, and retry rates.
- Queue depth and saturation.
- Data freshness and evidence coverage.
- AI tokens, GPU time, cost, and structured-output validation failures where applicable.

## Test strategy

- Unit tests for domain logic.
- Schema and contract tests.
- Integration tests with simulated and lab systems.
- Failure-injection tests.
- Security and authorization tests.
- Scale tests against the 2,000-VM target profile.
