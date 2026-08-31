import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")

def ensure_init(directory):
    directory.mkdir(parents=True, exist_ok=True)
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

def create_position_file(team_id, position_id, class_name, name, purpose, p_type, seniority, skills, pipelines, outputs):
    team_dir = BACKEND_DIR / "teams" / team_id.replace("team_", "").replace("engineering_", "developer")
    # Actually let's use the explicit folder names from the prompt: 
    # developer, research, creative, legal, marketing, finance, operations
    folder_map = {
        "team_engineering": "developer",
        "team_backend": "developer", # Kabir is in team_backend, which belongs to Developer team conceptually? Actually the prompt says "teams/developer/..."
        "team_research": "research",
        "team_market_intel": "research",
        "team_creative": "creative",
        "team_creative_production": "creative",
        "team_legal": "legal",
        "team_marketing": "marketing",
        "team_finance": "finance",
        "team_operations": "operations"
    }
    
    # Wait, the prompt says the teams are exactly developer, research, creative, legal, marketing, finance, operations.
    folder_name = team_id
    
    positions_dir = BACKEND_DIR / "teams" / folder_name / "positions"
    ensure_init(positions_dir)
    
    file_path = positions_dir / f"{position_id}.py"
    
    skills_str = ", ".join([f'PositionSkillRequirement(skill_id="{s}", minimum_proficiency=70, required=True)' for s in skills])
    pipelines_str = ", ".join([f'"{p}"' for p in pipelines])
    outputs_str = ", ".join([f'"{o}"' for o in outputs])
    
    content = f"""from workforce.positions.models import (
    Position, PositionStatus, PositionType, Seniority, Criticality,
    PositionSkillRequirement, PositionToolRequirement, PositionKnowledgeRequirement,
    PositionReasoningRequirement, WorkforceRequirement, Requiredness
)

{position_id} = Position(
    position_id="{position_id}",
    team_id="{folder_name}",
    name="{name}",
    display_name="{name}",
    purpose="{purpose}",
    status=PositionStatus.ACTIVE,
    position_type=PositionType.{p_type},
    seniority=Seniority.{seniority},
    criticality=Criticality.HIGH,
    workforce=WorkforceRequirement(min_headcount=1, max_headcount=5, recommended_headcount=2, requiredness=Requiredness.REQUIRED),
    required_skills=[{skills_str}],
    pipeline_responsibilities=[{pipelines_str}],
    output_responsibilities=[{outputs_str}]
)
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"Created {file_path}")

# DEVELOPER
create_position_file("developer", "backend_engineer", "BackendEngineer", "Backend Engineer", "Design, implement and maintain production backend services, APIs and data integrations.", "SPECIALIST", "MID", ["python", "api_development", "database_design"], ["development_pipeline"], ["backend_service"])
create_position_file("developer", "frontend_engineer", "FrontendEngineer", "Frontend Engineer", "Design, implement and maintain production user interfaces and frontend web applications.", "SPECIALIST", "MID", ["react", "typescript", "ui_development"], ["development_pipeline"], ["frontend_application"])
create_position_file("developer", "qa_engineer", "QAEngineer", "QA Engineer", "Design, implement and execute automated and manual testing strategies.", "SPECIALIST", "MID", ["testing", "test_automation", "quality_assurance"], ["testing_pipeline"], ["test_suite"])
create_position_file("developer", "devops_engineer", "DevOpsEngineer", "DevOps Engineer", "Manage cloud infrastructure, deployment pipelines, and operational reliability.", "SPECIALIST", "MID", ["deployment", "containers", "infrastructure"], ["deployment_pipeline"], ["infrastructure_config"])

# RESEARCH
create_position_file("research", "research_lead", "ResearchLead", "Research Lead", "Guide research strategies and oversee execution of complex analysis tasks.", "LEADERSHIP", "LEAD", ["research_strategy", "management"], ["research_pipeline"], ["research_strategy"])
create_position_file("research", "researcher", "Researcher", "Researcher", "Discover, collect, and verify information from diverse sources to produce reports.", "INDIVIDUAL_CONTRIBUTOR", "MID", ["web_research", "data_synthesis"], ["source_verification_pipeline"], ["research_report"])
create_position_file("research", "research_analyst", "ResearchAnalyst", "Research Analyst", "Analyze collected data to extract actionable insights and trends.", "SPECIALIST", "MID", ["data_analysis", "trend_forecasting"], ["research_pipeline"], ["analysis_report"])
create_position_file("research", "research_writer", "ResearchWriter", "Research Writer", "Synthesize findings into highly readable, professional reports.", "SPECIALIST", "MID", ["technical_writing", "editing"], ["research_pipeline"], ["published_report"])

# CREATIVE
create_position_file("creative", "creative_strategist", "CreativeStrategist", "Creative Strategist", "Define brand direction and conceptualize marketing campaigns.", "LEADERSHIP", "SENIOR", ["creative_direction", "branding"], ["creative_pipeline"], ["campaign_strategy"])
create_position_file("creative", "video_producer", "VideoProducer", "Video Producer", "Oversee and manage the end-to-end production of promotional videos.", "INDIVIDUAL_CONTRIBUTOR", "MID", ["video_production", "storytelling"], ["promotional_video_pipeline"], ["promotional_video"])
create_position_file("creative", "video_editor", "VideoEditor", "Video Editor", "Assemble, edit, and apply visual effects to video media.", "SPECIALIST", "MID", ["video_editing", "motion_graphics"], ["video_editing_pipeline"], ["edited_video"])
create_position_file("creative", "graphic_designer", "GraphicDesigner", "Graphic Designer", "Design visual assets, illustrations, and marketing imagery.", "SPECIALIST", "MID", ["visual_design", "illustration"], ["creative_pipeline"], ["marketing_image"])

# LEGAL
create_position_file("legal", "legal_researcher", "LegalResearcher", "Legal Researcher", "Research legal precedents, case law, and statutory regulations.", "SPECIALIST", "MID", ["legal_research", "statutory_analysis"], ["legal_research_pipeline"], ["legal_memo"])
create_position_file("legal", "legal_analyst", "LegalAnalyst", "Legal Analyst", "Analyze contracts and identify legal risks in corporate operations.", "SPECIALIST", "MID", ["contract_analysis", "risk_assessment"], ["legal_review_pipeline"], ["risk_assessment_report"])
create_position_file("legal", "legal_reviewer", "LegalReviewer", "Legal Reviewer", "Review and approve legal documents for compliance and accuracy.", "REVIEWER", "SENIOR", ["legal_review", "compliance"], ["legal_approval_pipeline"], ["approved_contract"])
create_position_file("legal", "compliance_analyst", "ComplianceAnalyst", "Compliance Analyst", "Ensure corporate activities adhere to regulatory compliance standards.", "SPECIALIST", "MID", ["regulatory_compliance", "auditing"], ["compliance_pipeline"], ["compliance_report"])

# MARKETING
create_position_file("marketing", "marketing_strategist", "MarketingStrategist", "Marketing Strategist", "Develop and execute go-to-market strategies and marketing campaigns.", "LEADERSHIP", "SENIOR", ["marketing_strategy", "campaign_management"], ["marketing_pipeline"], ["marketing_plan"])
create_position_file("marketing", "content_creator", "ContentCreator", "Content Creator", "Produce engaging written and visual content for marketing channels.", "INDIVIDUAL_CONTRIBUTOR", "MID", ["copywriting", "content_creation"], ["content_pipeline"], ["marketing_copy"])
create_position_file("marketing", "social_media_specialist", "SocialMediaSpecialist", "Social Media Specialist", "Manage social media presence and community engagement.", "SPECIALIST", "MID", ["social_media_management", "community_engagement"], ["social_pipeline"], ["social_post"])
create_position_file("marketing", "marketing_analyst", "MarketingAnalyst", "Marketing Analyst", "Analyze campaign performance and market trends to optimize ROI.", "SPECIALIST", "MID", ["marketing_analytics", "performance_tracking"], ["marketing_analytics_pipeline"], ["performance_report"])

# FINANCE
create_position_file("finance", "finance_analyst", "FinanceAnalyst", "Finance Analyst", "Analyze financial data, prepare models, and generate financial reports.", "SPECIALIST", "MID", ["financial_modeling", "data_analysis"], ["finance_pipeline"], ["financial_report"])
create_position_file("finance", "financial_planner", "FinancialPlanner", "Financial Planner", "Develop financial plans, budgets, and forecasts for the organization.", "SPECIALIST", "SENIOR", ["budgeting", "forecasting"], ["planning_pipeline"], ["budget_plan"])
create_position_file("finance", "accounts_specialist", "AccountsSpecialist", "Accounts Specialist", "Manage accounts payable/receivable and reconcile financial statements.", "INDIVIDUAL_CONTRIBUTOR", "MID", ["accounting", "reconciliation"], ["accounts_pipeline"], ["reconciliation_report"])
create_position_file("finance", "finance_reviewer", "FinanceReviewer", "Finance Reviewer", "Review and approve financial models, budgets, and compliance reports.", "REVIEWER", "SENIOR", ["financial_review", "compliance"], ["finance_approval_pipeline"], ["approved_budget"])

# OPERATIONS
create_position_file("operations", "operations_manager", "OperationsManager", "Operations Manager", "Oversee day-to-day operations and ensure process efficiency.", "LEADERSHIP", "SENIOR", ["operations_management", "process_optimization"], ["operations_pipeline"], ["operations_strategy"])
create_position_file("operations", "operations_coordinator", "OperationsCoordinator", "Operations Coordinator", "Coordinate resources, schedules, and cross-functional operational tasks.", "INDIVIDUAL_CONTRIBUTOR", "MID", ["project_coordination", "logistics"], ["coordination_pipeline"], ["schedule"])
create_position_file("operations", "process_analyst", "ProcessAnalyst", "Process Analyst", "Analyze and improve operational workflows and standard operating procedures.", "SPECIALIST", "MID", ["process_analysis", "workflow_design"], ["process_pipeline"], ["process_document"])
create_position_file("operations", "operations_reviewer", "OperationsReviewer", "Operations Reviewer", "Review operational metrics and approve process changes.", "REVIEWER", "SENIOR", ["performance_review", "quality_assurance"], ["operations_review_pipeline"], ["performance_review"])

# UPDATE TEAM MEMBERS
def replace_in_file(filepath, replacements):
    try:
        content = filepath.read_text(encoding="utf-8")
        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error updating {filepath}: {e}")

kabir_py = BACKEND_DIR / "teams/developer/team_members/emp_kabir_sharma/profile.py"
replace_in_file(kabir_py, [('position_id="pos_backend_engineer"', 'position_id="backend_engineer"')])

aarav_py = BACKEND_DIR / "teams/research/team_members/emp_aarav_mehta/profile.py"
replace_in_file(aarav_py, [('position_id="pos_research_specialist"', 'position_id="researcher"')])

riya_py = BACKEND_DIR / "teams/creative/team_members/emp_riya_sharma/profile.py"
replace_in_file(riya_py, [('position_id="pos_video_producer"', 'position_id="video_producer"')])

print("Positions generated and team members updated.")
