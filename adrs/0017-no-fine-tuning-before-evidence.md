# ADR 0017: No model fine-tuning before 1,000 labeled investigations

- **Status:** Accepted (supersedes the Phase 6 fine-tuning and continued-pretraining program)
- **Date:** 2026-07-12

## Context

The original roadmap planned fine-tuning, continued pretraining, TRL, MLflow, and Airflow.
In 2026, frontier and strong open-weight models with careful context engineering outperform
small-corpus fine-tunes for infrastructure reasoning. The project has zero labeled
investigation data today.

## Decision

Invest in context engineering (toolset design, evidence packaging, golden cases,
interpretation instructions) and model routing via LiteLLM. Fine-tuning is reconsidered only
after at least 1,000 labeled investigations with engineer-verified outcomes exist.

## Consequences

- Golden incident cases double as evaluation harness and demo, replacing the ML platform.
- Sovereign mode ships with off-the-shelf open-weight models; the measured accuracy delta
  versus frontier APIs is disclosed to clients as a priced trade-off.
- MLflow/Airflow/TRL are removed from the implementation stack.
