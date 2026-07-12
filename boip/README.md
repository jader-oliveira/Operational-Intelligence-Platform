# boip — collector and change engine (weeks 2–3 of the MVP plan)

## What this is

The versioned configuration history that answers "what changed before the incident?" —
the highest-value question in infrastructure RCA and BOIP's core differentiator.

One collector run = inventory upsert + canonical config snapshot per VM/host/datastore +
topology edges + structured diffs vs the previous snapshot. Idempotent: a run with no
real changes writes nothing.

## Layout

```
boip/
├── schema.sql                 # the 7 tables that carry the whole MVP
├── collector/
│   ├── canonical.py           # canonical JSON, hashing, keyed collections, diff engine
│   ├── vsphere.py             # connection + bulk PropertyCollector helpers
│   ├── vmware.py              # the VMware collector
│   ├── db.py                  # upserts + snapshot-then-diff write path
│   └── cli.py                 # python -m boip.collector.cli vmware
└── toolsets/
    ├── changes_tool.py        # read-only query CLI (changes / topology)
    └── boip_changes_toolset.yaml   # HolmesGPT toolset wrapping it
```

## Quick start

```bash
pip install -r requirements.txt
export BOIP_DB_DSN="host=127.0.0.1 dbname=boip user=boip password=boip"
export VCENTER_HOST=... VCENTER_USER=... VCENTER_PASSWORD=... VCENTER_INSECURE=true
psql "$BOIP_DB_DSN" -f schema.sql
python -m boip.collector.cli vmware          # run from the repo root
# schedule: cron/systemd timer/K8s CronJob every 15-60 min
```

Then load the toolset into HolmesGPT alongside the week-1 vCenter toolset:

```bash
export BOIP_TOOLS_DIR=$(pwd)/boip/toolsets
holmes ask "what changed in my environment in the last 24 hours?" \
  -t week1/boip_vmware_toolset.yaml -t boip/toolsets/boip_changes_toolset.yaml
```

## Design rules (from `collector/canonical.py` — read them before extending)

1. Snapshots contain configuration and intent, never runtime counters.
2. Collections are keyed by stable identity (device label), never list index —
   reordering must never produce a diff.
3. Canonical JSON (sorted keys) hashed with sha256; identical hash = no write.

## Validated (2026-07-12, vcsim v0.53 + pyVmomi 9.1 + PostgreSQL 16)

- Baseline run: 22 assets, 22 snapshots, 32 edges, 0 changes.
- Immediate re-run: 0 snapshots written (idempotency / zero diff noise).
- After `govc vm.change -m 128 -c 2`, `vm.power -off`, `snapshot.create`:
  exactly 4 change rows — cpus 1→2, memory_mb 32→128, power_state
  poweredOn→poweredOff, snapshots.pre-maintenance.created added.
- Empty-container flatten artifacts suppressed by design.

## Next (week 4–5)

`boip-core` FastAPI: AlertManager webhook → incident row → HolmesGPT investigation with
these toolsets → evidence + report persisted → Slack/Teams notification.
