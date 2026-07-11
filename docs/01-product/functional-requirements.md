# Functional Requirements

## Discovery and inventory

The platform shall discover infrastructure assets, relationships, ownership, software versions, configuration, and lifecycle state. Discovery shall be incremental, resumable, rate-limited, and auditable.

## Telemetry intelligence

The platform shall ingest or query metrics, logs, events, alarms, traces, and changes. It shall correlate them using time, topology, identity, and change context.

## Root-cause investigation

The platform shall create an incident workspace, formulate evidence requests, gather bounded evidence, generate ranked hypotheses, show supporting and contradicting evidence, and assign confidence.

## Prediction

The platform shall forecast capacity saturation, likely failure, abnormal behavior, configuration drift, and change risk. Predictions shall include horizon, uncertainty, features, model version, and backtest results.

## Security and hardening

The platform shall evaluate technical configuration against vendor guidance, CIS-style benchmarks, internal policy, exceptions, and business context. Findings shall include evidence, severity, exploitability or operational impact, and remediation.

## Remediation advice

Every remediation shall contain prerequisites, blast radius, risk, alternatives, backup/snapshot guidance, commands or automation references, validation, rollback, downtime expectations, and approval requirements.

## Guarded orchestration

Approved actions shall execute through controlled adapters such as AWX, Terraform, PowerCLI, or GitLab. The platform shall support dry-run, change windows, separation of duties, execution isolation, timeout, rollback, and post-change verification.

## Learning and evaluation

The platform shall capture incident outcome, engineer decision, recommendation acceptance, execution result, correctness, time saved, recurring issue status, and feedback for future retrieval, evaluation, or training.
