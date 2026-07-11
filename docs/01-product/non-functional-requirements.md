# Non-Functional Requirements

## Scale

- Initial target: 2,000+ VMs, multiple hypervisors, Kubernetes, and supporting infrastructure.
- Collector and processing services scale horizontally.
- Backpressure and replay are supported.
- Raw high-volume telemetry is not copied unnecessarily into the relational database.

## Reliability

- No single connector failure stops the platform.
- Collection checkpoints permit safe resume.
- Incident workflows are durable.
- Recommendation and approval history is immutable and auditable.
- Recovery objectives are documented and tested.

## Security

- Read-only access by default.
- Least privilege and short-lived credentials.
- Encryption in transit and at rest.
- Tenant, environment, and data-classification boundaries.
- Sensitive-data redaction before model use.
- Complete audit log for access, AI generation, approval, and execution.

## Explainability

- Every conclusion links to evidence.
- Confidence is calibrated and never represented as certainty.
- Contradictory evidence and alternative hypotheses are shown.
- Model, prompt, retrieval, tool, policy, and data versions are recorded.

## Performance targets for MVP

- Inventory freshness: under 15 minutes for normal polling.
- Incident evidence package: under 2 minutes for bounded investigations.
- First AI hypothesis report: under 3 minutes after evidence is ready.
- Portal API p95: under 500 ms for non-AI reads.
- Recommendation generation p95: target under 60 seconds, excluding evidence collection.
