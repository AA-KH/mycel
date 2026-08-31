from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="creative",
    company_id="mycel_global",
    name="Creative Team",
    slug="creative",
    description="Creative production including visual, video and multimedia content.",
    status=CompanyStatus.ACTIVE
)
