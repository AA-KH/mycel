import json
from teams.architecture.base import ArchitectureBaseAgent
from .profile import NAME, ROLE
from .prompt import SYSTEM_PROMPT
from .tools import get_tools

class PriyaAgent(ArchitectureBaseAgent):
    def __init__(self):
        super().__init__(
            name=NAME,
            role=ROLE,
            system_prompt=SYSTEM_PROMPT,
            agent_tools=get_tools()
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "generate_gantt_chart":
            title = arguments.get("title", "Project Timeline")
            tasks = arguments.get("tasks", [])
            
            mermaid_str = f"```mermaid\ngantt\n    title {title}\n    dateFormat YYYY-MM-DD\n"
            
            current_section = ""
            for i, task in enumerate(tasks):
                section = task.get("section", "Tasks")
                if section != current_section:
                    mermaid_str += f"    section {section}\n"
                    current_section = section
                
                t_name = task.get("task_name")
                duration = task.get("duration")
                deps = task.get("dependencies", [])
                
                # Make a unique ID for the task
                t_id = f"t{i}"
                if deps:
                    # In this simulation, we'll just format it as after the first dep
                    dep_str = f"after {deps[0]}"
                else:
                    dep_str = ""
                    
                mermaid_str += f"    {t_name} : {t_id}, {dep_str}, {duration}\n"
                
            mermaid_str += "```"
            
            return json.dumps({
                "status": "success",
                "message": "Mermaid Gantt chart generated successfully.",
                "markdown_code": mermaid_str
            })
            
        elif function_name == "estimate_sprint_velocity":
            complexity = arguments.get("complexity", "medium")
            engineers = arguments.get("engineers_assigned", 2)
            
            multiplier = {"low": 1, "medium": 3, "high": 5, "extreme": 10}.get(complexity, 3)
            # Rough math: 1 engineer can do 2 velocity points per sprint
            total_points = multiplier * 2
            velocity_per_sprint = engineers * 1.5  # Adjust for overhead
            
            estimated_sprints = max(1, round(total_points / velocity_per_sprint))
            
            return json.dumps({
                "feature": arguments.get("feature_name"),
                "total_points": total_points,
                "velocity_per_sprint": velocity_per_sprint,
                "estimated_sprints_required": estimated_sprints,
                "recommendation": "Consider adding more engineers." if estimated_sprints > 4 else "Velocity is optimal."
            })
            
        elif function_name == "map_technical_dependencies":
            return json.dumps({
                "status": "success",
                "critical_path_validated": True,
                "critical_path": arguments.get("critical_path", []),
                "parallel_tracks": arguments.get("parallel_tracks", []),
                "bottleneck_risk": "High" if len(arguments.get("critical_path", [])) > 5 else "Low"
            })
            
        else:
            return f"Error: Tool '{function_name}' not recognized by PriyaAgent."
