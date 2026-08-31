# Evaluation Policy

Evaluation Policies provide the explicit blueprints for how a specific target is assessed. They separate the execution rules from the evaluation logic.

## Structure

- **Target Type**: The scope of the evaluation (e.g., `OUTPUT`, `TASK`, `WORK_UNIT`, `TEAM`).
- **Dimensions**: An array of characteristics to assess (e.g., `CORRECTNESS`, `QUALITY`, `EFFICIENCY`).
- **Weights**: Relative values assigned to each dimension to calculate the overall weighted score.
- **Thresholds**: Cut-offs defining passing vs. failing grades for specific metrics.
- **Allows Semantic**: A strict security boolean (`True`/`False`) that gates the usage of LLM-as-a-Judge.

## Deterministic Precedence

Policies enforce that deterministic checks take absolute priority. If a dimension is evaluated deterministically as `0.0` (e.g., a required file is missing), the overall evaluation will reflect a `PARTIAL` or `FAILED` state, regardless of high scores in other subjective dimensions.

## Semantic Evaluation Control

By default, `allows_semantic` is `False`. The Orchestrator will aggressively skip any `LLM_ASSISTED` evaluators unless this flag is explicitly enabled. This controls cost, bounds LLM hallucinations, and enforces the "Deterministic First" principle.
