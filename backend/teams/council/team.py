from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="council",
    company_id="mycel",
    slug="council",
    name="Council",
    description="Strategic alignment and compliance.",
    status=CompanyStatus.ACTIVE
)
