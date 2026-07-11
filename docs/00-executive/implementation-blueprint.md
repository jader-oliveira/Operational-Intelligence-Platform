# Implementation Blueprint

## 1. Product definition

BreuTech Operational Intelligence Platform is a modular platform that unifies infrastructure telemetry, topology, configuration, operational knowledge, AI reasoning, prediction, security assessment, remediation planning, human approval, and continuous evaluation.

## 2. Core capability chain

1. **Observe:** collect inventory, metrics, logs, events, configurations, changes, and ownership.
2. **Normalize:** convert platform-specific records into canonical entities and events.
3. **Understand:** build a time-aware dependency and decision graph.
4. **Investigate:** gather evidence for an incident or question.
5. **Reason:** generate ranked hypotheses with supporting and contradicting evidence.
6. **Predict:** forecast failures, capacity saturation, drift, and change risk.
7. **Guard:** evaluate security posture, hardening, and policy.
8. **Advise:** produce remediation options with risk, prerequisites, backup/snapshot guidance, rollback, and verification.
9. **Approve and execute:** use controlled workflows and existing automation tools.
10. **Evaluate and learn:** measure correctness, outcomes, value, safety, and model performance.

## 3. Recommended implementation stack

| Layer | Recommended baseline | Reason |
| --- | --- | --- |
| API and services | Python 3.12, FastAPI, Pydantic; Go only for high-throughput collectors | Fast delivery, strong AI ecosystem, typed contracts |
| Event backbone | Redpanda/Kafka-compatible streaming | Durable high-volume event transport and replay |
| Relational and metadata | PostgreSQL | Reliable source of truth and transactional state |
| Graph | PostgreSQL + Apache AGE for MVP; dedicated graph engine only if scale proves necessary | Reduces early operational complexity |
| Vector search | pgvector initially; Qdrant when retrieval scale requires separation | Simple MVP with a clear scale path |
| Metrics | Prometheus plus Thanos or Mimir | Long-term metrics and scalable queries |
| Logs | OpenSearch | Search, retention, and existing operational familiarity |
| Objects and datasets | MinIO | Versioned evidence bundles, model datasets, artifacts |
| Workflow engine | Temporal | Durable, auditable long-running incident and approval workflows |
| Automation adapters | AWX/Ansible, Terraform, PowerCLI, GitLab pipelines | Reuse existing controlled automation |
| Policy | Open Policy Agent | Deterministic approval, safety, and compliance decisions |
| Identity and secrets | Keycloak/OIDC and HashiCorp Vault | Central RBAC, service identity, and secret management |
| Model serving | vLLM or SGLang behind a model gateway | Portable serving for multiple open-weight models |
| Training and evaluation | Hugging Face Transformers, PEFT, TRL, MLflow, Airflow | Fine-tuning, experiment tracking, scheduled pipelines |
| UI | React and TypeScript | Operational portal and review workflows |
| Deployment | Kubernetes with Helm and GitOps | Repeatable, scalable, auditable delivery |
| Platform observability | OpenTelemetry, Prometheus, Grafana, OpenSearch | End-to-end tracing, metrics, logs, and AI KPIs |

## 4. Delivery sequence

### Phase 0 — Foundation
Vision, architecture, schemas, security boundaries, test environments, Jira backlog, ADRs, and success baselines.

### Phase 1 — Observe and inventory
Connector SDK plus VMware MVP. Establish canonical assets, events, configuration snapshots, and coverage metrics.

### Phase 2 — Understand
Data platform, dependency graph, ownership, service mapping, change history, and graph queries.

### Phase 3 — Investigate and reason
Evidence engine, incident workspace, retrieval, tool calling, ranked hypotheses, citations, uncertainty, and challenge-agent review.

### Phase 4 — Predict and guard
Anomaly detection, capacity forecasting, failure risk, configuration drift, hardening, and policy assessment.

### Phase 5 — Advise and approve
Remediation plans, pre-flight checks, snapshot/backup policy, approval workflow, dry runs, rollback, and post-change validation.

### Phase 6 — Learn and scale
Fine-tuning, continued pre-training experiments, multi-model benchmarking, operations DNA, AI governance dashboards, rollout, and optimization.

## 5. First production-worthy use cases

1. VMware datastore latency and VM performance degradation investigation.
2. ESXi host configuration drift and hardening assessment.
3. Xen host capacity and failure-risk forecast.
4. Kubernetes workload incident investigation using events, metrics, logs, and recent changes.
5. Safe remediation recommendation with backup/snapshot and rollback requirements.
6. AI recommendation quality dashboard with engineer approval and outcome tracking.

## 6. Architecture guardrails

- Raw telemetry remains in purpose-built stores; the LLM receives bounded evidence packages.
- Retrieval and tools are permission-scoped per user and incident.
- Recommendations are immutable, versioned records.
- No production action is executed without policy evaluation and explicit approval.
- Snapshot advice is workload-aware; snapshots are not assumed safe for every database or clustered system.
- Every action has preconditions, timeout, rollback, and verification.
- Sensitive data is redacted before training and model context assembly.

## 7. Definition of MVP

The MVP is complete when it can discover a VMware environment, maintain a current dependency graph, investigate a selected incident, produce a cited and confidence-scored root-cause report, recommend a safe human-approved remediation plan, and track whether the recommendation was accepted and correct.
