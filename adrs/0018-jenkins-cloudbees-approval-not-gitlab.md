# ADR 0018: Jenkins/CloudBees as the approval workflow, not GitLab

- **Status:** Accepted (supersedes [ADR 0015](0015-gitlab-mr-approval-awx-execution.md)'s approval-surface choice; the AWX-as-executor decision from ADR 0015 stands unchanged)
- **Date:** 2026-07-12

## Context

ADR 0015 assumed GitLab MRs as the approval surface: "they already trust GitLab review
workflows." Checked directly against the running cluster (`kubectl get ns`) rather than
against the doc: there is no GitLab namespace, no GitLab-equivalent. The cluster runs
Jenkins (`jenkins` namespace) and CloudBees Core (`cloudbees-core` namespace) instead —
already deployed, already trusted, already the CI/CD system of record.

Building the approval loop around infrastructure that doesn't exist would mean either
standing up GitLab solely for this feature (real infra cost, real new attack surface,
against ADR 0016's monolith-first / reuse-what-you-run spirit) or building against a
document instead of a system.

## Decision

A recommendation triggers a Jenkins/CloudBees pipeline
(`deployment/jenkins/remediation-pipeline.Jenkinsfile`) parameterized with the
recommendation and incident IDs. The pipeline's `input` step is the human-approval gate —
submitter restricted by risk tier (`engineers` for low/medium, `senior-engineers` for
high/critical). Only after approval does the pipeline proceed to launch an AWX job
template. boip-core never calls AWX directly from a recommendation; it only triggers the
gated pipeline, mirroring how ADR 0015 never let opening an MR itself constitute approval.

`recommendation.gitlab_mr_url` is renamed to `recommendation.approval_url`, generic to
whichever pipeline system stores the run link.

## Consequences

- ADR 0001 (human approval before production change) is enforced by infrastructure this
  client already audits — same trust property ADR 0015 wanted from GitLab, delivered by
  the tool actually running.
- No new service, no new attack surface, no procurement conversation for a second CI/CD
  platform in the client's estate.
- If a future client's estate runs GitLab instead, `jenkins_client.py`'s two functions
  (`trigger_pipeline`, `get_build_status`) are the seam to swap — `recommendation.py`
  calls them by name, not by tool assumption.
- The three remediation job templates ADR 0015 assumed (storage vMotion, k8s
  resize/restart, config revert) still don't exist in AWX yet — the Jenkinsfile's
  execute stage fails closed on a placeholder template name until that work (MVP plan
  weeks 6-7) lands. This ADR unblocks the approval gate; it does not claim execution is
  wired.
