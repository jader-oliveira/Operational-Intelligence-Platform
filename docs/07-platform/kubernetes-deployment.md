# Kubernetes Deployment

## Namespace model

- platform-core.
- platform-data.
- platform-ai.
- platform-connectors.
- platform-execution.
- platform-observability.

## Workload model

Stateless APIs use Deployments. Stream processors and workers scale through queue depth. Databases should use proven operators or managed services. GPU model servers use dedicated nodes, taints, quotas, and network restrictions. Execution workers are isolated from model-serving.

## Production controls

Pod security, network policies, resource requests and limits, disruption budgets, topology spread, anti-affinity, autoscaling, sealed GitOps configuration, external secret integration, backup, and restore tests.
