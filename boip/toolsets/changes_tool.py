#!/usr/bin/env python3
"""boip changes_tool — query the change history and topology for HolmesGPT.

Read-only against the BOIP database (BOIP_DB_DSN env var). JSON on stdout.

  changes_tool.py changes --hours 24 [--asset NAME] [--limit 100]
  changes_tool.py topology --asset NAME
"""

import argparse
import json
import os
import signal
import sys

import psycopg

signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def die(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


def conn():
    dsn = os.environ.get("BOIP_DB_DSN")
    if not dsn:
        die("Missing BOIP_DB_DSN")
    return psycopg.connect(dsn)


def cmd_changes(args):
    q = """
        SELECT a.name, a.kind, c.detected_at, c.path, c.old_value, c.new_value
        FROM config_change c JOIN asset a ON a.id = c.asset_id
        WHERE c.detected_at > now() - make_interval(hours => %s)
    """
    params = [args.hours]
    if args.asset:
        q += " AND a.name = %s"
        params.append(args.asset)
    q += " ORDER BY c.detected_at DESC LIMIT %s"
    params.append(min(args.limit, 200))
    with conn() as c, c.cursor() as cur:
        cur.execute(q, params)
        rows = [{"asset": r[0], "kind": r[1], "detected_at": str(r[2]),
                 "path": r[3], "old_value": r[4], "new_value": r[5]}
                for r in cur.fetchall()]
    print(json.dumps({
        "window_hours": args.hours,
        "asset_filter": args.asset,
        "changes": rows,
        "note": ("detected_at is when the collector observed the change; the real "
                 "change happened between the previous collector run and this one. "
                 "Correlate with vCenter events for the exact time and user."),
    }, default=str))


def cmd_topology(args):
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT id, kind FROM asset WHERE name = %s ORDER BY last_seen DESC LIMIT 1",
                    (args.asset,))
        row = cur.fetchone()
        if not row:
            die(f"Asset not found: {args.asset!r}")
        aid, kind = row
        cur.execute("""
            SELECT 'depends_on' AS direction, e.relation, a.name, a.kind
            FROM asset_edge e JOIN asset a ON a.id = e.child_id
            WHERE e.parent_id = %s
            UNION ALL
            SELECT 'depended_on_by', e.relation, a.name, a.kind
            FROM asset_edge e JOIN asset a ON a.id = e.parent_id
            WHERE e.child_id = %s
            ORDER BY 1, 2, 3
        """, (aid, aid))
        edges = [{"direction": r[0], "relation": r[1], "name": r[2], "kind": r[3]}
                 for r in cur.fetchall()][:200]
    print(json.dumps({
        "asset": args.asset, "kind": kind, "edges": edges,
        "note": ("depends_on = things this asset runs on / is stored on. "
                 "depended_on_by = blast radius: assets affected if this one fails."),
    }))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("changes")
    sp.add_argument("--hours", type=int, default=24)
    sp.add_argument("--asset", default=None)
    sp.add_argument("--limit", type=int, default=100)
    sp = sub.add_parser("topology")
    sp.add_argument("--asset", required=True)
    args = p.parse_args()
    {"changes": cmd_changes, "topology": cmd_topology}[args.cmd](args)


if __name__ == "__main__":
    main()
