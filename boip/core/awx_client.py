"""Thin AWX REST client — the executor side of ADR 0015.

Credentials (AWX_URL, AWX_TOKEN) come from the deployment environment,
never from this codebase. boip-core does not read Vault or Kubernetes
secrets itself; whatever process deploys it is responsible for injecting
these two env vars.

launch_job_template refuses to fire unless confirm=True is passed
explicitly by the caller — this is the ADR 0001 human-approval gate, not
a formality. There is no code path in this module that launches a job
without that flag set by something upstream that represents a human
decision (an approved recommendation, a pipeline stage that only runs
after review, etc.).
"""

from __future__ import annotations

import os

import httpx


class AWXNotConfigured(RuntimeError):
    pass


class AWXLaunchNotConfirmed(RuntimeError):
    pass


def _client() -> httpx.Client:
    url = os.environ.get("AWX_URL")
    token = os.environ.get("AWX_TOKEN")
    if not url or not token:
        raise AWXNotConfigured("AWX_URL and AWX_TOKEN must be set in the environment")
    return httpx.Client(base_url=url.rstrip("/"), headers={"Authorization": f"Bearer {token}"}, timeout=10.0)


def list_job_templates() -> list[dict]:
    """Read-only discovery — safe to call at any time."""
    with _client() as c:
        resp = c.get("/api/v2/job_templates/")
        resp.raise_for_status()
        return [
            {"id": jt["id"], "name": jt["name"], "description": jt.get("description", "")}
            for jt in resp.json()["results"]
        ]


def build_launch_payload(template_id: int, extra_vars: dict) -> dict:
    """Pure — the exact payload launch_job_template would POST. No network call."""
    return {"template_id": template_id, "extra_vars": extra_vars}


def launch_job_template(template_id: int, extra_vars: dict, confirm: bool = False) -> dict:
    if not confirm:
        raise AWXLaunchNotConfirmed(
            "launch_job_template requires confirm=True — this call site must represent an "
            "explicit human approval (ADR 0001), not an automatic action"
        )
    payload = build_launch_payload(template_id, extra_vars)
    with _client() as c:
        resp = c.post(f"/api/v2/job_templates/{template_id}/launch/", json={"extra_vars": payload["extra_vars"]})
        resp.raise_for_status()
        job = resp.json()
        return {"job_id": job["id"], "status": job.get("status"), "template_id": template_id}
