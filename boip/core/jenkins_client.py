"""Jenkins/CloudBees client — the approval surface for ADR 0015 (amended:
the cluster runs Jenkins/CloudBees, not GitLab; see the ADR).

Triggering a pipeline run is *not* the human-approval gate — the pipeline
itself pauses on an `input` step (see deployment/jenkins/remediation-pipeline.Jenkinsfile)
before it ever calls boip's AWX client. This module only starts that
pipeline, the same way opening a GitLab MR doesn't itself change anything
until a human merges it.

Credentials (JENKINS_URL, JENKINS_USER, JENKINS_TOKEN) come from the
deployment environment. boip-core does not read Vault or Kubernetes
secrets itself.
"""

from __future__ import annotations

import os

import httpx


class JenkinsNotConfigured(RuntimeError):
    pass


def _auth_and_base_url() -> tuple[str, httpx.BasicAuth]:
    url = os.environ.get("JENKINS_URL")
    user = os.environ.get("JENKINS_USER")
    token = os.environ.get("JENKINS_TOKEN")
    if not url or not user or not token:
        raise JenkinsNotConfigured("JENKINS_URL, JENKINS_USER and JENKINS_TOKEN must be set")
    return url.rstrip("/"), httpx.BasicAuth(user, token)


def trigger_pipeline(job_name: str, parameters: dict) -> dict:
    """Start job_name with parameters (all values coerced to str, Jenkins'
    buildWithParameters only accepts form-encoded strings). Returns the
    queue item URL Jenkins hands back immediately — polling it to a real
    build number is a UI/human concern, not boip-core's."""
    base_url, auth = _auth_and_base_url()
    with httpx.Client(base_url=base_url, auth=auth, timeout=10.0) as c:
        crumb_resp = c.get("/crumbIssuer/api/json")
        crumb_resp.raise_for_status()
        crumb = crumb_resp.json()
        headers = {crumb["crumbRequestField"]: crumb["crumb"]}

        resp = c.post(
            f"/job/{job_name}/buildWithParameters",
            params={k: str(v) for k, v in parameters.items()},
            headers=headers,
        )
        resp.raise_for_status()
        queue_url = resp.headers.get("Location", "")
        return {"job_name": job_name, "queue_url": queue_url}


def get_build_status(job_name: str, build_number: int) -> dict:
    """Read-only — safe to poll at any time."""
    base_url, auth = _auth_and_base_url()
    with httpx.Client(base_url=base_url, auth=auth, timeout=10.0) as c:
        resp = c.get(f"/job/{job_name}/{build_number}/api/json")
        resp.raise_for_status()
        data = resp.json()
        return {"building": data.get("building"), "result": data.get("result")}
