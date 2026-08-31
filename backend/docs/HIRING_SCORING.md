# Hiring Scoring Model

Mycel's Smart Hiring System uses a deterministically weighted scoring algorithm. All raw inputs are normalized to a standard `0.0 - 1.0` range before weights are applied.

## Default Weights
Weights can be overridden by policy, but standard weights are:
- `skills`: 0.40
- `tools`: 0.20
- `outputs`: 0.15
- `reasoning`: 0.10
- `specialization`: 0.10
- `availability`: 0.05

## Score Normalization

### Skills (`skill_score`)
For each required skill, the candidate's proficiency (0-100) is normalized to a percentage (0.0 - 1.0) and multiplied by the skill's specific weight.
*Example: Required 'python' with candidate proficiency 90 -> 0.90 skill score.*

### Tools (`tool_score`)
Calculated as the percentage of requested tools the candidate actually possesses.
*Example: Requires 'python.execute' and 'fs.read'. Candidate has only 'python.execute' -> 0.50 tool score.*
*(Note: If a tool is flagged as mandatory, a missing tool causes hard filter rejection prior to scoring).*

### Outputs (`output_score`)
Calculated similarly to tool matching. Percentage overlap of requested outputs versus supported outputs.

### Reasoning (`reasoning_score`)
If a specific reasoning profile is preferred, it grants a perfect 1.0 match. Otherwise, a baseline score (0.50) is granted to allow candidate eligibility even if their primary profile isn't a strict alignment.

## Tie Breaking
In the event two candidates share identical `overall_score` values, Mycel employs a strict, deterministic tie-breaking cascade to prevent random selection:
1. `overall_score`
2. `skills` breakdown score
3. `tools` breakdown score
4. Canonical `employee_id` (alphabetical stability)
