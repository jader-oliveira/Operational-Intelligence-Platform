# Personas and Primary Workflows

## Personas

- Infrastructure engineer.
- Virtualization engineer.
- SRE or platform engineer.
- Security engineer.
- Change approver.
- Service owner.
- Platform administrator.
- ML or AI engineer.
- Auditor.

## Primary workflow: investigate an incident

1. Alert, ticket, or engineer creates an incident workspace.
2. The evidence engine identifies affected assets and relevant time window.
3. The system gathers metrics, logs, events, changes, configuration, topology, ownership, and similar incidents.
4. The reasoner generates ranked hypotheses.
5. A challenge agent searches for disconfirming evidence.
6. The engineer reviews evidence and requests deeper checks when needed.
7. The advisor produces remediation options.
8. Policies evaluate whether backup, snapshot, maintenance window, approvals, or specialist review are required.
9. An approver accepts, rejects, or modifies the plan.
10. Execution occurs through an approved automation adapter.
11. Post-change telemetry validates outcome.
12. The incident and decision graph are updated.

## Primary workflow: continuous posture review

The Guardian evaluates configuration and security posture, suppresses accepted exceptions, groups duplicate findings, identifies drift, and creates actionable recommendations with evidence and ownership.
