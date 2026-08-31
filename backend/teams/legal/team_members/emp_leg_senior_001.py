from workforce.employees.models import (
    Employee, EmployeeIdentity, Personality, PersonalityTraits, 
    Experience, EmployeeStatus, EmployeeAvailability
)

member_instance = Employee(
    employee_id="emp_leg_senior_001",
    company_id="mycel_global",
    department_id="default",
    team_id="legal",
    position_id="senior_lawyer",
    name="Vikram Singh",
    display_name="Vikram Singh",
    identity=EmployeeIdentity(
        title="Senior Lawyer",
        specialization="legal strategy",
        summary="Senior lawyer with expertise in legal strategy, complex legal matters, and advisory services.",
        personality="Professional",
        communication_style="Direct",
        experience_level="Senior"
    ),
    personality=Personality(
        traits=PersonalityTraits(),
        communication_style="Direct",
        decision_style="Collaborative"
    ),
    experience=Experience(
        level="Senior",
        years_equivalent=8,
        domains=["legal_research", "document_analysis", "contract_analysis", "compliance_analysis", "legal_writing", "citation_validation"]
    ),
    reasoning_profile_id="legal_authority_verification",
    status=EmployeeStatus.ACTIVE,
    availability=EmployeeAvailability.AVAILABLE
)
