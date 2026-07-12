# ADR 0013: Build the investigation capability on HolmesGPT

- **Status:** Accepted (supersedes the standalone Reasoner, Evidence Engine, Retrieval Service, and Model Gateway services from the original architecture)
- **Date:** 2026-07-12

## Context

HolmesGPT (Apache 2.0, CNCF sandbox, maintained by Robusta and Microsoft) already implements
the agentic investigation loop this project specified: iterative tool-calling over pluggable
toolsets, evidence citations tied to source data, read-only by design, RBAC-aware, and
LLM-agnostic including local models (Ollama/vLLM) for sovereign deployments. Rebuilding this
from scratch would cost months and produce a worse result.

## Decision

Use HolmesGPT as the investigation engine. BOIP's differentiation lives in custom toolsets
(VMware, Xen, config-change history, topology), the canonical data model, and the
approval/execution loop — all kept behind a thin interface so the agent can be replaced by
an in-house LiteLLM tool-calling loop if the dependency becomes a liability.

## Consequences

- Phases 3 and part of 1 of the original roadmap collapse into toolset development.
- Week 1 validation gates this decision: evidence discipline, tool-use correctness,
  accuracy on staged faults, latency/cost, and extension effort are scored before commit.
- Model Gateway is replaced by LiteLLM as a library (config-level model routing).
