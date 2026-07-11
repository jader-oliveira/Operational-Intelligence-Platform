# Knowledge and Decision Graph

## Infrastructure graph

Nodes represent assets, services, owners, configurations, policies, incidents, changes, and evidence. Edges represent hosted-on, depends-on, connected-to, owned-by, changed-by, violates, observed-on, caused-by, remediated-by, and verified-by.

## Decision graph

The decision graph preserves:

- Evidence considered.
- Hypotheses generated.
- Supporting and contradicting evidence.
- Engineer decisions.
- Policies evaluated.
- Recommendations accepted or rejected.
- Actions executed.
- Outcomes and validation.
- Lessons and reusable patterns.

## Query examples

- Which business services depend on this ESXi host?
- What changed in the 30 minutes before degradation?
- Which previous incidents had the same evidence pattern?
- Which recommendations for this configuration were accepted and successful?
- What evidence most strongly contradicts the leading hypothesis?
