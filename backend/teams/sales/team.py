from organization.teams.models import Team
from organization.types import CompanyStatus

team_instance = Team(
    id="sales",
    company_id="mycel_global",
    name="Sales Team",
    slug="sales",
    description="Property sales, lead nurturing, customer requirements analysis and property recommendations.",
    status=CompanyStatus.ACTIVE
)
