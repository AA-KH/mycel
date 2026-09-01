import json
from teams.architecture.base import ArchitectureBaseAgent
from .profile import NAME, ROLE
from .prompt import SYSTEM_PROMPT
from .tools import get_tools

class AtlasAgent(ArchitectureBaseAgent):
    def __init__(self, session_id: str = None):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools(),
            session_id=session_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "compile_executive_blueprint":
            try:
                # We return the JSON as-is, this is the final binding output
                return json.dumps({
                    "blueprint_status": "COMPILED",
                    "final_decision": arguments.get("final_decision", "REJECTED"),
                    "key_risks": arguments.get("key_risks", []),
                    "estimated_timeline": arguments.get("estimated_timeline", "Unknown"),
                    "executive_summary": arguments.get("executive_summary", "")
                })
            except Exception as e:
                return json.dumps({"error": f"Failed to compile blueprint: {str(e)}"})
                
        elif function_name == "calculate_total_risk_matrix":
            try:
                sec = arguments.get("security_vulnerabilities_count", 0)
                sc = arguments.get("supply_chain_bottlenecks_count", 0)
                deps = arguments.get("critical_path_dependencies_count", 0)
                
                # Math formula for risk:
                # Sec issues are weight 3, Supply chain weight 2, deps weight 1
                total_risk_score = (sec * 30) + (sc * 20) + (deps * 10)
                health_score = max(0, 100 - total_risk_score)
                
                return json.dumps({
                    "health_score_out_of_100": health_score,
                    "risk_level": "CRITICAL" if health_score < 40 else "WARNING" if health_score < 70 else "HEALTHY",
                    "breakdown": {
                        "security_penalty": sec * 30,
                        "supply_chain_penalty": sc * 20,
                        "dependency_penalty": deps * 10
                    }
                })
            except Exception as e:
                return json.dumps({"error": f"Failed to calculate risk: {str(e)}"})
            
        else:
            return f"Error: Tool '{function_name}' not recognized by AtlasAgent."
