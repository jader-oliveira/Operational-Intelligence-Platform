#!/usr/bin/env python3
"""
boip vcenter_tools — read-only vCenter query CLI for HolmesGPT toolsets.

Design rules (do not break these):
  * READ-ONLY. No method that mutates vCenter state is ever called.
  * Bulk PropertyCollector fetches, never per-object lazy attribute access.
    One round-trip for 2,000 VMs instead of 2,000; also required for vcsim
    compatibility with pyVmomi >= 9.x.
  * Bounded output. Every command caps list sizes and truncates strings,
    because output goes straight into an LLM context window.
  * JSON out, always. One JSON document on stdout; errors as JSON on stderr
    with exit code 1, so the agent can read failures too.
  * Credentials only via environment variables (VCENTER_HOST, VCENTER_USER,
    VCENTER_PASSWORD, VCENTER_PORT, VCENTER_INSECURE=true|false).

Usage examples:
  vcenter_tools.py check
  vcenter_tools.py list-vms --limit 100 --filter-name web --only-powered-on
  vcenter_tools.py vm-summary --name DC0_H0_VM0
  vcenter_tools.py vm-perf --name DC0_H0_VM0 --samples 30
  vcenter_tools.py host-summary
  vcenter_tools.py datastore-summary
  vcenter_tools.py events --minutes 120 --limit 50
  vcenter_tools.py events --minutes 240 --entity DC0_H0_VM0
  vcenter_tools.py alarms
  vcenter_tools.py snapshots
"""

import argparse
import atexit
import json
import os
import signal
import ssl
import sys

# Agents and shells often pipe output through head/truncation — exit quietly
# instead of stack-tracing when the reader closes the pipe.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
from datetime import datetime, timedelta, timezone

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl

MAX_STR = 300           # truncate any single string field
DEFAULT_LIST_CAP = 200  # hard ceiling on any list we return


# ---------------------------------------------------------------- utilities

def die(msg, detail=None):
    print(json.dumps({"error": msg,
                      "detail": str(detail)[:MAX_STR] if detail else None}),
          file=sys.stderr)
    sys.exit(1)


def out(payload):
    print(json.dumps(payload, default=str, ensure_ascii=False))


def trunc(s):
    if isinstance(s, str) and len(s) > MAX_STR:
        return s[:MAX_STR] + "...[truncated]"
    return s


def connect():
    host = os.environ.get("VCENTER_HOST")
    user = os.environ.get("VCENTER_USER")
    pwd = os.environ.get("VCENTER_PASSWORD")
    port = int(os.environ.get("VCENTER_PORT", "443"))
    if not all([host, user, pwd]):
        die("Missing VCENTER_HOST / VCENTER_USER / VCENTER_PASSWORD environment variables")
    ctx = None
    if os.environ.get("VCENTER_INSECURE", "false").lower() in ("1", "true", "yes"):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        si = SmartConnect(host=host, user=user, pwd=pwd, port=port, sslContext=ctx)
    except Exception as e:
        die(f"Cannot connect to vCenter {host}:{port}", e)
    atexit.register(Disconnect, si)
    return si


def collect(si, vimtype, pathset):
    """Bulk-fetch properties for every object of `vimtype`.

    Returns a list of (managed_object_ref, {prop_path: value}) tuples.
    Uses a ContainerView + PropertyCollector: single round-trip per page,
    which is the only pattern that behaves at 2,000-VM scale and the only
    one vcsim serves reliably with pyVmomi >= 9.
    """
    content = si.RetrieveContent()
    view = content.viewManager.CreateContainerView(
        content.rootFolder, [vimtype], True)
    try:
        tspec = vmodl.query.PropertyCollector.TraversalSpec(
            name="tv", path="view", skip=False, type=type(view))
        ospec = vmodl.query.PropertyCollector.ObjectSpec(
            obj=view, skip=True, selectSet=[tspec])
        pspec = vmodl.query.PropertyCollector.PropertySpec(
            type=vimtype, pathSet=pathset)
        fspec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=[ospec], propSet=[pspec])
        pc = content.propertyCollector
        opts = vmodl.query.PropertyCollector.RetrieveOptions()
        result, rows = pc.RetrievePropertiesEx([fspec], opts), []
        while result:
            for o in result.objects:
                rows.append((o.obj, {p.name: p.val for p in o.propSet}))
            if result.token:
                result = pc.ContinueRetrievePropertiesEx(result.token)
            else:
                break
        return rows
    finally:
        view.Destroy()   # leaked views degrade vpxd over time — always destroy


def name_map(si, vimtype):
    """{managed_object_ref: name} for cross-referencing hosts/datastores."""
    return {mor: props.get("name") for mor, props in collect(si, vimtype, ["name"])}


def find_vm(si, name, pathset):
    for mor, props in collect(si, vim.VirtualMachine, ["name"] + pathset):
        if props.get("name") == name:
            return mor, props
    die(f"VM not found: {name!r}. Use list-vms to see available VM names.")


# ------------------------------------------------------------ perf plumbing

# Counters chosen because each one answers a classic vSphere incident question.
VM_COUNTERS = {
    "cpu.usage.average":           ("cpu_usage_pct", 0.01),   # raw unit: 0.01%
    "cpu.ready.summation":         ("cpu_ready_ms", 1),       # ms per 20s sample
    "mem.usage.average":           ("mem_usage_pct", 0.01),
    "mem.vmmemctl.average":        ("mem_ballooned_kb", 1),   # >0 = host memory pressure
    "mem.swapped.average":         ("mem_swapped_kb", 1),
    "disk.maxTotalLatency.latest": ("disk_max_latency_ms", 1),
    "net.usage.average":           ("net_usage_kbps", 1),
}

HOST_COUNTERS = {
    "cpu.usage.average":           ("cpu_usage_pct", 0.01),
    "mem.usage.average":           ("mem_usage_pct", 0.01),
    "disk.maxTotalLatency.latest": ("disk_max_latency_ms", 1),
}


def query_realtime(si, entity, wanted, samples):
    """Query real-time (20s interval) stats; returns ({friendly: stats}, error)."""
    pm = si.RetrieveContent().perfManager
    cmap = {f"{c.groupInfo.key}.{c.nameInfo.key}.{c.rollupType}": c.key
            for c in pm.perfCounter}
    metric_ids, key_to_friendly = [], {}
    for cname, (friendly, factor) in wanted.items():
        key = cmap.get(cname)
        if key is None:
            continue   # counter absent on this vCenter version / simulator
        metric_ids.append(vim.PerformanceManager.MetricId(counterId=key, instance=""))
        key_to_friendly[key] = (friendly, factor, cname)
    if not metric_ids:
        return {}, "no matching performance counters available on this endpoint"
    spec = vim.PerformanceManager.QuerySpec(
        entity=entity, metricId=metric_ids, intervalId=20, maxSample=samples)
    try:
        results = pm.QueryPerf(querySpec=[spec])
    except Exception as e:
        return {}, f"perf query failed: {e}"
    series = {}
    for res in results or []:
        for val in res.value:
            friendly, factor, cname = key_to_friendly.get(
                val.id.counterId, (None, 1, None))
            if friendly is None:
                continue
            pts = [v * factor for v in val.value if v >= 0]   # -1 = no data
            if not pts:
                continue
            entry = {
                "counter": cname,
                "samples": len(pts),
                "interval_seconds": 20,
                "latest": round(pts[-1], 2),
                "avg": round(sum(pts) / len(pts), 2),
                "max": round(max(pts), 2),
            }
            # cpu.ready is ms of ready time per 20s sample; also express as %
            if cname == "cpu.ready.summation":
                entry["ready_pct_of_interval_avg"] = round(
                    entry["avg"] / (20 * 1000) * 100, 2)
                entry["ready_pct_of_interval_max"] = round(
                    entry["max"] / (20 * 1000) * 100, 2)
            series[friendly] = entry
    if not series:
        return {}, "perf query returned no data (normal on vcsim; real vCenter returns samples)"
    return series, None


# ---------------------------------------------------------------- commands

def cmd_check(si, args):
    about = si.RetrieveContent().about
    out({"status": "ok", "product": about.fullName, "api_version": about.apiVersion})


VM_LIST_PROPS = [
    "name", "summary.runtime.powerState", "summary.config.guestFullName",
    "summary.config.numCpu", "summary.config.memorySizeMB", "runtime.host",
    "summary.overallStatus", "summary.quickStats.guestHeartbeatStatus",
]


def cmd_list_vms(si, args):
    hosts = name_map(si, vim.HostSystem)
    rows = []
    for _, p in collect(si, vim.VirtualMachine, VM_LIST_PROPS):
        power = str(p.get("summary.runtime.powerState", ""))
        name = p.get("name", "")
        if args.only_powered_on and power != "poweredOn":
            continue
        if args.filter_name and args.filter_name.lower() not in name.lower():
            continue
        rows.append({
            "name": name,
            "power": power,
            "guest_os": trunc(p.get("summary.config.guestFullName")),
            "cpus": p.get("summary.config.numCpu"),
            "memory_mb": p.get("summary.config.memorySizeMB"),
            "host": hosts.get(p.get("runtime.host")),
            "overall_status": str(p.get("summary.overallStatus", "")),  # green/yellow/red
            "guest_heartbeat": str(p.get("summary.quickStats.guestHeartbeatStatus", "")),
        })
    cap = min(args.limit, DEFAULT_LIST_CAP)
    out({"total_matching": len(rows), "returned": min(len(rows), cap),
         "vms": rows[:cap]})


VM_DETAIL_PROPS = [
    "summary.runtime.powerState", "summary.runtime.connectionState",
    "runtime.host", "datastore", "summary.config.guestFullName",
    "guest.toolsStatus", "guest.ipAddress", "summary.config.numCpu",
    "summary.config.memorySizeMB", "summary.quickStats",
    "summary.overallStatus", "configIssue", "config.hardware.device",
    "snapshot",
]


def _walk_snaps(snap_list, acc):
    for s in snap_list or []:
        acc.append(s)
        _walk_snaps(s.childSnapshotList, acc)


def cmd_vm_summary(si, args):
    _, p = find_vm(si, args.name, VM_DETAIL_PROPS)
    hosts = name_map(si, vim.HostSystem)
    dstores = name_map(si, vim.Datastore)

    disks, nics = [], []
    for dev in (p.get("config.hardware.device") or []):
        if isinstance(dev, vim.vm.device.VirtualDisk):
            disks.append({
                "label": dev.deviceInfo.label if dev.deviceInfo else None,
                "capacity_gb": round(dev.capacityInKB / 1024 / 1024, 1)
                if dev.capacityInKB else None,
                "file": trunc(getattr(dev.backing, "fileName", None)),
            })
        elif isinstance(dev, vim.vm.device.VirtualEthernetCard):
            nics.append({
                "label": dev.deviceInfo.label if dev.deviceInfo else None,
                "network": trunc(getattr(dev.backing, "deviceName", None))
                if dev.backing else None,
                "connected": dev.connectable.connected if dev.connectable else None,
            })

    q = p.get("summary.quickStats")
    snap_acc = []
    snap = p.get("snapshot")
    if snap:
        _walk_snaps(snap.rootSnapshotList, snap_acc)

    out({
        "name": args.name,
        "power": str(p.get("summary.runtime.powerState", "")),
        "connection_state": str(p.get("summary.runtime.connectionState", "")),
        "host": hosts.get(p.get("runtime.host")),
        "datastores": [dstores.get(d, str(d)) for d in (p.get("datastore") or [])][:10],
        "guest_os": trunc(p.get("summary.config.guestFullName")),
        "vmware_tools": str(p.get("guest.toolsStatus", "")) or None,
        "ip_address": p.get("guest.ipAddress"),
        "cpus": p.get("summary.config.numCpu"),
        "memory_mb": p.get("summary.config.memorySizeMB"),
        "quick_stats": {
            "overall_cpu_mhz": q.overallCpuUsage,
            "guest_mem_usage_mb": q.guestMemoryUsage,
            "host_mem_usage_mb": q.hostMemoryUsage,
            "ballooned_mb": q.balloonedMemory,   # >0 = host reclaiming memory
            "swapped_mb": q.swappedMemory,
            "uptime_seconds": q.uptimeSeconds,
        } if q else None,
        "overall_status": str(p.get("summary.overallStatus", "")),
        "config_issues": [trunc(str(i.fullFormattedMessage))
                          for i in (p.get("configIssue") or [])][:5],
        "disks": disks[:10],
        "nics": nics[:10],
        "snapshot_count": len(snap_acc),
        "snapshots": [{"name": trunc(s.name), "created": str(s.createTime)}
                      for s in snap_acc][:10],
    })


def cmd_vm_perf(si, args):
    mor, _ = find_vm(si, args.name, [])
    series, err = query_realtime(si, mor, VM_COUNTERS, args.samples)
    payload = {
        "vm": args.name,
        "window_seconds": args.samples * 20,
        "metrics": series,
        "interpretation_hints": {
            "cpu_ready": "ready_pct_of_interval > 5% sustained = CPU contention on the host",
            "mem_ballooned_kb": "> 0 = host memory pressure, guest memory being reclaimed",
            "disk_max_latency_ms": "> 20-30ms sustained = storage bottleneck, check the datastore",
        },
    }
    if err:
        payload["warning"] = err
    out(payload)


HOST_PROPS = [
    "name", "summary.runtime.connectionState", "summary.runtime.inMaintenanceMode",
    "summary.runtime.powerState", "summary.overallStatus", "summary.hardware",
    "summary.quickStats", "summary.config.product", "vm",
]


def cmd_host_summary(si, args):
    # count running VMs per host with one bulk VM fetch
    running_by_host = {}
    for _, vp in collect(si, vim.VirtualMachine,
                         ["runtime.host", "summary.runtime.powerState"]):
        if str(vp.get("summary.runtime.powerState")) == "poweredOn":
            h = vp.get("runtime.host")
            running_by_host[h] = running_by_host.get(h, 0) + 1

    rows = []
    for mor, p in collect(si, vim.HostSystem, HOST_PROPS):
        if args.name and p.get("name") != args.name:
            continue
        hw, q = p.get("summary.hardware"), p.get("summary.quickStats")
        prod = p.get("summary.config.product")
        total_mem_mb = round(hw.memorySize / 1024 / 1024) if hw and hw.memorySize else None
        row = {
            "name": p.get("name"),
            "connection_state": str(p.get("summary.runtime.connectionState", "")),
            "in_maintenance_mode": p.get("summary.runtime.inMaintenanceMode"),
            "power_state": str(p.get("summary.runtime.powerState", "")),
            "overall_status": str(p.get("summary.overallStatus", "")),
            "model": trunc(f"{hw.vendor} {hw.model}") if hw else None,
            "cpu_cores": hw.numCpuCores if hw else None,
            "cpu_usage_mhz": q.overallCpuUsage if q else None,
            "cpu_total_mhz": (hw.cpuMhz * hw.numCpuCores) if hw else None,
            "mem_usage_mb": q.overallMemoryUsage if q else None,
            "mem_total_mb": total_mem_mb,
            "uptime_seconds": q.uptime if q else None,
            "vms_running": running_by_host.get(mor, 0),
            "esxi_version": prod.fullName if prod else None,
        }
        if row["mem_usage_mb"] and total_mem_mb:
            row["mem_usage_pct"] = round(row["mem_usage_mb"] / total_mem_mb * 100, 1)
        if row["cpu_usage_mhz"] and row["cpu_total_mhz"]:
            row["cpu_usage_pct"] = round(row["cpu_usage_mhz"] / row["cpu_total_mhz"] * 100, 1)
        if args.with_perf:
            series, err = query_realtime(si, mor, HOST_COUNTERS, args.samples)
            row["perf"] = series or {"warning": err}
        rows.append(row)
    if args.name and not rows:
        die(f"Host not found: {args.name!r}")
    out({"hosts": rows[:DEFAULT_LIST_CAP]})


def cmd_datastore_summary(si, args):
    rows = []
    for _, p in collect(si, vim.Datastore, ["name", "summary", "host", "vm"]):
        if args.name and p.get("name") != args.name:
            continue
        s = p.get("summary")
        cap_gb = round(s.capacity / 1024**3, 1) if s and s.capacity else 0
        free_gb = round(s.freeSpace / 1024**3, 1) if s and s.freeSpace else 0
        rows.append({
            "name": p.get("name"),
            "type": s.type if s else None,
            "accessible": s.accessible if s else None,
            "capacity_gb": cap_gb,
            "free_gb": free_gb,
            "used_pct": round((cap_gb - free_gb) / cap_gb * 100, 1) if cap_gb else None,
            "maintenance_mode": s.maintenanceMode if s else None,
            "hosts_mounted": len(p.get("host") or []),
            "vms_on_datastore": len(p.get("vm") or []),
        })
    if args.name and not rows:
        die(f"Datastore not found: {args.name!r}")
    rows.sort(key=lambda r: -(r["used_pct"] or 0))
    out({"datastores": rows[:DEFAULT_LIST_CAP],
         "hint": "For per-VM storage latency use vm-perf (disk_max_latency_ms)."})


def cmd_events(si, args):
    em = si.RetrieveContent().eventManager
    now = datetime.now(timezone.utc)
    time_spec = vim.event.EventFilterSpec.ByTime(
        beginTime=now - timedelta(minutes=args.minutes), endTime=now)
    fspec = vim.event.EventFilterSpec(time=time_spec)
    if args.entity:
        mor, _ = find_vm(si, args.entity, [])
        fspec.entity = vim.event.EventFilterSpec.ByEntity(
            entity=mor, recursion=vim.event.EventFilterSpec.RecursionOption.self)
    try:
        events = em.QueryEvents(fspec) or []
    except Exception as e:
        die("Event query failed", e)
    rows = [{
        "time": str(ev.createdTime),
        "type": type(ev).__name__.split(".")[-1],
        "user": getattr(ev, "userName", None) or None,
        "entity": (ev.vm.name if getattr(ev, "vm", None) else
                   (ev.host.name if getattr(ev, "host", None) else None)),
        "message": trunc(ev.fullFormattedMessage),
    } for ev in events]
    rows.sort(key=lambda r: r["time"], reverse=True)
    cap = min(args.limit, DEFAULT_LIST_CAP)
    out({"window_minutes": args.minutes, "total_events": len(rows),
         "returned": min(len(rows), cap), "events": rows[:cap]})


def cmd_alarms(si, args):
    content = si.RetrieveContent()
    rows = []
    for st in (content.rootFolder.triggeredAlarmState or []):
        alarm_name = None
        try:
            alarm_name = st.alarm.info.name if st.alarm else None
        except Exception:
            pass
        entity_name = None
        try:
            entity_name = st.entity.name if st.entity else None
        except Exception:
            pass
        rows.append({
            "alarm": trunc(alarm_name),
            "entity": entity_name,
            "status": str(st.overallStatus),   # yellow / red
            "time": str(st.time),
            "acknowledged": st.acknowledged,
        })
    out({"triggered_alarms": rows[:DEFAULT_LIST_CAP]})


def cmd_snapshots(si, args):
    rows = []
    for _, p in collect(si, vim.VirtualMachine, ["name", "snapshot"]):
        snap = p.get("snapshot")
        if not snap:
            continue
        acc = []
        _walk_snaps(snap.rootSnapshotList, acc)
        for s in acc:
            age_days = (datetime.now(timezone.utc) - s.createTime).days
            rows.append({"vm": p.get("name"), "snapshot": trunc(s.name),
                         "created": str(s.createTime), "age_days": age_days,
                         "description": trunc(s.description) or None})
    rows.sort(key=lambda r: -r["age_days"])
    out({"total_snapshots": len(rows),
         "snapshots": rows[:DEFAULT_LIST_CAP],
         "hint": "Old snapshots (age_days > 3) grow delta files and degrade "
                 "storage performance; they are a classic latency root cause."})


# ------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(
        description="Read-only vCenter query tool (boip week 1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="verify connectivity, print vCenter version")

    sp = sub.add_parser("list-vms")
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--filter-name", default=None)
    sp.add_argument("--only-powered-on", action="store_true")

    sp = sub.add_parser("vm-summary")
    sp.add_argument("--name", required=True)

    sp = sub.add_parser("vm-perf")
    sp.add_argument("--name", required=True)
    sp.add_argument("--samples", type=int, default=30,
                    help="number of 20s real-time samples (30 = last 10 minutes)")

    sp = sub.add_parser("host-summary")
    sp.add_argument("--name", default=None)
    sp.add_argument("--with-perf", action="store_true")
    sp.add_argument("--samples", type=int, default=30)

    sp = sub.add_parser("datastore-summary")
    sp.add_argument("--name", default=None)

    sp = sub.add_parser("events")
    sp.add_argument("--minutes", type=int, default=60)
    sp.add_argument("--entity", default=None, help="VM name to scope events to")
    sp.add_argument("--limit", type=int, default=50)

    sub.add_parser("alarms")
    sub.add_parser("snapshots")

    args = p.parse_args()
    si = connect()
    {
        "check": cmd_check,
        "list-vms": cmd_list_vms,
        "vm-summary": cmd_vm_summary,
        "vm-perf": cmd_vm_perf,
        "host-summary": cmd_host_summary,
        "datastore-summary": cmd_datastore_summary,
        "events": cmd_events,
        "alarms": cmd_alarms,
        "snapshots": cmd_snapshots,
    }[args.cmd](si, args)


if __name__ == "__main__":
    main()
