from workforce.baseline_members.models import BaselineMember, BaselineSkillProficiency, BaselineStatus

senior_lawyer_baseline = BaselineMember(
    baseline_member_id="legal_senior_lawyer_baseline",
    team_id="legal",
    position_id="senior_lawyer",
    display_name="Baseline Senior Lawyer",
    description="Baseline template for senior lawyer position.",
    status=BaselineStatus.ACTIVE,
    skills={
        "legal_research": BaselineSkillProficiency(level=85),
        "document_analysis": BaselineSkillProficiency(level=90),
        "contract_analysis": BaselineSkillProficiency(level=85),
        "compliance_analysis": BaselineSkillProficiency(level=80),
        "legal_writing": BaselineSkillProficiency(level=85),
        "citation_validation": BaselineSkillProficiency(level=80)
    },
    tools=["legal_document_parser", "rag_retrieval", "document_search", "citation_tools", "document_generation"]
)
