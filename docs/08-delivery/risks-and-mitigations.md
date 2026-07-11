# Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Poor or inconsistent source data | Coverage metrics, quality gates, quarantine, source contracts |
| AI overconfidence | Evidence requirement, calibrated confidence, challenge agent, approval |
| Excessive platform complexity | Start with PostgreSQL/AGE/pgvector and proven tools; measure before splitting |
| Unsafe remediation | Advisory-first, policy, dry-run, isolated execution, rollback, verification |
| Training data contamination | Dataset lineage, review, redaction, deduplication, versioning |
| Integration fragility | Connector SDK, contract tests, rate limiting, checkpoints |
| Low engineer trust | Transparent evidence, feedback loop, measurable accuracy, shadow mode |
| High inference cost | Task routing, smaller models, caching, bounded context, quotas |
| Vendor lock-in | Open schemas, model gateway, adapter interfaces |
