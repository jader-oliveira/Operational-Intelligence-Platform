# Retrieval-Augmented Generation and Tool Use

## Retrieval sources

- Current topology and configuration.
- Historical incidents and postmortems.
- Approved runbooks.
- Vendor documentation snapshots.
- Internal standards and exceptions.
- Change and deployment history.
- Similar evidence patterns.

## Pipeline

Query planning -> permission filter -> lexical/vector/graph retrieval -> reranking -> evidence compression -> context assembly -> structured reasoning -> citation validation.

## Rules

- Prefer current configuration over stale documentation.
- Mark conflicting sources explicitly.
- Never retrieve secrets.
- Every evidence item includes source, timestamp, asset, permissions, and integrity hash.
- Tool calls are allow-listed, typed, rate-limited, and audited.
