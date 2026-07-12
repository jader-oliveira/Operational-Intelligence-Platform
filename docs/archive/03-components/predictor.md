# Predictor

## Purpose

Provide the predictor capability as an independently deployable, observable, and policy-controlled service.

## Responsibilities

- Anomaly detection.
- Capacity and saturation forecasting.
- Failure-risk prediction.
- Configuration drift and change-risk prediction.

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

- Backtesting, calibration, drift detection, feature lineage, and prediction horizons are mandatory.
- Prediction never triggers production action without policy and approval.

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
