"""Shared vSphere plumbing: connection from env vars and bulk
PropertyCollector fetches (one round-trip per page, never lazy per-object
attribute access — required both for 2,000-VM scale and for vcsim
compatibility with pyVmomi >= 9)."""

from __future__ import annotations

import atexit
import os
import ssl

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl  # noqa: F401  (vim re-exported for callers)


def connect():
    host = os.environ.get("VCENTER_HOST")
    user = os.environ.get("VCENTER_USER")
    pwd = os.environ.get("VCENTER_PASSWORD")
    port = int(os.environ.get("VCENTER_PORT", "443"))
    if not all([host, user, pwd]):
        raise SystemExit("Missing VCENTER_HOST / VCENTER_USER / VCENTER_PASSWORD")
    ctx = None
    if os.environ.get("VCENTER_INSECURE", "false").lower() in ("1", "true", "yes"):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=host, user=user, pwd=pwd, port=port, sslContext=ctx)
    atexit.register(Disconnect, si)
    return si


def collect(si, vimtype, pathset):
    """[(managed_object_ref, {prop_path: value}), ...] for all objects of vimtype."""
    content = si.RetrieveContent()
    view = content.viewManager.CreateContainerView(content.rootFolder, [vimtype], True)
    try:
        tspec = vmodl.query.PropertyCollector.TraversalSpec(
            name="tv", path="view", skip=False, type=type(view))
        ospec = vmodl.query.PropertyCollector.ObjectSpec(
            obj=view, skip=True, selectSet=[tspec])
        pspec = vmodl.query.PropertyCollector.PropertySpec(type=vimtype, pathSet=pathset)
        fspec = vmodl.query.PropertyCollector.FilterSpec(objectSet=[ospec], propSet=[pspec])
        pc = content.propertyCollector
        result = pc.RetrievePropertiesEx(
            [fspec], vmodl.query.PropertyCollector.RetrieveOptions())
        rows = []
        while result:
            for o in result.objects:
                rows.append((o.obj, {p.name: p.val for p in o.propSet}))
            if result.token:
                result = pc.ContinueRetrievePropertiesEx(result.token)
            else:
                break
        return rows
    finally:
        view.Destroy()  # leaked views degrade vpxd — always destroy


def moid(mor) -> str:
    """Stable source_ref for a managed object, e.g. 'vm-56'."""
    return mor._moId
