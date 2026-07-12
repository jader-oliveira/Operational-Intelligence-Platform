# BOIP Reality Check & MVP Rebuild Plan

**Reviewed:** `jader-oliveira/Operational-Intelligence-Platform` @ main
**Date:** 2026-07-11
**Verdict in one line:** The vision and safety principles are genuinely good — better than most of the market's marketing. But as written, this is a $10M+, 20-person, 3-year enterprise program disguised as a project, it contains zero code, and if you try to build it as specced you will ship nothing while the AI SRE market eats the easy wins. The fix is not to abandon it — it's to collapse ~80% of it into things you already run (AWX, GitLab, Vault, NetBox, Prometheus) and existing open source (HolmesGPT), and build only the 20% that nobody sells: **evidence-driven, human-approved operational intelligence for on-prem VMware/Xen/Kubernetes estates that cannot ship telemetry to a SaaS.**

---

## Part 1 — Honest review of the repository

### What is actually in the repo

1,698 lines of Markdown documentation, a 4,401-line Jira import CSV, JSON schemas, a stub OpenAPI file, ADRs, and empty-shell deployment YAML. **There is no code.** No collector, no API implementation, no agent, no test, no Dockerfile. The MANIFEST.json with SHA256 hashes of every doc is a tell: this is a generated documentation package, not an engineered system.

### What is genuinely good (keep this — it's your differentiator in sales conversations)

- **The non-negotiable principles.** "Evidence before conclusions", "human approval before production change", "models never become the system of record", "recommendations include risk, rollback, and verification", "snapshot advice is workload-aware." These are exactly the trust properties enterprise infra teams demand and exactly what most AI SRE vendors hand-wave. This page is your sales pitch. Frame it, keep it.
- **The Recommendation schema.** Risk enum, confidence, evidence_ids, preconditions, backup/snapshot guidance, rollback, verification, lifecycle state. This is a better remediation contract than most commercial tools expose. Keep it nearly as-is.
- **The pilot plan.** Entry criteria, shadow investigation before execution, historical incident replay, exit criteria with coverage and acceptance thresholds. This is a real, sellable pilot structure. Keep it.
- **The success metrics.** Root-cause top-1/top-3 accuracy, recommendation acceptance rate, hallucination rate, confidence calibration. Most vendors can't produce these numbers. If you can, you win deals.
- **ADR discipline.** Keep writing ADRs.

### What is broken

**1. It's an architecture for a company you don't have.**
Seventeen named services (Observer, Connector Runtime, Asset Service, Knowledge Graph Service, Evidence Engine, Incident Workspace, Model Gateway, Retrieval, Reasoner, Predictor, Guardian, Advisor, Policy/Approval, Orchestrator, Execution Adapters, Evaluator, Operations DNA, Portal). Plus Redpanda/Kafka, Temporal, OpenSearch, Thanos/Mimir, MinIO, Apache AGE, pgvector→Qdrant, Keycloak, Vault, OPA, vLLM/SGLang, MLflow, Airflow, React portal. That is the tech stack of a 40-engineer platform org. Running Temporal + Redpanda + OpenSearch + Thanos **alone** is more operational burden than the entire MVP should be. Every one of these is defensible in isolation; together they guarantee you spend 18 months on plumbing before the first investigation report exists.

**2. The component specs are template-stamped.**
`reasoner.md`, `advisor.md`, `connector-sdk.md`, and the rest share identical boilerplate sections ("Provide the X capability as an independently deployable, observable, and policy-controlled service", identical Inputs/Outputs/Scaling/Telemetry blocks). A client's architect will spot this in five minutes and it will cost you credibility. Real component specs differ because real components differ. Either write them for real or delete them.

**3. The roadmap front-loads everything that doesn't produce value.**
Phase 0 alone is 6–8 weeks of documents. First user-visible value (an investigation report) arrives in Phase 3, i.e. month 8–12 by the repo's own numbers. No client waits that long, and you can't self-fund that long.

**4. The MVP definition is not an MVP.**
"Discover a VMware environment, maintain a current dependency graph, investigate a selected incident, produce a cited and confidence-scored root-cause report, recommend a safe human-approved remediation plan, and track whether the recommendation was accepted and correct" — that's five products. A real MVP is one incident class, investigated well, with evidence, on one client's estate.

**5. It plans to fine-tune and continue-pretrain models before it has a single user.**
Phase 6 fine-tuning, TRL, continued pretraining, multi-model benchmarking — in 2026 this is the wrong default. Frontier + strong open-weight models with good context engineering beat fine-tunes for this domain unless you have thousands of labeled incidents, which you won't have for years. (This matters for your DGX Spark plan too — see Part 6.)

**6. The OpenAPI file is decorative.** Endpoints with no request/response schemas. Either generate it from FastAPI code (the correct direction) or drop it.

**7. Schemas are untyped where it matters.** `event_id: string` with no format, `payload: object` with no discriminated variants, no `$id`, no versioning strategy beyond a string field. Fine as sketches, not as contracts.

---

## Part 2 — What the market already ships (and where it doesn't play)

The AI SRE / operational intelligence category exploded in 2024–2026. You are not early. You must know exactly who does what:

| Player | What they do well | Why they don't kill you |
|---|---|---|
| **Datadog Bits AI SRE** | Autonomous alert investigation with a hypothesis-testing loop (validated/invalidated/inconclusive), ~3–4 min investigations, zero setup — **inside Datadog** | Requires all telemetry in Datadog SaaS. Dead on arrival for sovereign/on-prem healthcare & public sector, and useless for vSphere/Xen estates not instrumented into Datadog |
| **Dynatrace Davis AI** | Causation-based RCA on a live topology model (Grail lakehouse), the most mature engine | Very expensive, SaaS-centric, heavy agent footprint; overkill and often non-compliant for the mid-size on-prem estate |
| **NeuBird, Traversal, Cleric, Sherlocks, Resolve.ai** | AI-native autonomous investigation over existing observability stacks; NeuBird claims ~94% RCA accuracy via context engineering; some offer in-VPC/on-prem deployment | Cloud/K8s-first. None of them speak vCenter perf counters, ESXi hardening, Xen pools, or hospital change-advisory-board workflows |
| **Komodor Klaudia** | Kubernetes-specialist agent, strong accuracy claims, Gartner-recognized | Kubernetes only |
| **Anyshift** | **Versioned infrastructure graph** — answers "what changed?" with diffs across time; RCA grounded in topology, not just telemetry correlation | Cloud/IaC-focused (AWS/Terraform). The *idea* is the most important one in the category — steal it for on-prem |
| **PagerDuty SRE Agent, Rootly, incident.io** | Incident workflow, on-call, AI triage and postmortems | Workflow layer, not deep infra investigation; SaaS |
| **ServiceNow** | Deep ITSM/CMDB/change governance + 2026 agentic updates | Six-figure licensing; your mid-market clients can't buy it |
| **HolmesGPT (CNCF sandbox, Apache 2.0)** | Open-source investigation agent: agentic loop over 25+ toolsets, evidence citations linked to data points, read-only by design, RBAC-aware, LLM-agnostic (incl. Ollama for air-gapped), custom YAML toolsets, alert-triggered via AlertManager/PagerDuty/Jira, 24/7 operator mode | **This is not a competitor — it is your Reasoner + Evidence Engine + Retrieval + Model Gateway, already built and maintained by Robusta + Microsoft.** It replaces roughly Phases 3 and half of Phase 1 of your roadmap |
| **VMware MCP servers (community + VCF Ops MCP)** | Thin VM-lifecycle wrappers (list/power/snapshot, `confirm=True` flags); VCF Operations MCP exposes vROps metrics/alerts/RCA to agents | Single-vCenter toy wrappers with no audit trail, no change history, no evidence model, no approval workflow. The official VCF one requires VCF Operations licensing — which post-Broadcom, many of your target clients are actively fleeing |

### The gap nobody fills — your wedge

Put the market on two axes: **deployment sovereignty** (SaaS ↔ fully on-prem/air-gapped) and **estate type** (cloud-native/K8s ↔ traditional virtualization + hybrid). The lower-right quadrant — *fully on-prem intelligence for VMware/Xen/K8s hybrid estates* — is nearly empty, and it's exactly where European hospitals, universities, municipalities, and mid-size industrials live. You work inside one (stluc/UCLouvain). You know:

- They **cannot** ship logs, configs, or hostnames to a US SaaS (GDPR, NIS2, patient data, procurement rules).
- They are mid-migration chaos: Broadcom licensing shock → XCP-ng/Proxmox evaluations, partial K8s adoption, config drift everywhere, tribal knowledge in three people's heads.
- They already run the boring, trusted tools: Ansible/AWX, GitLab, Zabbix/Prometheus, NetBox, Vault. They will never let an AI touch production directly — but they will happily let it **open a merge request**.
- NIS2 (in force, enforcement ramping through 2025–2026) forces them to document incident response, change control, and risk — your evidence bundles and audit trail are literally a compliance artifact.

**Positioning sentence for clients:** *"An AI infrastructure engineer that runs entirely inside your datacenter, investigates incidents across VMware, Xen and Kubernetes with cited evidence, tells you exactly what changed, and proposes fixes as Ansible jobs that your team approves in GitLab — nothing leaves your network, every conclusion is auditable."*

No one on the list above can say that sentence. Datadog can't (SaaS). HolmesGPT alone can't (no VMware depth, no change history, no approval/execution loop). ServiceNow can't (price). That sentence is the product.

---

## Part 3 — The rebuild: kill / keep / reuse

### Kill (for MVP — not forever, but be honest: most of these die permanently)

| Item | Replace with |
|---|---|
| 17 microservices | **One FastAPI monolith** (`boip-core`) + collector jobs. Split later only when a seam hurts |
| Redpanda/Kafka | Postgres tables + `LISTEN/NOTIFY` or a simple job queue (e.g. `procrastinate`/`arq`). You have no event volume yet |
| Temporal | Postgres state machine columns (`state`, `updated_at`) + idempotent workers. An incident lifecycle is 6 states, not a distributed saga |
| OpenSearch cluster | Client's existing log stack (query it, don't own it); Loki if greenfield |
| Thanos/Mimir | Client's existing Prometheus/Zabbix (query it via API) |
| Apache AGE graph DB | Postgres tables `asset` + `asset_edge` + recursive CTEs. A 2,000-VM topology is ~10k edges — trivial for Postgres |
| Qdrant / heavy RAG | pgvector *if* you index runbooks; for MVP, the agent's tool calls fetch live data — retrieval of documents is secondary |
| Model Gateway service | **LiteLLM as a library** (one config file: Claude API for capable clients, Ollama/vLLM on-prem for sovereign ones). Same code path |
| Keycloak | Client's existing SSO via a reverse-proxy (oauth2-proxy) or plain local users for pilot |
| OPA | 200 lines of Python policy functions with unit tests. Add OPA when a second client needs different policy |
| MLflow/Airflow/TRL/fine-tuning | Deleted from the roadmap until you have ≥1,000 labeled investigations |
| React portal | Phase 2. MVP output surface = **Slack/Teams/Mattermost message + Markdown report in GitLab + one boring server-rendered status page** |
| MinIO | Postgres `bytea`/JSONB for evidence bundles at MVP volume; move to object storage when bundles exceed ~50GB |

### Keep (from your repo)

- Non-negotiable principles page (verbatim — it's excellent)
- Recommendation JSON schema (tighten types, add `$id`, use it to validate LLM output)
- Canonical asset + config-snapshot concepts (implemented as 5 Postgres tables, not a "service")
- Pilot plan and success metrics (turn metrics into actual Postgres queries from day one)
- ADRs — and write new ones for every decision below

### Reuse (yours and the world's)

- **HolmesGPT** as the investigation engine — or, if you want full control, replicate its pattern: an agentic tool-calling loop (~600 lines with LiteLLM) whose contract is *every claim cites a tool call result*. Recommendation: **start with HolmesGPT + custom toolsets** to have a demo in week 2; decide by week 8 whether to internalize the loop. Apache 2.0 lets you embed it commercially.
- **Your own `inventory.py`** (pyVmomi, six classes, typed exceptions, per-NSIP output, CI pipeline) — this is 60% of the VMware collector already written.
- **Your XenAPI automation** — the Xen collector.
- **NetBox** (you already deploy its Helm chart) — this **is** your Asset & Configuration Service and your topology source of truth. Don't build one; sync into NetBox and read from it.
- **AWX** — this **is** your Orchestrator + Execution Adapter. Remediations are AWX job template launches with survey vars. Pre-flight checks and post-change verification are just more playbooks.
- **GitLab** — this **is** your Approval Service and audit trail. A recommendation becomes an MR containing the plan + evidence link; approval = merge (CODEOWNERS enforces who); merge pipeline calls AWX; rollback playbook referenced in the MR. Immutable, signed, familiar, NIS2-friendly. Zero code to build for approvals.
- **Vault** — credentials, exactly as you use it today.
- **Prometheus + Grafana** — both platform self-observability and a metrics source at clients who have it.

---

## Part 4 — MVP v0.1 architecture (what you actually build)

```
                        ┌────────────────────────────────────────────┐
                        │            CLIENT DATACENTER                │
                        │                                            │
  vCenter ──read-only──►│  ┌──────────────┐    ┌──────────────────┐  │
  Xen/XCP-ng ─read-only►│  │  Collectors   │───►│   PostgreSQL      │  │
  K8s API ───read-only─►│  │ (cron jobs)   │    │ assets/snapshots/ │  │
  Prometheus ──query───►│  └──────────────┘    │ diffs/incidents/  │  │
  Logs (existing) ─────►│                       │ evidence/recs     │  │
                        │  ┌──────────────┐    └────────┬─────────┘  │
  AlertManager ─webhook►│  │  boip-core    │◄────────────┘            │
  or manual trigger ───►│  │  (FastAPI)    │                          │
                        │  │  • incident    │    ┌──────────────────┐ │
                        │  │    lifecycle   │───►│ Investigation     │ │
                        │  │  • policy fns  │    │ agent (HolmesGPT  │ │
                        │  │  • report gen  │    │ + custom toolsets)│ │
                        │  └──────┬───────┘    └───────┬──────────┘ │
                        │         │                     │            │
                        │         │              LLM: Claude API     │
                        │         │              or Ollama/vLLM      │
                        │         ▼              (sovereign mode)    │
                        │  Slack/Teams msg + GitLab MR (plan+evidence)│
                        │         │  human merges = approval          │
                        │         ▼                                   │
                        │  GitLab pipeline ──► AWX job template       │
                        │  (pre-flight → change → verify → report)    │
                        └────────────────────────────────────────────┘
```

**Three deployable things. That's all:**

1. **`boip-collector`** — Python package, run as K8s CronJobs (or systemd timers at small clients). Modules: `vmware` (your inventory.py evolved), `xen`, `k8s`. Each run writes: full inventory upsert, per-asset **config snapshot** (canonical JSON, stable key ordering), and computes a **diff vs previous snapshot** stored as structured change records. This diff table is the crown jewel — it's what lets the agent answer *"what changed in the 24h before this incident?"*, which is the single highest-value question in infra RCA (this is Anyshift's whole thesis, applied to on-prem).

2. **`boip-core`** — one FastAPI app. Endpoints: webhook receiver (AlertManager/manual), incident CRUD, `POST /incidents/{id}/investigate` (launches agent, streams status), recommendation approval hooks (GitLab webhook), governance metrics (`GET /metrics/governance` — acceptance rate, top-3 accuracy, evidence coverage, straight SQL). State machine in Postgres: `new → investigating → report_ready → recommendation_proposed → approved → executing → verified | rolled_back | closed`.

3. **Investigation agent** — HolmesGPT with custom YAML toolsets you write:
   - `boip_changes`: "get config diffs for asset X / cluster Y in window Z" (queries your diff table)
   - `boip_topology`: "what depends on datastore D / host H" (NetBox + asset_edge CTE)
   - `vcenter_perf`: bounded pyVmomi perf counter queries (datastore latency, CPU ready, ballooning)
   - `vcenter_events`: vCenter event/task history in window
   - `xen_pool`: pool/host/SR status
   - plus built-ins: prometheus, kubernetes, loki/opensearch
   Output contract: Markdown report validated against a trimmed version of your Recommendation schema — every hypothesis lists supporting evidence IDs, contradicting evidence, confidence, and the report is stored immutably (hash it, keep the MANIFEST habit — there it's actually useful).

**Deployment:** one Helm chart (you live in Helm) with three values profiles: `demo` (kind/k3s + simulated vCenter), `pilot` (client K8s or single VM with docker-compose), `sovereign` (adds Ollama/vLLM). Also ship a docker-compose.yml — half your target clients don't have a K8s cluster to spare and a single VM install removes a sales objection.

**Data model — five tables carry the whole MVP:**

```sql
asset(id, kind, name, source, source_ref, environment, owner, labels jsonb, first_seen, last_seen)
asset_edge(parent_id, child_id, relation, first_seen, last_seen)          -- host_of, stored_on, runs_on, member_of
config_snapshot(id, asset_id, taken_at, config jsonb, config_hash)
config_change(id, asset_id, detected_at, path, old_value, new_value, snapshot_before, snapshot_after)
incident(id, title, state, source_alert jsonb, opened_at, closed_at)
evidence(id, incident_id, kind, source_tool, content jsonb, content_hash, collected_at)
recommendation(id, incident_id, summary, risk, confidence, evidence_ids uuid[], steps jsonb,
               rollback jsonb, verification jsonb, awx_template_id, gitlab_mr_url, state, outcome)
```

(Seven, counting evidence and recommendation — still one migration file.)

---

## Part 5 — The 10-week build plan (part-time realistic, evenings + weekends)

**Week 1 — Prove the loop end-to-end, ugly.**
Install HolmesGPT locally against your homelab (Proxmox/OKD) with the Prometheus + Kubernetes built-in toolsets. Break a pod, run `holmes investigate`. Then write your **first custom toolset**: a YAML toolset that shells out to a script calling pyVmomi for "get VM perf summary". Goal: by Sunday, Holmes answers a VMware question with cited data. This de-risks the entire project in seven days.

**Weeks 2–3 — Collector + snapshots + diffs.**
Refactor `inventory.py` into `boip-collector.vmware`: inventory upsert to Postgres, canonical config JSON per VM/host/datastore/portgroup, hash, diff vs previous, write `config_change` rows. Deliberately canonicalize (sort keys, strip volatile fields like uptime counters) or you'll drown in false diffs — this is where the real engineering is. Add the K8s collector (helm releases, deployments, images, resource specs — you know this API cold). Xen waits for week 8.

**Weeks 4–5 — boip-core + incident flow.**
FastAPI app, the seven tables via Alembic, AlertManager webhook → incident row → trigger HolmesGPT via its API/CLI with your toolsets (`boip_changes`, `boip_topology`, `vcenter_perf`, `vcenter_events`) → store report + evidence rows → post to Slack/Teams with a link. Server-rendered incident list page (Jinja2 — resist React).

**Weeks 6–7 — Recommendation → GitLab MR → AWX.**
Map 3 (three, not thirty) remediation types to AWX job templates you write as Ansible roles: (a) Storage vMotion off a hot datastore, (b) restart/resize a K8s workload, (c) revert a specific config change. `boip-core` renders the recommendation (schema-validated LLM output) into an MR in a `remediations` repo: plan.md with evidence links, `awx_launch.yml` with survey vars, rollback section. CODEOWNERS = your client's senior engineers. Merge pipeline: pre-flight playbook → change playbook → verification playbook → post result back to `boip-core` → outcome recorded on the recommendation row. **This closes the loop the entire repo dreamed about, using zero new infrastructure.**

**Week 8 — Sovereign mode + Xen.**
LiteLLM config swap to Ollama (Qwen3-32B-class or Llama tool-capable model) — test tool-calling quality honestly; document the accuracy gap vs Claude so you can price the trade-off for clients. Add the Xen/XCP-ng collector from your XenAPI code. This is also where the **DGX Spark earns its keep**: it's your portable on-prem inference demo box — "the model that analyzed your incident is sitting on this desk, not in Virginia."

**Weeks 9–10 — Golden cases + demo environment + hardening.**
Build 5 **golden incident cases** in your homelab with known root causes: (1) datastore latency from a noisy neighbor, (2) VM memory ballooning after a config change, (3) K8s crashloop from a bad image tag, (4) DNS breakage from a zone change (your BIND background), (5) certificate expiry cascade. Script the fault injection. Measure top-1/top-3 root-cause accuracy and evidence coverage across 3 runs each — now your success-metrics doc contains *numbers*, and your demo is reproducible in front of a client in 20 minutes. Write the pilot runbook (your existing pilot-plan.md, now executable).

**Explicit MVP definition (replaces the repo's):**
> Given a webhook or manual trigger about a VMware or Kubernetes incident, produce within 5 minutes an evidence-cited investigation report including what changed in the preceding 24h, and for 3 supported incident classes, open a GitLab MR with an approvable, rollback-equipped AWX remediation — deployed entirely inside the client network, with every metric in Part 1's success list queryable in Postgres.

---

## Part 6 — Business layer (because your clients buy outcomes, not architecture)

**Packaging (service-led, exactly matching your DGX/consulting analysis):**

1. **Pilot: "Operational Intelligence Assessment" — fixed price, 4–6 weeks, €12–25k.** Deploy read-only, ingest 2–4 weeks of estate data, replay 3 of *their* historical incidents through the agent, deliver: config-drift report, dependency map (NetBox), investigation demos on their real incidents, NIS2-relevant audit artifacts. Read-only means near-zero risk objections and the pilot itself is billable discovery.
2. **Subscription: platform + care — €2–6k/month** per site depending on estate size and sovereign-LLM vs API mode. Includes toolset updates, new remediation playbooks, quarterly accuracy report (your governance metrics — nobody else gives clients an AI accuracy report; make it a ritual).
3. **Expansion services:** custom connectors (their ITSM, their storage arrays), remediation catalog growth, migration intelligence (Broadcom-exodus assessments: "here's every workload, dependency, and risk ranked for XCP-ng/Proxmox migration" — the diff+topology engine does this almost for free and it's a red-hot 2026 pain).

**First client:** you have privileged insight into the hospital/university profile. Even if stluc itself can't be first (procurement, conflict), that profile — 500–3,000 VMs, VMware+ some Xen, small team, NIS2 pressure, zero appetite for SaaS telemetry — is your ICP. Belgian/EU healthcare, universities, communes, and MSPs serving them.

**Competitive one-liners you must be able to survive:**
- *"Why not Datadog Bits AI?"* → "Your data can't leave the building, and Bits doesn't know what an ESXi host is unless you pay to instrument everything into Datadog."
- *"Why not just HolmesGPT ourselves?"* → "You can — it's the engine we build on. What you're buying is the VMware/Xen depth, the change-history graph, the approval-to-Ansible loop, the golden-case validation, and someone accountable for accuracy." (Never hide the open-source foundation; sophisticated clients will find it and respect honesty.)
- *"Will the AI break production?"* → "It physically can't. Read-only credentials, and every change is an Ansible job your engineer merges in GitLab. Here's the audit trail." — this is your repo's principles page, now real.

**Name check:** "BOIP" is fine internally; for clients consider something that says the category ("<Brand> Sovereign Ops Intelligence"). Also, the repo pins you to "BreuTech" publicly — decide consciously whether this GitHub org/repo should be public while it's this far from the claims it makes; an empty-of-code repo with grand docs can hurt in due diligence. Either make it private until v0.1 code lands, or reframe README as "design docs" honestly.

---

## Part 7 — Risks, stated plainly

1. **HolmesGPT dependency risk.** CNCF sandbox, Robusta-driven; Robusta sells a SaaS on top. Mitigation: your value is in toolsets, data model, and the approval loop — all portable. Keep the agent behind a thin interface so you can swap in your own LiteLLM loop (weeks, not months, to replicate).
2. **Local-model tool-calling quality.** Sovereign mode with a 30B model will be measurably worse than Claude at multi-step investigation. Mitigation: measure it on golden cases, publish the delta to clients, offer a "EU-hosted API" middle tier (e.g., Claude via EU-region deployments or Mistral) between full-air-gap and US SaaS.
3. **Diff noise.** Config canonicalization is 80% of collector quality. Budget real time for suppression rules per asset type; a noisy "what changed" tool destroys agent accuracy and user trust simultaneously.
4. **Scope regrowth.** The old repo will whisper "add the Predictor, add Operations DNA." Rule: nothing new until 3 paying pilots. Forecasting/drift-scoring (Phase 4) is the *right second act* — capacity forecasting on your snapshot history is genuinely valuable and cheap once data accumulates — but it is act two.
5. **Solo-builder bus factor.** Clients will ask. Mitigation: everything in GitLab, runbooks, and a partner/subcontract bench story; or recruit one collaborator before the second client.

---

## Part 8 — Do this next (literal order)

1. Make the repo private (or re-title it "design documents") today.
2. Week 1 plan from Part 5: HolmesGPT + first pyVmomi toolset in your homelab. Seven days, go/no-go.
3. Delete or archive `docs/03-components/` (template-stamped); replace with three real specs: collector, core, agent-toolsets.
4. Rewrite README around the Part 2 positioning sentence and the Part 5 MVP definition.
5. New ADRs: 0013 "Build on HolmesGPT for investigation", 0014 "NetBox as asset source of truth", 0015 "GitLab MR as approval workflow, AWX as executor", 0016 "Monolith-first; defer Temporal/Kafka/OpenSearch", 0017 "No fine-tuning before 1,000 labeled investigations".
6. Keep the Jira CSV *only* after regenerating it from the 10-week plan — a 4,401-line backlog for a solo builder is demoralization-as-a-service.
7. Build the 5 golden cases as code from day one; they are your test suite, your demo, and your accuracy report generator — one artifact, three jobs.

---

### Final word

The repo's instincts — evidence, human approval, auditability, vendor neutrality — are the *right* instincts, and they're rarer in this market than the feature lists suggest. The mistake is purely one of scale and sequence: it specifies the cathedral before laying a brick, in a market that already sells prefab chapels. Collapse it onto the tools you already master, ship the one thing nobody sells (sovereign, change-aware, approval-gated intelligence for traditional infra), and let paying clients pull the rest of the architecture into existence. Ten weeks to a demo that no Datadog rep can give a Belgian hospital. That's the play.
