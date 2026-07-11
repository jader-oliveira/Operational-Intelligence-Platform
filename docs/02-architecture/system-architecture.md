# System Architecture

## Architectural style

The platform uses modular services, durable workflows, an event-driven data plane, purpose-built telemetry stores, a canonical metadata layer, and policy-governed AI workflows.

## Logical layers

| Layer | Responsibilities |
| --- | --- |
| Source systems | VMware, Xen, Kubernetes, networks, storage, monitoring, logging, ITSM, CMDB, backup, Git, automation |
| Collection | Connector SDK, collectors, subscriptions, polling, credential isolation, checkpoints |
| Normalization | Canonical assets, events, configuration snapshots, changes, incidents, and evidence references |
| Data platform | Stream, relational metadata, metrics, logs, graph, vectors, object storage |
| Operational intelligence | Evidence engine, reasoner, predictor, guardian, advisor |
| Control | Policy, approval, orchestration, execution adapters, post-change validation |
| Learning | Decision graph, operations DNA, datasets, evaluation, model registry, feedback |
| Experience | Portal, API, chat/search, dashboards, integrations |

## Service boundaries

- Observer Service.
- Connector Runtime and SDK.
- Asset and Configuration Service.
- Knowledge Graph Service.
- Evidence Engine.
- Incident Workspace Service.
- Model Gateway.
- Retrieval Service.
- Reasoner.
- Predictor.
- Guardian.
- Advisor.
- Policy and Approval Service.
- Orchestrator.
- Execution Adapters.
- Evaluator and AI Governance.
- Operations DNA Service.
- Portal/API Gateway.

## Data ownership

- PostgreSQL: authoritative metadata and workflow state.
- Metrics platform: authoritative time-series records.
- OpenSearch: authoritative searchable logs and events.
- Object storage: immutable evidence bundles, datasets, reports, and artifacts.
- Graph projection: topology and decision relationships derived from canonical metadata.
- Vector index: retrieval accelerator, never the source of truth.

## Trust boundaries

1. External infrastructure management planes.
2. Collection runtime.
3. Core platform.
4. Model-serving zone.
5. Automation execution zone.
6. User and integration boundary.

Each boundary requires explicit identity, authorization, network policy, audit, and data-classification rules.
