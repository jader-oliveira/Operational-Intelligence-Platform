# Helm Deployment

Create one umbrella chart with independently enabled services. Keep stateful platforms in separate charts or operators. Environment-specific values must not contain secrets; use external secret references.

Recommended values groups:

- global identity, environment, and image policy.
- connectors.
- stream and data services.
- operational-intelligence services.
- model gateway and GPU scheduling.
- policy, approval, and execution.
- observability.
- resource, autoscaling, disruption, and network-policy settings.
