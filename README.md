# BOIP — BreuTech Operational Intelligence Platform

**Sovereign, evidence-driven operational intelligence for on-premises VMware, Xen and
Kubernetes estates.**

An AI infrastructure engineer that runs entirely inside your datacenter, investigates
incidents across VMware, Xen and Kubernetes with cited evidence, tells you exactly what
changed before the incident, and proposes fixes as Ansible jobs that your team approves in
GitLab. Nothing leaves your network. Every conclusion is auditable.

## Status — honest version

| Area | State |
| --- | --- |
| Week 1 kit (vCenter query tool + HolmesGPT toolset) | **Code, tested against vcsim** — see `week1/` |
| MVP rebuild plan (market analysis, architecture, 10-week plan) | `docs/00-executive/mvp-rebuild-plan.md` |
| Architecture decisions | `adrs/` — 0013–0017 define the rebuilt approach |
| Collector, diff engine, boip-core, approval loop | Not yet built — weeks 2–7 of the plan |
| Original 17-service architecture docs | Superseded; component specs archived in `docs/archive/` |

This repository previously contained only architecture documentation. It is being rebuilt
around a deliberately small, implementable MVP. Anything not backed by running code is a
plan, and is labeled as such.

## Why this exists

The 2026 AI SRE market (Datadog Bits AI, Dynatrace Davis, NeuBird, Komodor, and others) is
cloud- and Kubernetes-first, and almost entirely SaaS. European hospitals, universities,
public bodies and mid-market industrials running VMware/Xen hybrid estates cannot ship
telemetry to a US SaaS — and post-Broadcom, many are mid-migration with config drift
everywhere and tribal knowledge in three people's heads. Nobody serves that quadrant.
BOIP does.

## Architecture in one paragraph

Read-only collectors (pyVmomi, XenAPI, Kubernetes API) write canonical inventory and
per-asset config snapshots into PostgreSQL, producing a versioned change history that
answers "what changed?". An investigation agent (HolmesGPT with custom toolsets — see
ADR 0013) correlates live performance data, vCenter events, topology (NetBox, ADR 0014) and
config diffs into evidence-cited root-cause reports. Recommendations become GitLab merge
requests executing AWX job templates on approval, with pre-flight, verification and
rollback (ADR 0015). One FastAPI core, one PostgreSQL, one Helm chart (ADR 0016). Sovereign
deployments run local models via Ollama/vLLM; the accuracy trade-off versus frontier APIs
is measured and disclosed (ADR 0017).

## Non-negotiable design principles

- Evidence before conclusions.
- Human approval before production change.
- Least privilege and read-only collection by default.
- Every recommendation includes risk, alternatives, rollback, and verification.
- Models never become the system of record.
- All AI outputs are traceable to evidence, model version, prompt version, and policy version.
- Vendor-neutral architecture with pluggable connectors and models.
- Separate deterministic policy checks from probabilistic AI reasoning.

## MVP definition

Given a webhook or manual trigger about a VMware or Kubernetes incident, produce within
5 minutes an evidence-cited investigation report including what changed in the preceding
24 hours, and for 3 supported incident classes, open a GitLab MR with an approvable,
rollback-equipped AWX remediation — deployed entirely inside the client network, with
governance metrics (root-cause top-1/top-3 accuracy, recommendation acceptance rate,
evidence coverage) queryable in PostgreSQL.

## Start here

1. `week1/WEEK1-RUNBOOK.md` — the 7-day validation of the whole approach (runnable today).
2. `docs/00-executive/mvp-rebuild-plan.md` — market reality, kill/keep/reuse decisions,
   data model, and the 10-week build plan.
3. `adrs/0013`–`0017` — why the architecture collapsed from 17 services to 3 deployables.

## Repository structure

```text
.
├── README.md
├── week1/                 # tested code: vCenter query tool + HolmesGPT toolset
├── docs/
│   ├── 00-executive/      # vision, mvp-rebuild-plan
│   ├── 01-product/        # requirements, success metrics, personas
│   ├── 02-architecture/   # data model, lifecycle (being revised to match ADRs 0013–0017)
│   ├── 04-ai-ml/ …        # under revision
│   └── archive/           # superseded 17-service component specs
├── adrs/                  # 0001–0012 original baseline, 0013–0017 the rebuild
├── schemas/               # recommendation schema is the load-bearing one
├── jira/                  # to be regenerated from the 10-week plan
└── deployment/            # Helm chart lands in week 4–5
```
