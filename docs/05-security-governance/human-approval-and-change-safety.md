# Human Approval and Change Safety

## Approval policy dimensions

- Environment.
- Business criticality.
- Action type.
- Blast radius.
- Risk score.
- Maintenance window.
- Backup or snapshot state.
- Required specialist.
- Separation of duties.
- Regulatory requirement.

## Safety sequence

Recommendation -> challenge -> policy evaluation -> pre-flight -> approval -> dry-run -> execute -> verify -> close or rollback.

## Snapshot and backup rule

The system must not blindly recommend snapshots. It evaluates workload consistency, database or cluster guidance, available backup, storage capacity, snapshot age, and rollback feasibility. When a snapshot is inappropriate, it recommends the correct application-consistent backup or alternate rollback method.
