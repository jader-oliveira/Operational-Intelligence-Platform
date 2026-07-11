# Threat Model

## Important threats

- Compromised connector credentials.
- Prompt injection in logs, tickets, or documentation.
- Poisoned training data.
- Unauthorized retrieval across environments.
- Model exfiltration of sensitive data.
- Malicious or unsafe automation.
- Approval bypass.
- Tampering with evidence or audit history.
- Dependency or model supply-chain compromise.
- Denial of service through telemetry floods or expensive model requests.

## Required mitigations

Input classification, content sanitization, permission filters, signed artifacts, provenance hashes, isolated execution, policy enforcement, rate limits, quotas, model allow-lists, dependency scanning, audit immutability, and regular red-team tests.
