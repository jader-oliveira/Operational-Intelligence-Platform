# ADR 0015: GitLab merge requests as the approval workflow, AWX as the executor

- **Status:** Superseded by [ADR 0018](0018-jenkins-cloudbees-approval-not-gitlab.md) — GitLab is not deployed in the target cluster; kept below for history (originally: Accepted, supersedes the standalone Policy/Approval Service, Orchestrator, and Execution Adapters; defers Temporal and OPA)
- **Date:** 2026-07-12

## Context

Target clients will not allow an AI to touch production directly, but they already trust
GitLab review workflows and Ansible/AWX execution. The original design introduced Temporal,
OPA, and three new services to achieve what these tools already provide: identity-bound
approval, immutable audit trail, controlled execution, and rollback.

## Decision

A recommendation is rendered as a merge request containing the plan, evidence links,
rollback and verification steps. CODEOWNERS enforces who may approve. Merging triggers a
pipeline that launches AWX job templates: pre-flight -> change -> verification, with results
posted back to the recommendation record. Policy checks are plain, unit-tested Python
functions until a second client requires divergent policy (then OPA is reconsidered).

## Consequences

- The human-approval-before-change principle (ADR 0001) is enforced by infrastructure the
  client already audits, satisfying NIS2 change-control expectations with zero new services.
- Incident lifecycle state lives in PostgreSQL columns; Temporal is deferred indefinitely.
- Remediation catalog grows as Ansible roles, reusing existing team expertise.
