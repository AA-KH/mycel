from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="developer",
    company_id="mycel_global",
    name="Developer Team",
    slug="developer",
    description="Software engineering and technical product development.",
    status=CompanyStatus.ACTIVE
)
