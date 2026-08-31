from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="legal",
    company_id="mycel_global",
    name="Legal Team",
    slug="legal",
    description="Legal research, document analysis and jurisdiction-aware legal drafting.",
    status=CompanyStatus.ACTIVE
)
