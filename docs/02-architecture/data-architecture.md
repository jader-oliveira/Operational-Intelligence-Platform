# Data Architecture

## Data flow

Source -> connector -> raw envelope -> canonical normalizer -> event stream -> specialized stores -> graph projection -> evidence package -> model and policy workflow.

## Data classes

- Inventory and topology.
- Metrics and forecasts.
- Logs, events, alarms, and traces.
- Configuration snapshots and diffs.
- Changes, deployments, and automation runs.
- Incidents, tickets, approvals, and outcomes.
- Runbooks, vendor documentation, internal standards, and postmortems.
- AI prompts, responses, evidence links, scores, feedback, and model metadata.

## Storage principles

- Store raw source references and hashes to prove provenance.
- Keep immutable evidence bundles for incidents and recommendations.
- Separate hot operational retention from long-term training retention.
- Redact secrets and personal data before dataset promotion.
- Version canonical schemas and support backward-compatible evolution.
- Enforce retention and deletion at the data-classification level.

## Data quality controls

- Schema validation.
- Source timestamp versus ingest timestamp checks.
- Duplicate and replay detection.
- Coverage and freshness metrics.
- Referential integrity for assets and relationships.
- Configuration snapshot completeness.
- Clock-skew detection.
- Quarantine for invalid payloads.
