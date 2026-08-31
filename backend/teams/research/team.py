from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="research",
    company_id="mycel_global",
    name="Research Team",
    slug="research",
    description="Research, evidence collection, verification, analysis and knowledge synthesis.",
    status=CompanyStatus.ACTIVE
)
