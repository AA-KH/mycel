import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")

def ensure_init(directory):
    directory.mkdir(parents=True, exist_ok=True)
    init_file = directory / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

def create_baseline_file(team_id, position_id, class_name, name, purpose, skills, tools):
    baseline_dir = BACKEND_DIR / "teams" / team_id / "team_members" / "baseline"
    ensure_init(baseline_dir)
    
    file_path = baseline_dir / f"{position_id}.py"
    
    baseline_member_id = f"{team_id}_{position_id}_baseline"
    
    skills_dict = ",\n        ".join([f'"{s}": BaselineSkillProficiency(level=70)' for s in skills])
    tools_list = ", ".join([f'"{t}"' for t in tools])
    
    content = f"""from workforce.baseline_members.models import BaselineMember, BaselineSkillProficiency, BaselineStatus

{class_name} = BaselineMember(
    baseline_member_id="{baseline_member_id}",
    team_id="{team_id}",
    position_id="{position_id}",
    display_name="Baseline {name}",
    description="{purpose}",
    status=BaselineStatus.ACTIVE,
    skills={{
        {skills_dict}
    }},
    tools=[{tools_list}]
)
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"Created {file_path}")


# DEVELOPER
create_baseline_file("developer", "backend_engineer", "developer_backend_baseline", "Backend Engineer", "Baseline template for backend engineering.", ["python", "api_development", "database_design"], ["git", "github", "terminal"])
create_baseline_file("developer", "frontend_engineer", "developer_frontend_baseline", "Frontend Engineer", "Baseline template for frontend engineering.", ["react", "typescript", "ui_development"], ["git", "github", "terminal"])
create_baseline_file("developer", "qa_engineer", "developer_qa_baseline", "QA Engineer", "Baseline template for QA engineering.", ["testing", "test_automation", "quality_assurance"], ["git", "github", "terminal"])
create_baseline_file("developer", "devops_engineer", "developer_devops_baseline", "DevOps Engineer", "Baseline template for devops engineering.", ["deployment", "containers", "infrastructure"], ["git", "github", "terminal"])

# RESEARCH
create_baseline_file("research", "research_lead", "research_lead_baseline", "Research Lead", "Baseline template for research leadership.", ["research_strategy", "management"], ["web_browser", "document_editor"])
create_baseline_file("research", "researcher", "research_researcher_baseline", "Researcher", "Baseline template for researcher.", ["web_research", "data_synthesis"], ["web_browser", "document_editor"])
create_baseline_file("research", "research_analyst", "research_analyst_baseline", "Research Analyst", "Baseline template for research analysis.", ["data_analysis", "trend_forecasting"], ["web_browser", "document_editor"])
create_baseline_file("research", "research_writer", "research_writer_baseline", "Research Writer", "Baseline template for research writing.", ["technical_writing", "editing"], ["web_browser", "document_editor"])

# CREATIVE
create_baseline_file("creative", "creative_strategist", "creative_strategist_baseline", "Creative Strategist", "Baseline template for creative strategy.", ["creative_direction", "branding"], ["design_tool", "presentation_software"])
create_baseline_file("creative", "video_producer", "creative_video_producer_baseline", "Video Producer", "Baseline template for video production.", ["video_production", "storytelling"], ["video_editor", "asset_manager"])
create_baseline_file("creative", "video_editor", "creative_video_editor_baseline", "Video Editor", "Baseline template for video editing.", ["video_editing", "motion_graphics"], ["video_editor", "asset_manager"])
create_baseline_file("creative", "graphic_designer", "creative_graphic_designer_baseline", "Graphic Designer", "Baseline template for graphic design.", ["visual_design", "illustration"], ["design_tool", "asset_manager"])

# LEGAL
create_baseline_file("legal", "legal_researcher", "legal_researcher_baseline", "Legal Researcher", "Baseline template for legal research.", ["legal_research", "statutory_analysis"], ["legal_database", "document_editor"])
create_baseline_file("legal", "legal_analyst", "legal_analyst_baseline", "Legal Analyst", "Baseline template for legal analysis.", ["contract_analysis", "risk_assessment"], ["contract_manager", "document_editor"])
create_baseline_file("legal", "legal_reviewer", "legal_reviewer_baseline", "Legal Reviewer", "Baseline template for legal review.", ["legal_review", "compliance"], ["contract_manager", "document_editor"])
create_baseline_file("legal", "compliance_analyst", "compliance_analyst_baseline", "Compliance Analyst", "Baseline template for compliance analysis.", ["regulatory_compliance", "auditing"], ["compliance_tracker", "document_editor"])

# MARKETING
create_baseline_file("marketing", "marketing_strategist", "marketing_strategist_baseline", "Marketing Strategist", "Baseline template for marketing strategy.", ["marketing_strategy", "campaign_management"], ["marketing_platform", "analytics_tool"])
create_baseline_file("marketing", "content_creator", "marketing_content_creator_baseline", "Content Creator", "Baseline template for content creation.", ["copywriting", "content_creation"], ["content_manager", "social_media_tool"])
create_baseline_file("marketing", "social_media_specialist", "marketing_social_media_specialist_baseline", "Social Media Specialist", "Baseline template for social media management.", ["social_media_management", "community_engagement"], ["social_media_tool"])
create_baseline_file("marketing", "marketing_analyst", "marketing_analyst_baseline", "Marketing Analyst", "Baseline template for marketing analytics.", ["marketing_analytics", "performance_tracking"], ["analytics_tool"])

# FINANCE
create_baseline_file("finance", "finance_analyst", "finance_analyst_baseline", "Finance Analyst", "Baseline template for finance analysis.", ["financial_modeling", "data_analysis"], ["spreadsheet_software", "financial_platform"])
create_baseline_file("finance", "financial_planner", "finance_planner_baseline", "Financial Planner", "Baseline template for financial planning.", ["budgeting", "forecasting"], ["spreadsheet_software", "financial_platform"])
create_baseline_file("finance", "accounts_specialist", "finance_accounts_specialist_baseline", "Accounts Specialist", "Baseline template for accounts management.", ["accounting", "reconciliation"], ["accounting_software"])
create_baseline_file("finance", "finance_reviewer", "finance_reviewer_baseline", "Finance Reviewer", "Baseline template for finance review.", ["financial_review", "compliance"], ["financial_platform", "document_editor"])

# OPERATIONS
create_baseline_file("operations", "operations_manager", "operations_manager_baseline", "Operations Manager", "Baseline template for operations management.", ["operations_management", "process_optimization"], ["project_management_tool", "analytics_tool"])
create_baseline_file("operations", "operations_coordinator", "operations_coordinator_baseline", "Operations Coordinator", "Baseline template for operations coordination.", ["project_coordination", "logistics"], ["project_management_tool"])
create_baseline_file("operations", "process_analyst", "operations_process_analyst_baseline", "Process Analyst", "Baseline template for process analysis.", ["process_analysis", "workflow_design"], ["process_mapping_tool"])
create_baseline_file("operations", "operations_reviewer", "operations_reviewer_baseline", "Operations Reviewer", "Baseline template for operations review.", ["performance_review", "quality_assurance"], ["project_management_tool", "document_editor"])

print("Baseline members generated.")
