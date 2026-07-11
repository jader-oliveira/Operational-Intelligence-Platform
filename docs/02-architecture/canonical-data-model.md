# Canonical Data Model

## Core entities

- Asset.
- Relationship.
- Observation.
- Metric reference.
- Log or event reference.
- Configuration snapshot.
- Change.
- Incident.
- Evidence item.
- Hypothesis.
- Recommendation.
- Approval.
- Execution.
- Verification.
- Policy decision.
- Model run.
- Feedback.
- Organization context.

## Required common fields

- Stable global identifier.
- Source and source-native identifier.
- Environment and tenant.
- Observed, effective, and ingested timestamps.
- Classification and sensitivity.
- Provenance and integrity hash.
- Schema version.
- Ownership and business service.
- Lifecycle state.
- Tags and labels.

## Time model

Topology and configuration are time-aware. The system must answer both “what is connected now?” and “what was connected when the incident occurred?”
