# ADR 0014: Use NetBox as the asset and topology source of truth

- **Status:** Accepted (supersedes the standalone Asset and Configuration Service)
- **Date:** 2026-07-12

## Context

The original architecture specified a bespoke Asset and Configuration Service plus a graph
database (Apache AGE). NetBox is an established open-source source of truth for
infrastructure, already operated by the team, familiar to target clients, and exposes a
complete API for both sync and query.

## Decision

Collectors sync canonical assets into NetBox; topology queries read from NetBox plus a thin
`asset_edge` table in PostgreSQL traversed with recursive CTEs. No dedicated graph engine
until scale proves it necessary.

## Consequences

- Zero custom asset-service code in the MVP; effort moves to collector quality.
- A ~10k-edge topology (2,000 VM target) is well within PostgreSQL capability.
- Clients gain a standalone-valuable NetBox instance even before AI features land.
