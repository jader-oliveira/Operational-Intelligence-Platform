# Testing Strategy

## Test pyramid

- Unit tests.
- Schema and contract tests.
- Connector simulation tests.
- Integration tests with VMware, Xen, Kubernetes, telemetry, identity, and automation labs.
- End-to-end incident workflows.
- Performance and soak tests.
- Chaos and dependency-failure tests.
- Security tests.
- AI evaluation and regression suites.
- Human-factors and approval workflow tests.

## Release gates

No release passes without schema compatibility, authorization tests, evidence/citation regression, golden-case AI evaluation, deployment rollback test, and critical security scan.
