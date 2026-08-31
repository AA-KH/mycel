from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="architecture",
    company_id="mycel",
    slug="architecture",
    name="Architecture",
    description="Master supply-chain network construction and validation.",
    status=CompanyStatus.ACTIVE
)
