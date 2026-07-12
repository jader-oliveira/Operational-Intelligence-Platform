"""Turn an investigation report's top hypothesis into a Recommendation
(ADR 0001: advisory-first, human-approved). No AWX job is launched from
here — this only proposes a plan; execution is a separate, explicitly
gated step (see awx_client.launch_job_template).

Risk is graded by blast radius, not by guesswork: reverting a change on
an asset that other assets depend on (a shared datastore, a host) is
judged riskier than reverting a change scoped to the single incident
asset, because the topology data already tells us who else is affected.
"""

from __future__ import annotations

from . import jenkins_client, queries

REMEDIATION_PIPELINE_JOB = "boip-remediation-approval"


def propose_recommendation(incident_id: int) -> dict:
    incident = queries.get_incident(incident_id)
    if incident is None:
        raise ValueError(f"incident {incident_id} not found")

    evidence = queries.list_evidence(incident_id)
    report = next((e["content"] for e in reversed(evidence) if e["kind"] == "investigation_report"), None)
    if report is None:
        raise ValueError(f"incident {incident_id} has no investigation report yet — run /investigate first")
    if not report["ranked_changes"]:
        raise ValueError(f"incident {incident_id}'s investigation found no changes to remediate")

    top = report["ranked_changes"][0]
    target_asset = queries.find_asset_by_name(top["asset"])
    neighbors = queries.one_hop_neighbors(target_asset["id"]) if target_asset else []
    dependents = [n for n in neighbors if n["direction"] == "depended_on_by"]
    risk = "high" if len(dependents) > 1 else ("medium" if dependents else "low")

    summary = (
        f"Revert {top['asset']}.{top['path']} from {top['new_value']!r} back to "
        f"{top['old_value']!r} — ranked as the most likely cause of '{incident['title']}'."
    )

    steps = [{
        "action": "revert_config",
        "asset": top["asset"], "path": top["path"],
        "from_value": top["new_value"], "to_value": top["old_value"],
    }]
    rollback = [{
        "action": "revert_config",
        "asset": top["asset"], "path": top["path"],
        "from_value": top["old_value"], "to_value": top["new_value"],
        "note": "re-apply the original change if the revert does not resolve the incident or causes a regression",
    }]
    verification = [
        {"check": "config_matches", "asset": top["asset"], "path": top["path"], "expect": top["old_value"]},
        {"check": "collector_rerun", "asset": top["asset"],
         "note": "re-run the collector and confirm no new unexplained config_change rows appear"},
    ]
    if risk != "low":
        verification.append({
            "check": "blast_radius_healthy",
            "assets": [d["name"] for d in dependents],
            "note": f"{top['asset']} is shared by {len(dependents)} other asset(s) — verify they are healthy after the revert",
        })

    rec = queries.create_recommendation(
        incident_id=incident_id, summary=summary, risk=risk, confidence=report["confidence"],
        evidence_ids=report["evidence_ids"], steps=steps, rollback=rollback, verification=verification,
    )
    queries.set_incident_state(incident_id, "recommendation_proposed")

    try:
        pipeline = jenkins_client.trigger_pipeline(
            REMEDIATION_PIPELINE_JOB,
            {"recommendation_id": rec["id"], "incident_id": incident_id, "risk": risk},
        )
        queries.set_recommendation_approval(rec["id"], pipeline["queue_url"], "pending_approval")
        rec["approval_url"], rec["state"] = pipeline["queue_url"], "pending_approval"
    except jenkins_client.JenkinsNotConfigured:
        pass  # no JENKINS_* env vars — recommendation stays 'proposed', approval wiring is a later step

    return rec
