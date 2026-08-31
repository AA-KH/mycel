import os

base_dir = r"d:\Projects\agent-virtual-office\backend\organization"

# 1. REPOSITORIES
with open(os.path.join(base_dir, "company", "repository.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Company

class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db):
        super().__init__(db, "companies", Company)

    async def get_by_slug(self, slug: str) -> Optional[Company]:
        docs = await self.find({"slug": slug}, limit=1)
        return docs[0] if docs else None
''')

with open(os.path.join(base_dir, "departments", "repository.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Department

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db):
        super().__init__(db, "departments", Department)

    async def get_by_slug(self, company_id: str, slug: str) -> Optional[Department]:
        docs = await self.find({"company_id": company_id, "slug": slug}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Department]:
        return await self.find({"company_id": company_id}, limit=1000)
''')

with open(os.path.join(base_dir, "teams", "repository.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Team

class TeamRepository(BaseRepository[Team]):
    def __init__(self, db):
        super().__init__(db, "teams", Team)

    async def get_by_slug(self, company_id: str, slug: str) -> Optional[Team]:
        docs = await self.find({"company_id": company_id, "slug": slug}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Team]:
        return await self.find({"company_id": company_id}, limit=1000)

    async def get_all_by_department(self, company_id: str, department_id: str) -> List[Team]:
        return await self.find({"company_id": company_id, "department_id": department_id}, limit=1000)
''')

with open(os.path.join(base_dir, "positions", "repository.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import List, Optional
from infrastructure.database.repositories.base import BaseRepository
from .models import Position

class PositionRepository(BaseRepository[Position]):
    def __init__(self, db):
        super().__init__(db, "positions", Position)

    async def get_by_slug(self, company_id: str, slug: str) -> Optional[Position]:
        docs = await self.find({"company_id": company_id, "slug": slug}, limit=1)
        return docs[0] if docs else None

    async def get_all_by_company(self, company_id: str) -> List[Position]:
        return await self.find({"company_id": company_id}, limit=1000)

    async def get_all_by_team(self, company_id: str, team_id: str) -> List[Position]:
        return await self.find({"company_id": company_id, "team_id": team_id}, limit=1000)
''')

with open(os.path.join(base_dir, "repositories.py"), "w", encoding="utf-8") as f:
    f.write('''from organization.company.repository import CompanyRepository
from organization.departments.repository import DepartmentRepository
from organization.teams.repository import TeamRepository
from workforce.positions.repository import PositionRepository
''')

# 2. SCHEMAS
with open(os.path.join(base_dir, "company", "schemas.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    settings: Dict[str, Any] = Field(default_factory=dict)

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[CompanyStatus] = None
    settings: Optional[Dict[str, Any]] = None

class CompanyResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
''')

with open(os.path.join(base_dir, "departments", "schemas.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[CompanyStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class DepartmentResponse(BaseModel):
    id: str
    company_id: str
    name: str
    slug: str
    description: Optional[str] = None
    status: CompanyStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
''')

with open(os.path.join(base_dir, "teams", "schemas.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from organization.types import CompanyStatus

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    mission: Optional[str] = None
    status: CompanyStatus = CompanyStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    mission: Optional[str] = None
    status: Optional[CompanyStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class TeamResponse(BaseModel):
    id: str
    company_id: str
    department_id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    mission: Optional[str] = None
    status: CompanyStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
''')

with open(os.path.join(base_dir, "positions", "schemas.py"), "w", encoding="utf-8") as f:
    f.write('''from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from organization.types import Level, PositionRequirements

class PositionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    level: Level = Level.MID
    responsibilities: List[str] = Field(default_factory=list)
    requirements: PositionRequirements = Field(default_factory=PositionRequirements)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PositionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    level: Optional[Level] = None
    status: Optional[str] = None  # open, closed, archived
    responsibilities: Optional[List[str]] = None
    requirements: Optional[PositionRequirements] = None
    metadata: Optional[Dict[str, Any]] = None

class PositionResponse(BaseModel):
    id: str
    company_id: str
    department_id: Optional[str] = None
    team_id: str
    title: str
    slug: str
    description: Optional[str] = None
    level: Level
    status: str
    responsibilities: List[str]
    requirements: PositionRequirements
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
''')

with open(os.path.join(base_dir, "schemas.py"), "w", encoding="utf-8") as f:
    f.write('''from typing import Any, List
from pydantic import BaseModel

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None

class PaginatedData(BaseModel):
    items: List[Any]
    total: int

from organization.company.schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from organization.departments.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from organization.teams.schemas import TeamCreate, TeamUpdate, TeamResponse
from workforce.positions.schemas import PositionCreate, PositionUpdate, PositionResponse

from organization.types import CompanyStatus, Level
class TreePositionNode(BaseModel):
    id: str
    title: str
    slug: str
    level: Level
    status: str

class TreeTeamNode(BaseModel):
    id: str
    name: str
    slug: str
    status: CompanyStatus
    positions: List[TreePositionNode]

class TreeDepartmentNode(BaseModel):
    id: str
    name: str
    slug: str
    status: CompanyStatus
    teams: List[TreeTeamNode]

class TreeCompanyNode(BaseModel):
    id: str
    name: str
    slug: str
    status: CompanyStatus

class OrganizationTreeResponse(BaseModel):
    company: TreeCompanyNode
    departments: List[TreeDepartmentNode]
''')

print("Schemas and Repositories split successfully.")
