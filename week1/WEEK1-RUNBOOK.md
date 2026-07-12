# Week 1 Runbook — Prove the Loop, Ugly

**Objective:** by day 7, HolmesGPT answers a VMware incident question with an evidence-cited
root cause, using your own custom toolset, against both a simulator and a real vCenter.
This de-risks the entire BOIP rebuild in seven days.

**Go/no-go decision at the end.** Scoring sheet in §Day 7. Don't polish anything this week —
speed of learning is the only metric.

**Files in this kit:**
- `vcenter_tools.py` — read-only pyVmomi query CLI (validated against vcsim v0.53 + pyVmomi 9.1)
- `boip_vmware_toolset.yaml` — HolmesGPT toolset wrapping it
- `env.example` — environment template

---

## Day 1 — HolmesGPT baseline on Kubernetes (your OKD homelab)

Goal: see what "good" looks like on the terrain Holmes knows best, before you judge it on VMware.

```bash
# Install (pick one)
pipx install holmesgpt            # or: pip install holmesgpt / brew install holmesgpt
holmes version

export ANTHROPIC_API_KEY=sk-ant-...   # strong API model first; local models are week 8

# Sanity: point kubectl at your OKD cluster, then
holmes ask "which pods are unhealthy in this cluster and why?"
```

Break something on purpose:

```bash
kubectl create ns boip-lab
kubectl -n boip-lab create deployment crash --image=busybox -- /bin/sh -c "exit 1"
sleep 60
holmes ask "why is the crash deployment in namespace boip-lab failing?"
```

**Watch for (this is your quality bar for the rest of the week):**
- Does it call tools before concluding, or guess?
- Does every claim trace to a tool output (logs, events, describe)?
- How many tool calls / how long / rough token cost per investigation?

Write these three observations down. You'll compare VMware answers against them.

---

## Day 2 — vcsim + validate the query tool

vcsim is VMware's official vCenter simulator (from the govmomi project). It speaks the real
SOAP API — the same `vcenter_tools.py` runs unmodified against it and against production.

```bash
# Get vcsim + govc (govc is your fault-injection remote control for the sim)
V=v0.53.0
curl -sLO https://github.com/vmware/govmomi/releases/download/$V/vcsim_Linux_x86_64.tar.gz
curl -sLO https://github.com/vmware/govmomi/releases/download/$V/govc_Linux_x86_64.tar.gz
tar xzf vcsim_Linux_x86_64.tar.gz vcsim && tar xzf govc_Linux_x86_64.tar.gz govc
sudo mv vcsim govc /usr/local/bin/

# Simulated estate: 1 DC, 1 cluster, 3 hosts, 8 VMs, 2 datastores
vcsim -l 127.0.0.1:8989 -dc 1 -cluster 1 -host 3 -vm 8 -ds 2 &

# Install the tool
sudo mkdir -p /opt/boip && sudo cp vcenter_tools.py /opt/boip/
pip install pyvmomi          # tested with 9.1.0

cp env.example .env && set -a; source .env; set +a

# Validate every subcommand
python3 /opt/boip/vcenter_tools.py check
python3 /opt/boip/vcenter_tools.py list-vms --limit 5
python3 /opt/boip/vcenter_tools.py vm-summary --name DC0_H0_VM0
python3 /opt/boip/vcenter_tools.py vm-perf --name DC0_H0_VM0
python3 /opt/boip/vcenter_tools.py host-summary
python3 /opt/boip/vcenter_tools.py datastore-summary
python3 /opt/boip/vcenter_tools.py events --minutes 60
python3 /opt/boip/vcenter_tools.py alarms
python3 /opt/boip/vcenter_tools.py snapshots
```

Every command must return clean JSON. (vcsim even serves realistic perf samples, so
`vm-perf` returns real-looking cpu_ready / latency numbers.)

**Engineering note baked into the tool:** it uses bulk PropertyCollector fetches, never lazy
per-object attribute access. That's one API round-trip for 2,000 VMs instead of 2,000, and
it's also the only pattern pyVmomi ≥ 9 serves reliably against vcsim. Keep that pattern for
every collector you write in weeks 2–3.

---

## Day 3 — Wire the toolset, first AI investigation, first fault injection

```bash
set -a; source .env; set +a

# Discovery questions
holmes ask "give me an overview of the health of my vmware environment" \
  -t boip_vmware_toolset.yaml

holmes ask "which datastore is fullest and which VMs are on it?" \
  -t boip_vmware_toolset.yaml
```

Now inject a fault into the simulator with govc and see if Holmes finds it:

```bash
export GOVC_URL="https://user:pass@127.0.0.1:8989/sdk" GOVC_INSECURE=1

govc vm.power -off DC0_H0_VM1        # kill a VM

holmes ask "users report the service on DC0_H0_VM1 is unreachable. Investigate and \
give me the root cause with evidence." -t boip_vmware_toolset.yaml
```

Expected: Holmes calls `vcenter_vm_summary` and/or `vcenter_events`, finds the poweredOff
state and the power-off event (with timestamp and user), and cites both. If it instead
answers from general knowledge without calling tools, your tool `description` fields need
sharpening — that's the tuning loop for today. Iterate on descriptions, not on code.

---

## Day 4 — Real vCenter, read-only service account

Get access to a test/lower-risk vCenter (work test environment is fine — this is exactly the
"read-only collection by default" principle from your own ADR-0001).

Ask your vCenter admin (or do it yourself) for:

1. A dedicated local SSO user, e.g. `svc-boip-ro@vsphere.local` (dedicated account = clean
   audit trail; every query shows up under this identity in vCenter logs).
2. The **built-in "Read-only" role**, granted at the datacenter or cluster level,
   **with "propagate to children"**. That's sufficient for everything the tool does:
   inventory, perf counters, events, alarms, snapshots. No custom role needed for week 1.
3. Network reachability to vCenter 443 from wherever holmes runs.

```bash
# Switch .env to the real target (see commented block in env.example), then:
python3 /opt/boip/vcenter_tools.py check
python3 /opt/boip/vcenter_tools.py list-vms --limit 10
```

If `check` passes and `list-vms` shows real VMs, day 4 is done. Note how long `list-vms`
takes on the real estate — that's your first scale datapoint.

---

## Day 5 — Real investigations, quality notes

Ask 5 real questions about the environment, the kind an engineer would actually ask:

```bash
holmes ask "are any ESXi hosts under memory pressure right now?" -t boip_vmware_toolset.yaml
holmes ask "which VMs have snapshots older than 3 days and what risk does that pose?" -t boip_vmware_toolset.yaml
holmes ask "what changed in this environment in the last 24 hours?" -t boip_vmware_toolset.yaml   # use --minutes 1440
holmes ask "is VM <real-vm-name> healthy? check performance, config issues and recent events" -t boip_vmware_toolset.yaml
holmes ask "which datastores are above 80% and which VMs would be affected if one fills up?" -t boip_vmware_toolset.yaml
```

For each, score in a notes file: tools called (right ones? wasted calls?), claims cited vs
asserted, factual errors, wall-clock time, and whether a colleague would trust the answer.
This file becomes your go/no-go evidence and, later, your first golden-case ideas.

---

## Day 6 — Staged incident on a real test VM

Pick a disposable test VM and create a realistic fault, e.g.:

- **Snapshot + load:** take 2–3 snapshots (via the normal UI/PowerCLI — your tool stays
  read-only), then run `stress-ng --io 4 --hdd 2` or a big `dd` inside the guest.
- Or **CPU contention:** `stress-ng --cpu $(nproc)` on 2–3 VMs sharing one host.

Wait 10+ minutes so real-time counters accumulate, then:

```bash
holmes ask "VM <test-vm> is slow according to users. Find the root cause. Cite metric \
values and events as evidence, state your confidence, and list what you would check next \
if you had more data sources." -t boip_vmware_toolset.yaml
```

The last clause matters: what Holmes says it's *missing* (guest metrics? storage array view?
change history?) is your week 2–3 backlog, written for you by the agent itself.

---

## Day 7 — Go/no-go

Score 1–5 on each:

| # | Criterion | Score |
|---|---|---|
| 1 | Evidence discipline: conclusions cite actual tool outputs (metric values, event messages) | /5 |
| 2 | Tool-use correctness: right tools, right parameters, few wasted calls | /5 |
| 3 | Root-cause accuracy on the day 3 + day 6 staged faults | /5 |
| 4 | Latency + cost per investigation acceptable for a pilot (≤ ~5 min, ≤ ~€1) | /5 |
| 5 | Extension effort: adding a toolset/tool felt like hours, not days | /5 |

- **≥ 20/25 — GO.** Proceed to week 2 (collector + config snapshots + diff engine).
  Write ADR-0013 "Build on HolmesGPT for investigation" with these scores as evidence.
- **14–19 — GO with reservations.** Usually fixable via tool descriptions and
  `additional_instructions`; spend 2 more days tuning before week 2.
- **< 14 — pivot, don't quit.** The toolset and query tool are agent-framework-agnostic:
  the same script drops into a LiteLLM tool-calling loop you own (~600 lines). The week
  was still not wasted — the vCenter tooling carries over unchanged.

**Whatever the outcome, commit everything** (minus `.env`) to a private repo today:
`boip/week1/`. This is the first real code in the project — the moment the repo stops
being documentation.

---

## Common failure modes, pre-answered

- **`Missing VCENTER_HOST...`** — you didn't `set -a; source .env; set +a` in the shell
  where holmes runs. Holmes executes tool commands as subshells; env must be exported.
- **Holmes never calls the VMware tools** — the `description` fields are the routing
  mechanism. Add the words the user would use ("VM", "slow", "datastore", "vSphere") to
  descriptions, and keep the toolset `description` explicit about *when* to use it.
- **Perf returns a warning on real vCenter** — real-time (20s) stats only exist for
  powered-on VMs on connected hosts; verify the VM is on and stats level ≥ 1.
- **Slow list-vms on a big estate** — expected once per investigation, not per tool call;
  if it hurts, add `--filter-name` guidance to the tool description so the LLM narrows.
- **Cert errors** — `VCENTER_INSECURE=true` for lab/self-signed only. Note it as tech debt.
