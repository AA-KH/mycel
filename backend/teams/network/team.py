from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="network",
    company_id="mycel",
    slug="network",
    name="Network",
    description="Supply chain design, logistics, and capacity planning.",
    status=CompanyStatus.ACTIVE
)
