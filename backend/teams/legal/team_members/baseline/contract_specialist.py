from workforce.baseline_members.models import BaselineMember, BaselineSkillProficiency, BaselineStatus

contract_specialist_baseline = BaselineMember(
    baseline_member_id="legal_contract_specialist_baseline",
    team_id="legal",
    position_id="contract_specialist",
    display_name="Baseline Contract Specialist",
    description="Baseline template for contract specialization.",
    status=BaselineStatus.ACTIVE,
    skills={
        "contract_analysis": BaselineSkillProficiency(level=85),
        "legal_writing": BaselineSkillProficiency(level=80),
        "document_analysis": BaselineSkillProficiency(level=75),
        "compliance_analysis": BaselineSkillProficiency(level=70)
    },
    tools=["legal_document_parser", "document_generation", "document_search"]
)
