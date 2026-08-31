from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="finance",
    company_id="mycel_global",
    name="Finance Team",
    slug="finance",
    description="Financial analysis, budgeting, reporting and financial operations.",
    status=CompanyStatus.ACTIVE
)
