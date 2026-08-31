from typing import Tuple, List
from .models import CandidateSnapshot, HiringRequirement

class CandidateFilter:
    """
    Evaluates hard constraints. If a candidate fails any of these, they are marked INELIGIBLE.
    """
    
    @classmethod
    def evaluate(cls, candidate: CandidateSnapshot, reqs: HiringRequirement) -> Tuple[bool, List[str]]:
        reasons = []
        
        # 1. Status & Availability
        if candidate.status != "active":
            reasons.append("inactive_employee")
        if candidate.availability != "available":
            reasons.append("unavailable_employee")
            
        # 2. Mandatory Tools
        for t_req in reqs.tools:
            if t_req.required and t_req.tool_id not in candidate.tools:
                reasons.append(f"missing_required_tool:{t_req.tool_id}")
                
        # 3. Mandatory Outputs
        for o_req in reqs.outputs:
            if o_req.required and o_req.type not in candidate.outputs:
                reasons.append(f"unsupported_output:{o_req.type}")
                
        # 4. Mandatory Skills (Minimum Proficiency)
        for s_req in reqs.skills:
            if s_req.required:
                prof = candidate.skills.get(s_req.skill_id, 0)
                if prof < s_req.minimum_proficiency:
                    reasons.append(f"insufficient_skill_proficiency:{s_req.skill_id}")
                    
        # 5. Mandatory Reasoning Profile
        if reqs.reasoning_profile.required:
            if candidate.reasoning_profile_id != reqs.reasoning_profile.preferred:
                reasons.append("missing_reasoning_profile")
                
        eligible = len(reasons) == 0
        return eligible, reasons
