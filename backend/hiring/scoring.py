from typing import List, Tuple
from .models import CandidateSnapshot, HiringRequirement, HiringCandidateScore, HiringScoreBreakdown

class CandidateScorer:
    """
    Evaluates soft matches and normalizes everything to 0.0 - 1.0.
    """
    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "skills": 0.40,
            "tools": 0.20,
            "outputs": 0.15,
            "reasoning": 0.10,
            "specialization": 0.10,
            "availability": 0.05
        }

    def score(self, candidate: CandidateSnapshot, reqs: HiringRequirement, eligible: bool, ineligible_reasons: List[str]) -> HiringCandidateScore:
        if not eligible:
            # Short-circuit for ineligible
            return HiringCandidateScore(
                employee_id=candidate.employee_id,
                overall_score=0.0,
                breakdown=HiringScoreBreakdown(),
                eligible=False,
                ineligible_reasons=ineligible_reasons
            )
            
        skill_s = self._score_skills(candidate, reqs)
        tool_s = self._score_tools(candidate, reqs)
        output_s = self._score_outputs(candidate, reqs)
        reason_s = self._score_reasoning(candidate, reqs)
        spec_s = self._score_specialization(candidate, reqs)
        avail_s = self._score_availability(candidate)
        
        overall = (
            (skill_s * self.weights["skills"]) +
            (tool_s * self.weights["tools"]) +
            (output_s * self.weights["outputs"]) +
            (reason_s * self.weights["reasoning"]) +
            (spec_s * self.weights["specialization"]) +
            (avail_s * self.weights["availability"])
        )
        
        breakdown = HiringScoreBreakdown(
            skills=skill_s, tools=tool_s, outputs=output_s, 
            reasoning=reason_s, specialization=spec_s, availability=avail_s
        )
        
        return HiringCandidateScore(
            employee_id=candidate.employee_id,
            overall_score=round(overall, 4),
            breakdown=breakdown,
            eligible=True,
            ineligible_reasons=[]
        )

    def _score_skills(self, candidate: CandidateSnapshot, reqs: HiringRequirement) -> float:
        if not reqs.skills:
            return 1.0
        total_score = 0.0
        total_weight = sum(s.weight for s in reqs.skills) or 1.0
        
        for s_req in reqs.skills:
            prof = candidate.skills.get(s_req.skill_id, 0)
            norm = min(prof / 100.0, 1.0)
            weight = s_req.weight / total_weight
            total_score += norm * weight
            
        return total_score

    def _score_tools(self, candidate: CandidateSnapshot, reqs: HiringRequirement) -> float:
        if not reqs.tools:
            return 1.0
        match_count = sum(1 for t in reqs.tools if t.tool_id in candidate.tools)
        return match_count / len(reqs.tools)

    def _score_outputs(self, candidate: CandidateSnapshot, reqs: HiringRequirement) -> float:
        if not reqs.outputs:
            return 1.0
        match_count = sum(1 for o in reqs.outputs if o.type in candidate.outputs)
        return match_count / len(reqs.outputs)

    def _score_reasoning(self, candidate: CandidateSnapshot, reqs: HiringRequirement) -> float:
        if not reqs.reasoning_profile.preferred:
            return 1.0
        return 1.0 if candidate.reasoning_profile_id == reqs.reasoning_profile.preferred else 0.5

    def _score_specialization(self, candidate: CandidateSnapshot, reqs: HiringRequirement) -> float:
        # Without deep LLM inference on how the specialization string matches the text,
        # we do a basic keyword overlap, or rely heavily on the skills match.
        # Returning 0.85 as a baseline unless we implement deep text matching.
        return 0.85 

    def _score_availability(self, candidate: CandidateSnapshot) -> float:
        return 1.0 if candidate.availability == "available" else 0.0


class CandidateRanker:
    """
    Sorts eligible candidates deterministically by score, applying tiebreakers.
    """
    @classmethod
    def rank(cls, scores: List[HiringCandidateScore]) -> List[HiringCandidateScore]:
        eligible = [s for s in scores if s.eligible]
        
        # Sort descending by:
        # 1. Overall Score
        # 2. Skill Score (Tiebreaker 1)
        # 3. Tool Score (Tiebreaker 2)
        # 4. Employee ID (Stable Deterministic Tiebreaker)
        
        eligible.sort(key=lambda x: (
            x.overall_score,
            x.breakdown.skills,
            x.breakdown.tools,
            x.employee_id
        ), reverse=True)
        
        return eligible
