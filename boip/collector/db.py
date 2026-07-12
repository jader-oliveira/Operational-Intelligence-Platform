"""Persistence for the collector: asset/edge upserts and the
snapshot-then-diff write path. DSN from env BOIP_DB_DSN, e.g.
  host=127.0.0.1 dbname=boip user=boip password=boip
"""

from __future__ import annotations

import os

import psycopg
from psycopg.types.json import Jsonb

from .canonical import canonical_json, config_hash, diff_configs


def get_conn():
    dsn = os.environ.get("BOIP_DB_DSN")
    if not dsn:
        raise SystemExit("Missing BOIP_DB_DSN")
    return psycopg.connect(dsn)


def upsert_asset(cur, kind, name, source, source_ref, labels=None) -> int:
    cur.execute(
        """
        INSERT INTO asset (kind, name, source, source_ref, labels)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source, source_ref)
        DO UPDATE SET name = EXCLUDED.name, kind = EXCLUDED.kind,
                      labels = EXCLUDED.labels, last_seen = now()
        RETURNING id
        """,
        (kind, name, source, source_ref, Jsonb(labels or {})),
    )
    return cur.fetchone()[0]


def upsert_edge(cur, parent_id: int, child_id: int, relation: str):
    cur.execute(
        """
        INSERT INTO asset_edge (parent_id, child_id, relation)
        VALUES (%s, %s, %s)
        ON CONFLICT (parent_id, child_id, relation)
        DO UPDATE SET last_seen = now()
        """,
        (parent_id, child_id, relation),
    )


def record_snapshot(cur, asset_id: int, config: dict) -> dict:
    """Store a snapshot only if config changed; diff against the previous one.

    Returns {'changed': bool, 'snapshot_id': int|None, 'changes': int}.
    """
    new_hash = config_hash(config)
    cur.execute(
        """SELECT id, config, config_hash FROM config_snapshot
           WHERE asset_id = %s ORDER BY taken_at DESC, id DESC LIMIT 1""",
        (asset_id,),
    )
    prev = cur.fetchone()

    if prev and prev[2] == new_hash:
        return {"changed": False, "snapshot_id": prev[0], "changes": 0}

    cur.execute(
        """INSERT INTO config_snapshot (asset_id, config, config_hash)
           VALUES (%s, %s::jsonb, %s) RETURNING id""",
        (asset_id, canonical_json(config), new_hash),
    )
    snap_id = cur.fetchone()[0]

    n_changes = 0
    if prev:
        prev_id, prev_config = prev[0], prev[1]
        for ch in diff_configs(prev_config, config):
            cur.execute(
                """INSERT INTO config_change
                   (asset_id, path, old_value, new_value, snapshot_before, snapshot_after)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (asset_id, ch["path"],
                 Jsonb(ch["old_value"]), Jsonb(ch["new_value"]),
                 prev_id, snap_id),
            )
            n_changes += 1
    return {"changed": True, "snapshot_id": snap_id, "changes": n_changes}
