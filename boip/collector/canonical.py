"""Canonicalization + diffing — the heart of the "what changed?" engine.

Rules that keep the diff signal clean (80% of collector quality lives here):

1. Snapshots contain *configuration and intent*, never runtime counters.
   Uptime, CPU MHz, memory usage, IP leases etc. are metrics, not config —
   they belong in Prometheus, not in config_snapshot.
2. Collections are keyed, not indexed. Disks/NICs are stored as dicts keyed
   by a stable identity (device label), so reordering never produces a diff
   and paths read as 'disks[disk-202-0].capacity_gb'.
3. Canonical JSON = sorted keys, compact separators -> stable sha256.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterator


def canonical_json(config: dict) -> str:
    return json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)


def config_hash(config: dict) -> str:
    return hashlib.sha256(canonical_json(config).encode()).hexdigest()


def flatten(obj: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    """Flatten nested dicts/lists to (path, scalar) pairs.

    dict  -> prefix.key
    list  -> prefix[i]        (avoid lists for identity-bearing collections;
                               use dicts keyed by stable ids instead — see rule 2)
    """
    if isinstance(obj, dict):
        if not obj:
            yield prefix, {}
        for k in sorted(obj):
            child = f"{prefix}.{k}" if prefix else str(k)
            yield from flatten(obj[k], child)
    elif isinstance(obj, list):
        if not obj:
            yield prefix, []
        for i, v in enumerate(obj):
            yield from flatten(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def diff_configs(old: dict, new: dict) -> list[dict]:
    """Return [{'path','old_value','new_value'}] for every changed leaf.

    old_value None + new_value set   -> key added
    old_value set  + new_value None  -> key removed
    """
    old_flat = dict(flatten(old))
    new_flat = dict(flatten(new))

    def _has_children(path: str, flat: dict) -> bool:
        return any(k.startswith(path + ".") or k.startswith(path + "[") for k in flat)

    changes = []
    for path in sorted(set(old_flat) | set(new_flat)):
        ov, nv = old_flat.get(path), new_flat.get(path)
        if ov == nv:
            continue
        # Suppress empty-container markers: '{} -> children appeared' (or the
        # reverse) is fully described by the child rows themselves.
        if ov in ({}, []) and nv is None and _has_children(path, new_flat):
            continue
        if nv in ({}, []) and ov is None and _has_children(path, old_flat):
            continue
        changes.append({"path": path, "old_value": ov, "new_value": nv})
    return changes


def keyed(items: list[dict], key_field: str) -> dict:
    """Convert a list of dicts into a dict keyed by a stable identity field,
    so element order can never generate a false diff (rule 2)."""
    out = {}
    for it in items:
        k = str(it.get(key_field) or f"unkeyed-{len(out)}")
        out[k] = {f: v for f, v in it.items() if f != key_field}
    return out
