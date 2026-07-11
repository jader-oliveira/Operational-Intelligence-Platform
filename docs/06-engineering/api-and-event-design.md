# API and Event Design

## API principles

- Versioned REST APIs for external integration.
- Durable workflows for long-running work.
- Idempotency keys for create and execute operations.
- Cursor pagination.
- Problem Details error format.
- Correlation and trace identifiers.
- Explicit tenant and environment context.

## Domain event principles

- Immutable events.
- Schema version and producer version.
- Event time and ingest time.
- Source identity and sequence/checkpoint.
- Trace and causation identifiers.
- Sensitivity and retention labels.
- Replay-safe consumers.

See `api/openapi.yaml` and `schemas/`.
