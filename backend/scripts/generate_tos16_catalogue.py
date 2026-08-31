import os
import textwrap
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
TEAMS_DIR = BACKEND_DIR / "teams"
TESTS_DIR = BACKEND_DIR / "tests" / "teams"

TEAMS_DEF = {
    "developer": {
        "name": "Developer Team",
        "purpose": "Software engineering and technical product development.",
        "skills": ["programming", "software engineering", "system design", "debugging", "testing", "API development", "code review"],
        "tools": ["git", "github", "terminal", "code execution", "repository access"],
        "knowledge": ["software engineering", "software architecture", "design patterns", "testing practices"],
        "reasoning": "engineering_reasoning",
        "pipelines": ["development_pipeline"],
        "outputs": ["source_code", "software_component", "API", "technical_document"],
        "positions": ["backend_engineer", "frontend_engineer", "qa_engineer", "devops_engineer"],
        "members": [
            {"id": "emp_dev_backend_001", "pos": "backend_engineer", "name": "Kabir Sharma", "spec": "FastAPI + Python"},
            {"id": "emp_dev_frontend_001", "pos": "frontend_engineer", "name": "Ananya Mehta", "spec": "React + TypeScript"},
            {"id": "emp_dev_qa_001", "pos": "qa_engineer", "name": "Rohan Verma", "spec": "Testing + API automation"},
            {"id": "emp_dev_devops_001", "pos": "devops_engineer", "name": "Ishita Kapoor", "spec": "Docker + CI/CD"}
        ]
    },
    "research": {
        "name": "Research Team",
        "purpose": "Research, evidence collection, verification, analysis and knowledge synthesis.",
        "skills": ["research", "information retrieval", "source analysis", "fact verification", "data analysis", "synthesis"],
        "tools": ["web search", "web scraping", "browser", "document parsing", "data extraction"],
        "knowledge": ["research methodology", "source evaluation", "academic research", "information verification"],
        "reasoning": "research_verify",
        "pipelines": ["research_pipeline"],
        "outputs": ["research_report", "research_summary", "evidence_table", "analysis_document"],
        "positions": ["researcher", "research_analyst", "fact_checker", "research_writer"],
        "members": [
            {"id": "emp_res_researcher_001", "pos": "researcher", "name": "Aarav Mehta", "spec": "web research"},
            {"id": "emp_res_analyst_001", "pos": "research_analyst", "name": "Meera Sharma", "spec": "data analysis"},
            {"id": "emp_res_factchecker_001", "pos": "fact_checker", "name": "Aditya Rao", "spec": "source verification"},
            {"id": "emp_res_writer_001", "pos": "research_writer", "name": "Nisha Kapoor", "spec": "technical writing"}
        ]
    },
    "creative": {
        "name": "Creative Team",
        "purpose": "Creative production including visual, video and multimedia content.",
        "skills": ["creative ideation", "visual communication", "storytelling", "content production", "editing", "creative review"],
        "tools": ["image generation", "video generation", "video editing", "Manim", "media processing"],
        "knowledge": ["visual design", "storytelling", "content principles", "brand communication"],
        "reasoning": "creative_review",
        "pipelines": ["creative_pipeline"],
        "outputs": ["image", "video", "promotional_video", "animation", "creative_asset"],
        "positions": ["creative_director", "video_editor", "motion_designer", "content_creator"],
        "members": [
            {"id": "emp_cre_director_001", "pos": "creative_director", "name": "Riya Sharma", "spec": "visual direction"},
            {"id": "emp_cre_editor_001", "pos": "video_editor", "name": "Arjun Malhotra", "spec": "video editing, FFmpeg"},
            {"id": "emp_cre_motion_001", "pos": "motion_designer", "name": "Kavya Mehta", "spec": "Manim, motion graphics"},
            {"id": "emp_cre_creator_001", "pos": "content_creator", "name": "Vihaan Kapoor", "spec": "copywriting, scripting"}
        ]
    },
    "legal": {
        "name": "Legal Team",
        "purpose": "Legal research, document analysis and jurisdiction-aware legal drafting.",
        "skills": ["legal research", "legal document analysis", "citation", "case analysis", "contract analysis", "legal writing"],
        "tools": ["legal document parser", "RAG retrieval", "document search", "citation tools", "document generation"],
        "knowledge": ["Indian legal system", "Indian statutes", "Indian regulations", "Indian case law", "legal terminology"],
        "reasoning": "legal_authority_verification",
        "pipelines": ["legal_pipeline"],
        "outputs": ["legal_research_report", "legal_summary", "legal_document", "contract_draft"],
        "positions": ["legal_researcher", "legal_analyst", "contract_specialist", "legal_reviewer"],
        "members": [
            {"id": "emp_leg_researcher_001", "pos": "legal_researcher", "name": "Aditi Sharma", "spec": "legal research"},
            {"id": "emp_leg_analyst_001", "pos": "legal_analyst", "name": "Raghav Mehta", "spec": "case analysis"},
            {"id": "emp_leg_contract_001", "pos": "contract_specialist", "name": "Isha Verma", "spec": "contract drafting"},
            {"id": "emp_leg_reviewer_001", "pos": "legal_reviewer", "name": "Armaan Kapoor", "spec": "legal review"}
        ]
    },
    "marketing": {
        "name": "Marketing Team",
        "purpose": "Marketing strategy, campaign planning, content distribution and audience analysis.",
        "skills": ["market research", "campaign planning", "content strategy", "audience analysis", "marketing analytics"],
        "tools": ["web research", "analytics", "social media tooling", "content generation", "campaign planning"],
        "knowledge": ["marketing principles", "consumer behavior", "branding", "digital marketing"],
        "reasoning": "marketing_strategy",
        "pipelines": ["marketing_pipeline"],
        "outputs": ["marketing_plan", "campaign", "social_media_content", "campaign_report"],
        "positions": ["marketing_strategist", "content_marketer", "growth_marketer", "marketing_analyst"],
        "members": [
            {"id": "emp_mkt_strategist_001", "pos": "marketing_strategist", "name": "Neha Sharma", "spec": "brand strategy"},
            {"id": "emp_mkt_content_001", "pos": "content_marketer", "name": "Karan Mehta", "spec": "copywriting"},
            {"id": "emp_mkt_growth_001", "pos": "growth_marketer", "name": "Simran Kapoor", "spec": "SEO"},
            {"id": "emp_mkt_analyst_001", "pos": "marketing_analyst", "name": "Dev Malhotra", "spec": "marketing analytics"}
        ]
    },
    "finance": {
        "name": "Finance Team",
        "purpose": "Financial analysis, budgeting, reporting and financial operations.",
        "skills": ["financial analysis", "budgeting", "forecasting", "reporting", "data analysis"],
        "tools": ["spreadsheet processing", "financial calculator", "data analysis", "document generation"],
        "knowledge": ["accounting fundamentals", "financial analysis", "budgeting", "financial reporting"],
        "reasoning": "financial_validation",
        "pipelines": ["finance_pipeline"],
        "outputs": ["financial_report", "budget", "forecast", "financial_analysis"],
        "positions": ["financial_analyst", "accounting_specialist", "budget_analyst"],
        "members": [
            {"id": "emp_fin_analyst_001", "pos": "financial_analyst", "name": "Priya Sharma", "spec": "financial modeling"},
            {"id": "emp_fin_accounting_001", "pos": "accounting_specialist", "name": "Rahul Mehta", "spec": "bookkeeping"},
            {"id": "emp_fin_budget_001", "pos": "budget_analyst", "name": "Sneha Kapoor", "spec": "forecasting"}
        ]
    },
    "operations": {
        "name": "Operations Team",
        "purpose": "Operational planning, process execution, coordination and workflow management.",
        "skills": ["process management", "task coordination", "workflow planning", "documentation", "operations analysis"],
        "tools": ["task management", "workflow automation", "document processing", "communication tools"],
        "knowledge": ["operations management", "process design", "SOPs", "workflow management"],
        "reasoning": "operational_planning",
        "pipelines": ["operations_pipeline"],
        "outputs": ["operations_report", "workflow", "SOP", "execution_plan"],
        "positions": ["operations_manager", "project_coordinator", "process_analyst", "operations_specialist"],
        "members": [
            {"id": "emp_ops_manager_001", "pos": "operations_manager", "name": "Ananya Verma", "spec": "resource planning"},
            {"id": "emp_ops_coordinator_001", "pos": "project_coordinator", "name": "Rohit Sharma", "spec": "scheduling"},
            {"id": "emp_ops_analyst_001", "pos": "process_analyst", "name": "Kriti Mehta", "spec": "process optimization"},
            {"id": "emp_ops_specialist_001", "pos": "operations_specialist", "name": "Samar Kapoor", "spec": "workflow execution"}
        ]
    }
}

def write_team_file(team_dir: Path, tid: str, props: dict):
    content = f"""from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="{tid}",
    company_id="mycel_global",
    name="{props['name']}",
    slug="{tid}",
    description="{props['purpose']}",
    status=CompanyStatus.ACTIVE
)
"""
    (team_dir / "team.py").write_text(content, encoding="utf-8")

def write_common_capabilities(team_dir: Path, props: dict):
    common_dir = team_dir / "common"
    common_dir.mkdir(exist_ok=True)
    content = f"""COMMON_SKILLS = {props['skills']}
COMMON_TOOLS = {props['tools']}
COMMON_KNOWLEDGE = {props['knowledge']}
COMMON_REASONING = "{props['reasoning']}"
"""
    (common_dir / "capabilities.py").write_text(content, encoding="utf-8")

def write_pipelines(team_dir: Path, tid: str, props: dict):
    pipelines_dir = team_dir / "pipelines"
    pipelines_dir.mkdir(exist_ok=True)
    pipe_id = props['pipelines'][0]
    out = props['outputs'][0] if props['outputs'] else 'report'
    
    content = f"""from execution.pipelines.models import TeamPipeline, PipelineInputContract

pipeline_instance = TeamPipeline(
    pipeline_id="{pipe_id}",
    team_id="{tid}",
    name="main",
    display_name="Main {props['name']} Pipeline",
    input_contract=PipelineInputContract(input_type="task"),
    output_contract_id="{out}",
    stages=[]
)
"""
    (pipelines_dir / f"{pipe_id}.py").write_text(content, encoding="utf-8")

def write_positions(team_dir: Path, tid: str, props: dict):
    positions_dir = team_dir / "positions"
    positions_dir.mkdir(exist_ok=True)
    for pos in props["positions"]:
        content = f"""# Stub for {pos} position definition
POSITION_ID = "{pos}"
TEAM_ID = "{tid}"
"""
        (positions_dir / f"{pos}.py").write_text(content, encoding="utf-8")

def write_members(team_dir: Path, tid: str, props: dict):
    members_dir = team_dir / "team_members"
    members_dir.mkdir(exist_ok=True)
    
    for member in props["members"]:
        content = f"""from workforce.employees.models import (
    Employee, EmployeeIdentity, Personality, PersonalityTraits, 
    Experience, EmployeeStatus, EmployeeAvailability
)

member_instance = Employee(
    employee_id="{member['id']}",
    company_id="mycel_global",
    department_id="default",
    team_id="{tid}",
    position_id="{member['pos']}",
    name="{member['name']}",
    display_name="{member['name']}",
    identity=EmployeeIdentity(
        title="{member['pos'].replace('_', ' ').title()}",
        specialization="{member['spec']}",
        summary="Baseline team member.",
        personality="Professional",
        communication_style="Direct",
        experience_level="Mid-level"
    ),
    personality=Personality(
        traits=PersonalityTraits(),
        communication_style="Direct",
        decision_style="Collaborative"
    ),
    experience=Experience(
        level="Mid-level",
        years_equivalent=3,
        domains=[]
    ),
    reasoning_profile_id="{props['reasoning']}",
    status=EmployeeStatus.ACTIVE,
    availability=EmployeeAvailability.AVAILABLE
)
"""
        (members_dir / f"{member['id']}.py").write_text(content, encoding="utf-8")

def generate_teams():
    for tid, props in TEAMS_DEF.items():
        team_dir = TEAMS_DIR / tid
        team_dir.mkdir(parents=True, exist_ok=True)
        (team_dir / "__init__.py").touch(exist_ok=True)
        
        write_team_file(team_dir, tid, props)
        write_common_capabilities(team_dir, props)
        write_pipelines(team_dir, tid, props)
        write_positions(team_dir, tid, props)
        write_members(team_dir, tid, props)

SEED_SCRIPT = """import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline
from workforce.employees.models import Employee

logger = logging.getLogger(__name__)

class TeamCatalogueSeed:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
    def load_teams(self) -> List[Team]:
        teams = []
        for child in self.base_dir.iterdir():
            if child.is_dir() and (child / "team.py").exists():
                try:
                    mod_path = f"teams.{child.name}.team"
                    spec = importlib.util.spec_from_file_location(mod_path, str(child / "team.py"))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    teams.append(mod.team_instance)
                except Exception as e:
                    logger.error(f"Failed to load team {child.name}: {e}")
        return teams

    def load_pipelines(self) -> List[TeamPipeline]:
        pipelines = []
        for team_dir in self.base_dir.iterdir():
            if not team_dir.is_dir(): continue
            pipe_dir = team_dir / "pipelines"
            if not pipe_dir.exists(): continue
            
            for pipe_file in pipe_dir.glob("*.py"):
                if pipe_file.name == "__init__.py": continue
                try:
                    mod_path = f"teams.{team_dir.name}.pipelines.{pipe_file.stem}"
                    spec = importlib.util.spec_from_file_location(mod_path, str(pipe_file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    pipelines.append(mod.pipeline_instance)
                except Exception as e:
                    pass
        return pipelines

    def load_members(self) -> List[Employee]:
        members = []
        for team_dir in self.base_dir.iterdir():
            if not team_dir.is_dir(): continue
            mem_dir = team_dir / "team_members"
            if not mem_dir.exists(): continue
            
            for mem_file in mem_dir.glob("*.py"):
                if mem_file.name == "__init__.py": continue
                try:
                    mod_path = f"teams.{team_dir.name}.team_members.{mem_file.stem}"
                    spec = importlib.util.spec_from_file_location(mod_path, str(mem_file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    members.append(mod.member_instance)
                except Exception as e:
                    pass
        return members

def seed():
    # Deterministic loading of the entire catalogue
    base = Path(__file__).parent
    seeder = TeamCatalogueSeed(base)
    
    teams = seeder.load_teams()
    pipelines = seeder.load_pipelines()
    members = seeder.load_members()
    
    return {
        "teams": teams,
        "pipelines": pipelines,
        "members": members
    }
"""

def generate_seed():
    (TEAMS_DIR / "seed.py").write_text(SEED_SCRIPT, encoding="utf-8")

TEST_SCRIPT = """import pytest
from pathlib import Path
from teams.seed import seed

def test_team_catalogue_idempotency():
    res1 = seed()
    res2 = seed()
    
    # Must be identical counts
    assert len(res1["teams"]) == len(res2["teams"])
    assert len(res1["members"]) == len(res2["members"])

def test_team_catalogue_counts():
    res = seed()
    
    assert len(res["teams"]) >= 7
    
    team_ids = [t.id for t in res["teams"]]
    assert "developer" in team_ids
    assert "research" in team_ids
    assert "creative" in team_ids
    
    assert len(res["members"]) >= 27
    member_ids = [m.employee_id for m in res["members"]]
    assert "emp_dev_backend_001" in member_ids
    
def test_member_isolation():
    res = seed()
    dev_members = [m for m in res["members"] if m.team_id == "developer"]
    assert len(dev_members) == 4
    for m in dev_members:
        assert "dev" in m.employee_id
        
def test_pipeline_validity():
    res = seed()
    team_ids = {t.id for t in res["teams"]}
    for p in res["pipelines"]:
        assert p.team_id in team_ids
"""

def generate_tests():
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    (TESTS_DIR / "test_team_seed.py").write_text(TEST_SCRIPT, encoding="utf-8")

if __name__ == "__main__":
    generate_teams()
    generate_seed()
    generate_tests()
    print("Generated TOS 16 Catalogue definition script completed successfully.")
