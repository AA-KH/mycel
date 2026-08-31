from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="marketing",
    company_id="mycel_global",
    name="Marketing Team",
    slug="marketing",
    description="Marketing strategy, campaign planning, content distribution and audience analysis.",
    status=CompanyStatus.ACTIVE
)
