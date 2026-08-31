import os
import shutil

BASE_DIR = r"d:\Projects\mycel\backend\teams"

# 1. Wipe old prototype folders
OLD_TEAMS = ["research", "planning", "resilience", "strategy", "architecture", "executive"]
for t in OLD_TEAMS:
    path = os.path.join(BASE_DIR, t)
    if os.path.exists(path):
        shutil.rmtree(path)

# 2. Final Architecture Definition
TEAMS = {
    "executive": {
        "description": "Chief Supply Chain Architect and Orchestration.",
        "members": {
            "Atlas": "Chief Supply Chain Architect / orchestration"
        }
    },
    "intelligence": {
        "description": "Market, demand, and risk intelligence.",
        "members": {
            "Mira": "Market & demand intelligence",
            "Ravi": "Supplier intelligence",
            "Anika": "Industry & supply-chain benchmarking",
            "Noor": "Geopolitical/external risk intelligence"
        }
    },
    "network": {
        "description": "Supply chain design, logistics, and capacity planning.",
        "members": {
            "Aanya": "Supply-chain network design",
            "Dev": "Procurement & total landed cost",
            "Kabir": "Logistics & fulfillment",
            "Tara": "Inventory & capacity planning"
        }
    },
    "resilience": {
        "description": "Risk mapping, stress testing, and continuity planning.",
        "members": {
            "Zoya": "Failure/risk mapping",
            "Ishaan": "Disruption scenario generation",
            "Leena": "Stress testing",
            "Arjun": "Continuity & recovery planning"
        }
    },
    "council": {
        "description": "Strategic alignment and compliance.",
        "members": {
            "Helena": "Cost strategist",
            "Vikram": "Resilience strategist",
            "Nisha": "Operations strategist",
            "Omar": "Risk/compliance strategist",
            "Sofia": "Council chair"
        }
    },
    "architecture": {
        "description": "Master supply-chain network construction and validation.",
        "members": {
            "Rohan": "Master supply-chain architect",
            "Priya": "Implementation planner",
            "Ethan": "Independent validator"
        }
    }
}

TEAM_PY_TEMPLATE = """from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="{team_id}",
    company_id="mycel",
    slug="{team_id}",
    name="{team_name}",
    description="{description}",
    status=CompanyStatus.ACTIVE
)
"""

PIPELINE_PY_TEMPLATE = """from execution.pipelines.models import TeamPipeline, PipelineInputContract, PipelineStatus

pipeline_instance = TeamPipeline(
    pipeline_id="{team_id}_default",
    team_id="{team_id}",
    name="default_{team_id}_pipeline",
    display_name="Default {team_name} Pipeline",
    description="Standard execution pipeline for {team_id} tasks.",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(
        input_type="task_request",
        required=True,
        description="Standard task input"
    ),
    stages=[]
)
"""

PROFILE_PY_TEMPLATE = """from workforce.employees.models import Employee, EmployeeIdentity

{member_lower} = Employee(
    employee_id="{member_lower}",
    team_id="{team_id}",
    name="{member_name}",
    identity=EmployeeIdentity(
        first_name="{member_name}",
        last_name="",
        title="{responsibility}",
        specialization="scm_{team_id}",
        seniority="Senior",
        background="Expert in {responsibility}."
    ),
    reasoning_profile_id="standard"
)
"""

def generate():
    os.makedirs(BASE_DIR, exist_ok=True)
        
    for team_id, data in TEAMS.items():
        team_dir = os.path.join(BASE_DIR, team_id)
        os.makedirs(team_dir, exist_ok=True)
        
        # __init__.py
        open(os.path.join(team_dir, "__init__.py"), "w").close()
        
        # team.py
        with open(os.path.join(team_dir, "team.py"), "w") as f:
            f.write(TEAM_PY_TEMPLATE.format(
                team_id=team_id,
                team_name=team_id.capitalize(),
                description=data["description"]
            ))
            
        # pipelines
        pipelines_dir = os.path.join(team_dir, "pipelines")
        os.makedirs(pipelines_dir, exist_ok=True)
        open(os.path.join(pipelines_dir, "__init__.py"), "w").close()
        
        with open(os.path.join(pipelines_dir, "default_pipeline.py"), "w") as f:
            f.write(PIPELINE_PY_TEMPLATE.format(
                team_id=team_id,
                team_name=team_id.capitalize()
            ))
            
        # members
        members_dir = os.path.join(team_dir, "team_members")
        os.makedirs(members_dir, exist_ok=True)
        open(os.path.join(members_dir, "__init__.py"), "w").close()
        
        for member_name, responsibility in data["members"].items():
            member_lower = member_name.lower()
            emp_dir = os.path.join(members_dir, member_lower)
            os.makedirs(emp_dir, exist_ok=True)
            open(os.path.join(emp_dir, "__init__.py"), "w").close()
            
            with open(os.path.join(emp_dir, "profile.py"), "w") as f:
                f.write(PROFILE_PY_TEMPLATE.format(
                    member_lower=member_lower,
                    team_id=team_id,
                    member_name=member_name,
                    responsibility=responsibility
                ))
                
    print("Final SCM teams generated successfully!")

if __name__ == "__main__":
    generate()
