# Model Strategy

## Principle

Do not bind the platform to a single model. Use a model gateway with task-specific routing, common structured contracts, and a shared evaluation harness.

## Model roles

- Embedding model for retrieval.
- Reranker for evidence relevance.
- General reasoning model for incident analysis.
- Code and configuration model for remediation review.
- Small local classifier for routing, redaction, and guardrails.
- Time-series and tabular models for forecasting and anomaly detection.

## Selection criteria

Accuracy on internal golden cases, evidence faithfulness, structured-output reliability, tool-use correctness, latency, context length, deployment fit, license, GPU requirements, cost, and security.

## Promotion process

Candidate -> offline evaluation -> red-team and safety evaluation -> shadow mode -> limited pilot -> production -> continuous monitoring.
