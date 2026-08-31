# Phase 12: Memory System

## Purpose
The **Memory System** provides persistent, structured, privacy-aware retention of useful insights, decisions, lessons, and summaries across Mycel execution sessions. 

It explicitly differentiates Memory (learned experiences) from Knowledge (static manuals), Chat History (raw transcripts), and Artifacts (deliverable binaries).

---

## Architectural Principles & Boundaries

1. **Memory Scope Hierarchy**: Memory is isolated and grouped into specific scopes: `ORGANIZATION`, `TEAM`, `POSITION`, `EMPLOYEE`, `AGENT`, `TASK`, and `COLLABORATION`. 
2. **Typed Memory Classification**: Memory is typed to signal semantic purpose (`EPISODIC`, `SEMANTIC`, `PROCEDURAL`, `DECISION`, `LESSON`).
3. **Extraction & Sanitization**: Memory is automatically extracted and sanitized. Prohibited secrets (`api_key`, `secret`, `password`) and chain-of-thought traces (`think`) are rigorously scrubbed before storage.
4. **Deterministic Retrieval & Indexing**: Indexing relies on hierarchical scope bounding, tags, and keyword relevance scoring, avoiding mandatory costly LLM calls for storage or querying.
5. **Context Optimization**: Memory queries project minimal context dictionaries to avoid token explosion when loaded into Agent or WorkUnit runtimes.
6. **No Execution Side Effects**: The memory system does NOT run LLMs, hire employees, instantiate agents, call external tools, or build physical artifacts.

---

## Scopes
- **ORGANIZATION**: Global company-wide policies, cross-team learnings, strategic guidelines.
- **TEAM**: Team-level operational memory, preferred pipelines, common mistakes, team decisions.
- **POSITION**: Role-specific practices, specialized domain guidelines.
- **EMPLOYEE**: Individual employee identity learnings, style preferences, historical performance notes.
- **AGENT**: Runtime execution instance memory (session-bounded).
- **TASK**: Task-scoped memory (learnings from a specific task execution).
- **COLLABORATION**: Inter-team handoff learnings, cross-team feedback.

---

## Types
- **EPISODIC**: Execution events, milestone summaries, task completion records.
- **SEMANTIC**: Extracted facts, rules, learned preferences, domain guidelines.
- **PROCEDURAL**: Best-practice steps, pipeline shortcuts, workflow optimizations.
- **DECISION**: Explicit choices made, rationale, trade-offs, approvals, rejections.
- **LESSON**: Identified mistakes, failure causes, quality gate feedback, corrective rules.
