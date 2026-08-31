from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="intelligence",
    company_id="mycel",
    slug="intelligence",
    name="Intelligence",
    description="Market, demand, and risk intelligence.",
    status=CompanyStatus.ACTIVE
)
