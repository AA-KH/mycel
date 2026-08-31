from typing import List, Dict, Set
from .models import Plan, PlanNode

class ReasoningValidator:
    """
    Validates reasoning structures like Plans for safety and completeness.
    """
    
    @staticmethod
    def validate_plan(plan: Plan) -> List[str]:
        """
        Checks a plan for circular dependencies, missing required fields, 
        and orphaned nodes. Returns a list of error strings. 
        Empty list means valid.
        """
        errors = []
        
        if not plan.goal:
            errors.append("Plan missing goal.")
            
        if not plan.steps:
            errors.append("Plan contains no steps.")
            
        node_ids = {step.id for step in plan.steps}
        
        for step in plan.steps:
            if not step.title or not step.description:
                errors.append(f"Step {step.id} missing title or description.")
                
            for dep in step.dependencies:
                if dep not in node_ids:
                    errors.append(f"Step {step.id} depends on unknown step {dep}.")
                    
        # Check circular dependencies using DFS
        visited = set()
        rec_stack = set()
        
        def is_cyclic(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            node = next((n for n in plan.steps if n.id == node_id), None)
            if node:
                for dep in node.dependencies:
                    if dep not in visited:
                        if is_cyclic(dep):
                            return True
                    elif dep in rec_stack:
                        return True
                        
            rec_stack.remove(node_id)
            return False

        for step in plan.steps:
            if step.id not in visited:
                if is_cyclic(step.id):
                    errors.append("Plan contains circular dependencies.")
                    break
                    
        return errors
