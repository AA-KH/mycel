import os
import shutil

base_dir = r"d:\Projects\agent-virtual-office\backend\organization"

dirs = ["company", "departments", "teams", "positions"]
for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    with open(os.path.join(base_dir, d, "__init__.py"), "w") as f:
        f.write("")

# MODELS
with open(os.path.join(base_dir, "company", "models.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class Company(BaseModel):
    id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
''')

with open(os.path.join(base_dir, "departments", "models.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class Department(BaseModel):
    id: Optional[str] = None
    company_id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
''')

with open(os.path.join(base_dir, "teams", "models.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class Team(BaseModel):
    id: Optional[str] = None
    company_id: str
    department_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    mission: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
''')

with open(os.path.join(base_dir, "positions", "models.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from organization.types import Level, PositionRequirements

class Position(BaseModel):
    id: Optional[str] = None
    company_id: str
    department_id: Optional[str] = None
    team_id: str
    title: str
    slug: str
    description: Optional[str] = None
    level: Level = Level.MID
    status: str = "open"  # open, closed, archived
    responsibilities: List[str] = Field(default_factory=list)
    requirements: PositionRequirements = Field(default_factory=PositionRequirements)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
''')

# Create __init__.py at organization root to export models to maintain backward compatibility
with open(os.path.join(base_dir, "models.py"), "w", encoding="utf-8") as f:
    f.write('''from organization.types import CompanyStatus, Level, PositionRequirements, CapabilityRequirement
from organization.company.models import Company
from organization.departments.models import Department
from organization.teams.models import Team
from workforce.positions.models import Position
''')

print("Models split successfully.")
