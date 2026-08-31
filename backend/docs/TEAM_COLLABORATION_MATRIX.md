# Team Collaboration Matrix

Mycel ships with 7 intentional collaboration contracts. Only meaningful operational dependencies are included.

## Collaboration Graph

```
Research ─────→ Developer
Research ─────→ Marketing

Developer ────→ Creative

Creative ─────→ Marketing

Legal ────────→ Marketing

Finance ──────→ Operations

Operations ───→ Developer
```

## Relationship Reference

| Contract ID | Provider → Requester | Why |
|---|---|---|
| `research_to_developer.requirements.v1` | Research → Developer | Developer needs verified requirements before building. Research provides market-validated, evidence-backed specifications. |
| `research_to_marketing.market_analysis.v1` | Research → Marketing | Marketing needs audience profiling and competitor intelligence for campaign strategy. Research provides this with source verification. |
| `developer_to_creative.product_demo.v1` | Developer → Creative | Creative needs accurate product feature descriptions, technical context, and UI references before producing videos or assets. |
| `creative_to_marketing.promotional_asset.v1` | Creative → Marketing | Marketing distributes creative output. Creative produces the finished promotional video or asset; Marketing receives an ArtifactReference. |
| `legal_to_marketing.compliance_review.v1` | Legal → Marketing | Marketing content in regulated contexts requires legal compliance review under Indian law before distribution. Human approval required. |
| `finance_to_operations.budget_approval.v1` | Finance → Operations | Operations cannot plan resource allocation without an approved budget. Finance validates and constrains the spend. |
| `operations_to_developer.workflow_requirements.v1` | Operations → Developer | Developer needs formal workflow and process specifications before building automation or tooling systems. |

## Design Principles

- **Intentional, not exhaustive**: Only real operational dependencies create contracts.
- **No combinatorial expansion**: Not every team connects to every other team.
- **Directionality matters**: `research_to_developer` means Research provides to Developer — not a bidirectional channel.
- **Legal remains isolated**: Legal only provides to Marketing; other teams cannot pull legal knowledge directly.
- **Finance controls budget approval**: Operations must request budget from Finance, not self-approve.
