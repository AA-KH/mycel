import logging
from typing import Optional, List
from .models import HiringRequirement, CandidateSnapshot, HiringDecision, HiringCandidateScore
from .builder import HiringRequirementBuilder
from .filters import CandidateFilter
from .scoring import CandidateScorer, CandidateRanker
from workforce.employees.registry import EmployeeRegistry

logger = logging.getLogger(__name__)

class HiringEngine:
    def __init__(self, employee_registry: EmployeeRegistry, min_hiring_score: float = 0.65):
        self.registry = employee_registry
        self.scorer = CandidateScorer()
        self.min_hiring_score = min_hiring_score

    async def select_candidate(self, task_description: str, task_id: str, company_id: str) -> HiringDecision:
        logger.info(f"Hiring process started for task {task_id}")
        
        # 1. Build Requirements
        reqs = await HiringRequirementBuilder.build_from_task(task_description, task_id, company_id)
        
        # 2. Discover Candidates (Snapshots)
        snapshots_raw = await self.registry.get_capability_snapshot(company_id)
        snapshots = [CandidateSnapshot(**s) for s in snapshots_raw]
        
        if not snapshots:
            return self._create_no_candidate_decision(reqs, [], ["no_employees_in_company"])

        # 3. Filter & Score
        scored_candidates = []
        for snap in snapshots:
            eligible, reasons = CandidateFilter.evaluate(snap, reqs)
            score = self.scorer.score(snap, reqs, eligible, reasons)
            scored_candidates.append(score)
            
        # 4. Rank Eligible
        ranked = CandidateRanker.rank(scored_candidates)
        
        # 5. Apply Threshold & Select
        if not ranked:
            return self._create_no_candidate_decision(reqs, scored_candidates, ["all_candidates_failed_hard_filters"])
            
        top_candidate = ranked[0]
        if top_candidate.overall_score < self.min_hiring_score:
            return self._create_no_candidate_decision(
                reqs, 
                scored_candidates, 
                [f"top_candidate_below_threshold_{self.min_hiring_score}"]
            )
            
        # 6. Create Decision
        return HiringDecision(
            task_id=task_id,
            company_id=company_id,
            selected_employee_id=top_candidate.employee_id,
            status="selected",
            overall_score=top_candidate.overall_score,
            candidate_count=len(snapshots),
            selected_rank=1,
            reason_codes=["strong_overall_match", "passed_hard_filters", "highest_score"],
            candidate_scores=scored_candidates
        )
        
    def _create_no_candidate_decision(self, reqs: HiringRequirement, scores: List[HiringCandidateScore], reasons: List[str]) -> HiringDecision:
        return HiringDecision(
            task_id=reqs.task_id,
            company_id=reqs.company_id,
            status="no_candidate",
            overall_score=0.0,
            candidate_count=len(scores),
            reason_codes=reasons,
            candidate_scores=scores
        )
