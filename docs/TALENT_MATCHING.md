# Talent Matching Reference

## Skill Matching
- Match: `actual_proficiency >= minimum_proficiency` → PASS
- Score: `min(actual / minimum_proficiency, 1.0)` — full credit at threshold, bonus above it
- Weight: configurable per requirement; default weight = 1.0
- Missing skill: proficiency=0, counts as failure

## Tool Matching
- Match: `tool_id in authorized_tools` (NOT raw tools list)
- Authorization check: `Employee.permissions[tool_id] == ALLOWED`
- `APPROVAL_REQUIRED` and `DENIED` are NOT authorized
- Score: `matched_count / required_count`

## Capability Matching
- Sources: `snapshot.capabilities` ∪ `snapshot.upskill_capabilities`
- Score: `matched_count / required_count`
- Revoked upskill → removed from upskill_capabilities → no longer matches

## Availability Scores
| State | Score |
|---|---|
| AVAILABLE | 1.0 |
| LIMITED | 0.6 |
| BUSY | 0.2 |
| OFFLINE | 0.0 |
| UNAVAILABLE | 0.0 |

## Workload Score
`score = 1.0 - workload_ratio`  — lower workload = higher availability score
Missing workload = NOT_EVALUATED (not penalized)

## Evaluation Signal
`score = overall_performance / 100.0` (normalized 0–100 → 0–1)
Missing evaluation = NOT_EVALUATED (not penalized — absence of history ≠ failure)

## Overall Match Score (Weighted Aggregation)
```
score = Σ(dimension_score × weight) / Σ(weights of evaluated dimensions)
```
Dimensions with `score=None` (NOT_EVALUATED) are excluded from both numerator and denominator.

**Default Weights:**
| Dimension | Weight |
|---|---|
| Skills | 0.35 |
| Capabilities | 0.25 |
| Tools | 0.15 |
| Availability | 0.10 |
| Workload | 0.10 |
| Position | 0.05 |

Weights are configurable via `TalentSearchRequest.score_weights`.
Score is bounded `0.0–1.0`, rounded to 4 decimal places.

## Ranking
- Primary: `match_score` descending
- Tiebreaker: `employee_id` ascending (deterministic, reproducible)
- Ranking is **per-query** — no global leaderboard

## NOT_EVALUATED vs 0.0
| Value | Meaning |
|---|---|
| `score=0.0` | Dimension was evaluated and scored zero |
| `score=None` | Dimension was not requested / data unavailable |

Missing data never produces a zero score automatically.
