from typing import Any, List
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
from workforce.positions.schemas import PositionCreate, PositionResponse

from organization.types import CompanyStatus, Level

class TreeTeamNode(BaseModel):
    id: str
    name: str
    slug: str
    status: CompanyStatus

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
