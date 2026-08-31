from workforce.employees.models import (
    Employee, EmployeeIdentity, Personality, PersonalityTraits, 
    Experience, EmployeeStatus, EmployeeAvailability
)

member_instance = Employee(
    employee_id="emp_leg_compliance_001",
    company_id="mycel_global",
    department_id="default",
    team_id="legal",
    position_id="compliance_analyst",
    name="Priya Nair",
    display_name="Priya Nair",
    identity=EmployeeIdentity(
        title="Compliance Analyst",
        specialization="compliance analysis",
        summary="Compliance analyst with expertise in regulatory compliance and risk assessment.",
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
        domains=["compliance_analysis", "document_analysis", "legal_research", "legal_writing"]
    ),
    reasoning_profile_id="compliance_risk_assessment",
    status=EmployeeStatus.ACTIVE,
    availability=EmployeeAvailability.AVAILABLE
)
