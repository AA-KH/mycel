from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="executive",
    company_id="mycel",
    slug="executive",
    name="Executive",
    description="Chief Supply Chain Architect and Orchestration.",
    status=CompanyStatus.ACTIVE
)
