# Hiring System Architecture

The Smart Hiring System (Phase 9) evaluates Mycel's specialized workforce (created in Phase 8) against structured task requirements and deterministically selects the optimal employee for a given assignment.

## Responsibilities

*   **Hiring Selects:** Evaluates candidates and chooses the best match based on capabilities.
*   **Runtime Executes:** Receives the hired `employee_id` and orchestrates their actions.
*   **Reasoning Thinks:** Decides *how* the execution takes place.

## Core Flow

1.  **Task Input:** A user issues a task (e.g., "Create a market report").
2.  **Requirement Extraction:** `HiringRequirementBuilder` uses the LLM to parse the raw text into structured `HiringRequirement`s (skills, tools, outputs, preferred reasoning profile).
3.  **Candidate Discovery:** Retrieves a `CandidateSnapshot` from the `EmployeeRegistry` for all employees within the tenant `company_id`.
4.  **Hard Filters:** `CandidateFilter` evaluates mandatory checks (status, minimum skill proficiencies, required tools/outputs). Failed candidates are marked `INELIGIBLE`.
5.  **Soft Scoring:** `CandidateScorer` normalizes all eligible candidate matches against the requirements (0.0 to 1.0) and applies category weights to calculate an `overall_score`.
6.  **Ranking:** `CandidateRanker` sorts candidates deterministically by score and applies stable tie-breakers (`overall_score` -> `skill_score` -> `tool_score` -> `employee_id`).
7.  **Decision:** `HiringEngine` validates against the minimum threshold (e.g., 0.65) and generates a structured `HiringDecision` containing the selected `employee_id`.

## Non-Goals
The Hiring Engine explicitly does **not**:
*   Spawn brand-new agents or use raw LLM generation to bypass deterministic policy.
*   Store hidden chain-of-thought rationale (decisions are mathematically auditable).
*   Mutate employee records or upskill employees.
