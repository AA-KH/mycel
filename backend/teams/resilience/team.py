from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="resilience",
    company_id="mycel",
    slug="resilience",
    name="Resilience",
    description="Risk mapping, stress testing, and continuity planning.",
    status=CompanyStatus.ACTIVE
)
