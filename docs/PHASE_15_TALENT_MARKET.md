# Phase 15: Talent Market

## Purpose
The Talent Market is a **capability-centric discovery layer** over the Mycel workforce. It answers the question "who can do this?" without making final hiring decisions. The Hiring System consumes its output — a list of `CandidateReference`s — and performs selection.

## Talent Market vs Hiring

| | Talent Market | Hiring System |
|---|---|---|
| **Question** | Who satisfies these requirements? | Which candidate should be selected? |
| **Output** | `CandidateReference` list | `HiringDecision` |
| **Can hire?** | ❌ Never | ✅ Yes |
| **Can assign tasks?** | ❌ Never | ✅ Yes |

## Architecture

```
TASK REQUIREMENTS
       ↓
 TALENT MARKET
       │
       ├── TalentRegistry (snapshot store)
       ├── TalentCandidateFilter (eligibility gates)
       ├── TalentCandidateMatcher (per-dimension breakdown)
       └── TalentCandidateRanker (weighted score + top-K)
       ↓
 CANDIDATE POOL (CandidateReference list)
       ↓
 HIRING SYSTEM (selection + revalidation)
```

## Components

| File | Responsibility |
|---|---|
| `models.py` | Domain entities: TalentCapabilitySnapshot, TalentProfile, CandidateReference, TalentSearchRequest, TalentSearchResult |
| `snapshot.py` | Projects Employee → TalentCapabilitySnapshot |
| `filter.py` | Hard eligibility gates (skill proficiency, tool authorization, availability, workload) |
| `matcher.py` | Per-dimension breakdowns with scores and explanations |
| `ranker.py` | Weighted aggregation + deterministic sort + top-K |
| `registry.py` | In-memory snapshot store with invalidation |
| `service.py` | Orchestration facade: Filter → Match → Rank → Return |

## Non-Goals
- Does NOT hire employees
- Does NOT assign tasks
- Does NOT create Agents
- Does NOT grant Tool permissions
- Does NOT activate Upskills
- Does NOT modify Employee skills or Team membership
- Does NOT maintain a global employee leaderboard
- Does NOT use LLM for structured search
