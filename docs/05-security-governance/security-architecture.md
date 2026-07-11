# Security Architecture

## Identity

- OIDC for users and services.
- RBAC plus contextual policy.
- Separate collector, reasoning, approval, and execution identities.
- Short-lived credentials where supported.
- Service-to-service mTLS.

## Secrets

- Secrets remain in Vault or native secret stores.
- Connectors receive scoped credentials at runtime.
- Secrets are never embedded in prompts, logs, datasets, or evidence bundles.
- Secret-access events are audited.

## Network

- Namespace and service segmentation.
- Default-deny network policies.
- Restricted egress from model-serving and execution zones.
- Dedicated execution workers for production automation.

## Data protection

- Classification labels.
- Encryption.
- Redaction and tokenization.
- Retention and deletion policies.
- Immutable audit and evidence records.
- Training dataset approval workflow.
