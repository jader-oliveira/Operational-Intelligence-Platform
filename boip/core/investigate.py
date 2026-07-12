"""The investigation logic: given an incident's asset, gather every config
change in its blast radius over the lookback window and rank them by how
plausibly each explains the incident.

Deterministic and explainable on purpose (ADR 0017 — no model dependency
before evidence). This is not a substitute for the HolmesGPT agent loop
(ADR 0013); it is the same evidence the agent's boip_changes toolset already
exposes, ranked into a report a human can read without an LLM in the loop.

Score = proximity (1.0 on the incident asset itself, 0.5 one hop away)
        x recency (changes right before the incident outrank stale ones).
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import queries

RECENCY_HALF_LIFE_HOURS = 6.0


def _recency_weight(detected_at: datetime, reference: datetime) -> float:
    hours = abs((reference - detected_at).total_seconds()) / 3600.0
    return 0.5 ** (hours / RECENCY_HALF_LIFE_HOURS)


def investigate(incident_id: int, lookback_hours: int = 24) -> dict:
    incident = queries.get_incident(incident_id)
    if incident is None:
        raise ValueError(f"incident {incident_id} not found")

    queries.set_incident_state(incident_id, "investigating")

    asset_name = incident["source_alert"].get("asset")
    target = queries.find_asset_by_name(asset_name) if asset_name else None
    if target is None:
        raise ValueError(f"asset not found for incident {incident_id}: {asset_name!r}")

    neighbors = queries.one_hop_neighbors(target["id"])
    neighbor_by_id = {n["id"]: n for n in neighbors}
    scope_ids = [target["id"], *neighbor_by_id.keys()]

    reference_time = incident["opened_at"]
    changes = queries.changes_for_assets(scope_ids, lookback_hours)

    ranked = []
    evidence_ids = []
    for ch in changes:
        proximity = 1.0 if ch["asset_id"] == target["id"] else 0.5
        weight = proximity * _recency_weight(ch["detected_at"], reference_time)
        neighbor = neighbor_by_id.get(ch["asset_id"])
        evidence_id = queries.record_evidence(
            incident_id, kind="config_change", source_tool="boip_core.investigate",
            content={
                "asset": ch["asset_name"], "asset_kind": ch["asset_kind"],
                "relation_to_incident_asset": "self" if proximity == 1.0 else neighbor["relation"],
                "detected_at": ch["detected_at"].isoformat(),
                "path": ch["path"], "old_value": ch["old_value"], "new_value": ch["new_value"],
                "score": round(weight, 4),
            },
        )
        evidence_ids.append(evidence_id)
        ranked.append({**ch, "score": weight, "evidence_id": evidence_id})

    ranked.sort(key=lambda c: c["score"], reverse=True)

    top = ranked[0] if ranked else None
    if top:
        summary = (
            f"Highest-ranked change: {top['asset_name']} ({top['asset_kind']}).{top['path']} "
            f"changed {top['old_value']!r} -> {top['new_value']!r} at "
            f"{top['detected_at'].isoformat()}, {_hours_before(top['detected_at'], reference_time)} "
            f"before the incident was opened."
        )
        confidence = round(min(top["score"], 1.0), 2)
    else:
        summary = f"No config changes found on {asset_name} or its neighbors in the last {lookback_hours}h."
        confidence = 0.0

    report = {
        "incident_id": incident_id,
        "asset": asset_name,
        "lookback_hours": lookback_hours,
        "summary": summary,
        "confidence": confidence,
        "blast_radius": [
            {"name": n["name"], "kind": n["kind"], "relation": n["relation"], "direction": n["direction"]}
            for n in neighbors
        ],
        "ranked_changes": [
            {
                "asset": c["asset_name"], "path": c["path"],
                "old_value": c["old_value"], "new_value": c["new_value"],
                "detected_at": c["detected_at"].isoformat(),
                "score": round(c["score"], 4), "evidence_id": c["evidence_id"],
            }
            for c in ranked
        ],
        "evidence_ids": evidence_ids,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    queries.record_evidence(incident_id, kind="investigation_report", source_tool="boip_core.investigate",
                             content=report)
    queries.set_incident_state(incident_id, "report_ready")
    return report


def _hours_before(t: datetime, reference: datetime) -> str:
    hours = (reference - t).total_seconds() / 3600.0
    return f"{hours:.1f}h" if hours >= 0 else f"{-hours:.1f}h after"
