from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="operations",
    company_id="mycel_global",
    name="Operations Team",
    slug="operations",
    description="Operational planning, process execution, coordination and workflow management.",
    status=CompanyStatus.ACTIVE
)
