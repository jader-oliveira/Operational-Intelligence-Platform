"""VMware collector: one run = inventory upsert + canonical config snapshot
per VM/host/datastore + topology edges + diffs vs previous snapshot.

What goes in a snapshot (and what deliberately does not) is the whole game:
configuration and intent only — power state, sizing, placement, devices,
snapshot inventory. Never runtime counters (uptime, usage, heartbeats):
those are metrics and belong in Prometheus, not in the change history.
"""

from __future__ import annotations

from pyVmomi import vim

from .canonical import keyed
from .db import get_conn, record_snapshot, upsert_asset, upsert_edge
from .vsphere import collect, connect, moid

VM_PROPS = [
    "name", "summary.runtime.powerState", "summary.config.numCpu",
    "summary.config.memorySizeMB", "summary.config.guestFullName",
    "config.template", "runtime.host", "datastore",
    "config.hardware.device", "snapshot",
]
HOST_PROPS = [
    "name", "summary.config.product", "summary.hardware",
    "summary.runtime.inMaintenanceMode", "summary.runtime.connectionState",
    "parent",
]
DS_PROPS = ["name", "summary"]


def _vm_config(props, host_names, ds_names):
    disks, nics = [], []
    for dev in (props.get("config.hardware.device") or []):
        if isinstance(dev, vim.vm.device.VirtualDisk):
            disks.append({
                "label": dev.deviceInfo.label if dev.deviceInfo else None,
                "capacity_gb": round(dev.capacityInKB / 1024 / 1024, 1)
                if dev.capacityInKB else None,
                "file": getattr(dev.backing, "fileName", None),
            })
        elif isinstance(dev, vim.vm.device.VirtualEthernetCard):
            nics.append({
                "label": dev.deviceInfo.label if dev.deviceInfo else None,
                "network": getattr(dev.backing, "deviceName", None)
                if dev.backing else None,
            })
    snaps = []

    def walk(lst):
        for s in lst or []:
            snaps.append({"label": s.name, "created": str(s.createTime)})
            walk(s.childSnapshotList)

    if props.get("snapshot"):
        walk(props["snapshot"].rootSnapshotList)

    return {
        "power_state": str(props.get("summary.runtime.powerState", "")),
        "cpus": props.get("summary.config.numCpu"),
        "memory_mb": props.get("summary.config.memorySizeMB"),
        "guest_os": props.get("summary.config.guestFullName"),
        "is_template": bool(props.get("config.template")),
        "host": host_names.get(props.get("runtime.host")),
        "datastores": sorted(ds_names.get(d, str(d))
                             for d in (props.get("datastore") or [])),
        "disks": keyed(disks, "label"),        # keyed by identity, not index
        "nics": keyed(nics, "label"),
        "snapshots": keyed(snaps, "label"),
    }


def _host_config(props):
    hw = props.get("summary.hardware")
    prod = props.get("summary.config.product")
    return {
        "esxi_version": prod.fullName if prod else None,
        "model": f"{hw.vendor} {hw.model}" if hw else None,
        "cpu_cores": hw.numCpuCores if hw else None,
        "memory_total_mb": round(hw.memorySize / 1024 / 1024)
        if hw and hw.memorySize else None,
        "in_maintenance_mode": bool(props.get("summary.runtime.inMaintenanceMode")),
        "connection_state": str(props.get("summary.runtime.connectionState", "")),
    }


def _ds_config(props):
    s = props.get("summary")
    return {
        "type": s.type if s else None,
        "capacity_gb": round(s.capacity / 1024**3, 1) if s and s.capacity else None,
        "accessible": bool(s.accessible) if s else None,
        "maintenance_mode": s.maintenanceMode if s else None,
    }


def run() -> dict:
    si = connect()
    stats = {"assets": 0, "snapshots_written": 0, "changes_detected": 0, "edges": 0}

    hosts = collect(si, vim.HostSystem, HOST_PROPS)
    dstores = collect(si, vim.Datastore, DS_PROPS)
    vms = collect(si, vim.VirtualMachine, VM_PROPS)
    host_names = {mor: p.get("name") for mor, p in hosts}
    ds_names = {mor: p.get("name") for mor, p in dstores}

    with get_conn() as conn, conn.cursor() as cur:
        host_ids, ds_ids = {}, {}

        for mor, p in hosts:
            aid = upsert_asset(cur, "host", p["name"], "vmware", moid(mor))
            host_ids[mor] = aid
            r = record_snapshot(cur, aid, _host_config(p))
            stats["snapshots_written"] += int(r["changed"])
            stats["changes_detected"] += r["changes"]

        for mor, p in dstores:
            aid = upsert_asset(cur, "datastore", p["name"], "vmware", moid(mor))
            ds_ids[mor] = aid
            r = record_snapshot(cur, aid, _ds_config(p))
            stats["snapshots_written"] += int(r["changed"])
            stats["changes_detected"] += r["changes"]

        for mor, p in vms:
            aid = upsert_asset(cur, "vm", p["name"], "vmware", moid(mor))
            r = record_snapshot(cur, aid, _vm_config(p, host_names, ds_names))
            stats["snapshots_written"] += int(r["changed"])
            stats["changes_detected"] += r["changes"]
            h = p.get("runtime.host")
            if h in host_ids:
                upsert_edge(cur, aid, host_ids[h], "runs_on")
                stats["edges"] += 1
            for d in (p.get("datastore") or []):
                if d in ds_ids:
                    upsert_edge(cur, aid, ds_ids[d], "stored_on")
                    stats["edges"] += 1

        stats["assets"] = len(hosts) + len(dstores) + len(vms)
        conn.commit()
    return stats
