# Team Execution Contracts

Mycel ships with **21 canonical execution contracts** across 7 core teams (3 per team).

---

## Developer Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `developer.software_development.v1` | `software_development`, `feature_development` | `development_pipeline` |
| `developer.bug_fix.v1` | `bug_fix`, `defect_resolution` | `development_pipeline` |
| `developer.api_development.v1` | `api_development`, `endpoint_development` | `development_pipeline` |

## Research Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `research.research_report.v1` | `research_report`, `research` | `research_pipeline` |
| `research.fact_verification.v1` | `fact_verification`, `fact_check` | `research_pipeline` |
| `research.market_research.v1` | `market_research` | `research_pipeline` |

## Creative Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `creative.promotional_video.v1` | `promotional_video`, `product_video` | `creative_pipeline` |
| `creative.image_generation.v1` | `image_generation`, `image_asset` | `creative_pipeline` |
| `creative.creative_asset.v1` | `creative_asset`, `marketing_asset`, `social_media_asset` | `creative_pipeline` |

## Legal Team

| Contract ID | Task Types | Pipeline | Human Approval |
|---|---|---|---|
| `legal.legal_research.v1` | `legal_research` | `legal_pipeline` | Required |
| `legal.contract_analysis.v1` | `contract_analysis`, `contract_review` | `legal_pipeline` | Required |
| `legal.contract_draft.v1` | `contract_draft`, `contract_drafting` | `legal_pipeline` | Required |

## Marketing Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `marketing.campaign.v1` | `campaign`, `marketing_campaign`, `market_campaign` | `marketing_pipeline` |
| `marketing.content_strategy.v1` | `content_strategy` | `marketing_pipeline` |
| `marketing.marketing_plan.v1` | `marketing_plan` | `marketing_pipeline` |

## Finance Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `finance.financial_analysis.v1` | `financial_analysis` | `finance_pipeline` |
| `finance.budget.v1` | `budget`, `budgeting` | `finance_pipeline` |
| `finance.financial_report.v1` | `financial_report`, `finance_report` | `finance_pipeline` |

## Operations Team

| Contract ID | Task Types | Pipeline |
|---|---|---|
| `operations.workflow_execution.v1` | `workflow_execution`, `workflow`, `process_execution` | `operations_pipeline` |
| `operations.process_analysis.v1` | `process_analysis` | `operations_pipeline` |
| `operations.operations_plan.v1` | `operations_plan`, `operational_plan` | `operations_pipeline` |

---

## Featured Contract: `creative.promotional_video.v1`

This contract represents the canonical end-to-end creative production flow:

- **Required input**: `product_description`
- **Optional inputs**: `brand_assets`, `target_audience`, `duration`, `format`
- **Pipeline**: `creative_pipeline`
- **Stages**: concept → scripting → production → editing → quality → delivery
- **Expected artifact**: `video` (mp4)
- **Quality gates**: `visual_quality`, `format_validation`, `content_review`
- **Completion criteria**: artifact created, format valid, all quality gates passed, ArtifactReference created, handoff ready
- **Human approval**: not required (automated creative flow)
