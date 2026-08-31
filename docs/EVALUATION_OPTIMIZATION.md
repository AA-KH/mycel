# Evaluation Optimization

To maintain system speed and keep inference costs low, the Evaluation System adheres to a strict set of optimization principles.

## 1. Deterministic-First
Evaluators checking basic constraints (file types, existences, explicit schema keys) are favored over generative evaluation. If a deterministic evaluator fails, the system bypasses expensive LLM evaluation for that dimension.

## 2. LLM Call Minimization
LLM semantic evaluation is strictly opt-in and bound by `EvaluationPolicy.allows_semantic`. We never use LLMs to perform checks that a script or schema validator can accomplish.

## 3. Context Minimization
The `EvaluationContext` is rigorously pared down. We do not load massive chat histories or Agent Memory dumps into the evaluators. They receive only the `ArtifactReferences`, existing `QualityGateResult`s, and the core task IDs. 

## 4. Sampling & Caching
For large-scale processing, evaluation supports skipping duplicate runs via strict idempotency checks. If the `policy_version`, `evaluator_version`, and `task_id` match an existing Evaluation, the system can bypass recalculation and return the cached result.

## 5. Async Evaluation
Heavy operations, particularly LLM judgments and metric aggregations, are designed to run asynchronously. They do not block the critical path of `TaskCompletion` unless explicitly required by an Output Contract.
