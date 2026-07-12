"""boip-core data access — incidents, evidence, and the change/topology
lookups the investigation logic ranks over. Same BOIP_DB_DSN as the collector."""

from __future__ import annotations

from psycopg.types.json import Jsonb

from ..collector.canonical import config_hash
from ..collector.db import get_conn


def create_incident(title: str, asset_name: str, source_alert: dict | None = None) -> dict:
    payload = dict(source_alert or {})
    payload["asset"] = asset_name
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO incident (title, state, source_alert)
               VALUES (%s, 'new', %s)
               RETURNING id, title, state, source_alert, opened_at, closed_at""",
            (title, Jsonb(payload)),
        )
        return _incident_row(cur.fetchone())


def get_incident(incident_id: int) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, title, state, source_alert, opened_at, closed_at
               FROM incident WHERE id = %s""",
            (incident_id,),
        )
        row = cur.fetchone()
        return _incident_row(row) if row else None


def list_incidents(limit: int = 50) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, title, state, source_alert, opened_at, closed_at
               FROM incident ORDER BY opened_at DESC LIMIT %s""",
            (limit,),
        )
        return [_incident_row(r) for r in cur.fetchall()]


def set_incident_state(incident_id: int, state: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE incident SET state = %s WHERE id = %s", (state, incident_id))


def find_asset_by_name(name: str) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, kind, name, source, source_ref FROM asset
               WHERE name = %s ORDER BY last_seen DESC LIMIT 1""",
            (name,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "kind": row[1], "name": row[2], "source": row[3], "source_ref": row[4]}


def one_hop_neighbors(asset_id: int) -> list[dict]:
    """Blast radius: everything this asset depends on and everything that depends on it."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.name, a.kind, e.relation, 'depends_on' AS direction
            FROM asset_edge e JOIN asset a ON a.id = e.child_id
            WHERE e.parent_id = %s
            UNION ALL
            SELECT a.id, a.name, a.kind, e.relation, 'depended_on_by' AS direction
            FROM asset_edge e JOIN asset a ON a.id = e.parent_id
            WHERE e.child_id = %s
            """,
            (asset_id, asset_id),
        )
        return [
            {"id": r[0], "name": r[1], "kind": r[2], "relation": r[3], "direction": r[4]}
            for r in cur.fetchall()
        ]


def changes_for_assets(asset_ids: list[int], since_hours: int) -> list[dict]:
    if not asset_ids:
        return []
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.asset_id, a.name, a.kind, c.detected_at, c.path, c.old_value, c.new_value
            FROM config_change c JOIN asset a ON a.id = c.asset_id
            WHERE c.asset_id = ANY(%s)
              AND c.detected_at > now() - make_interval(hours => %s)
            ORDER BY c.detected_at DESC
            """,
            (asset_ids, since_hours),
        )
        return [
            {
                "change_id": r[0], "asset_id": r[1], "asset_name": r[2], "asset_kind": r[3],
                "detected_at": r[4], "path": r[5], "old_value": r[6], "new_value": r[7],
            }
            for r in cur.fetchall()
        ]


def record_evidence(incident_id: int, kind: str, source_tool: str, content: dict) -> int:
    h = config_hash(content)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO evidence (incident_id, kind, source_tool, content, content_hash)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (incident_id, kind, source_tool, Jsonb(content), h),
        )
        return cur.fetchone()[0]


def list_evidence(incident_id: int) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, kind, source_tool, content, content_hash, collected_at
               FROM evidence WHERE incident_id = %s ORDER BY collected_at ASC""",
            (incident_id,),
        )
        return [
            {"id": r[0], "kind": r[1], "source_tool": r[2], "content": r[3],
             "content_hash": r[4], "collected_at": r[5]}
            for r in cur.fetchall()
        ]


def create_recommendation(
    incident_id: int, summary: str, risk: str, confidence: float,
    evidence_ids: list[int], steps: list[dict], rollback: list[dict], verification: list[dict],
) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO recommendation
               (incident_id, summary, risk, confidence, evidence_ids, steps, rollback, verification)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id, incident_id, summary, risk, confidence, evidence_ids, steps,
                         rollback, verification, awx_template_id, approval_url, state, outcome, created_at""",
            (incident_id, summary, risk, confidence, evidence_ids,
             Jsonb(steps), Jsonb(rollback), Jsonb(verification)),
        )
        return _recommendation_row(cur.fetchone())


def get_recommendations_for_incident(incident_id: int) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, incident_id, summary, risk, confidence, evidence_ids, steps,
                      rollback, verification, awx_template_id, approval_url, state, outcome, created_at
               FROM recommendation WHERE incident_id = %s ORDER BY created_at DESC""",
            (incident_id,),
        )
        return [_recommendation_row(r) for r in cur.fetchall()]


def set_recommendation_approval(recommendation_id: int, approval_url: str, state: str) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE recommendation SET approval_url = %s, state = %s WHERE id = %s",
            (approval_url, state, recommendation_id),
        )


def _recommendation_row(row) -> dict:
    return {
        "id": row[0], "incident_id": row[1], "summary": row[2], "risk": row[3],
        "confidence": float(row[4]) if row[4] is not None else None, "evidence_ids": row[5],
        "steps": row[6], "rollback": row[7], "verification": row[8],
        "awx_template_id": row[9], "approval_url": row[10], "state": row[11],
        "outcome": row[12], "created_at": row[13],
    }


def _incident_row(row) -> dict:
    return {
        "id": row[0], "title": row[1], "state": row[2], "source_alert": row[3],
        "opened_at": row[4], "closed_at": row[5],
    }
