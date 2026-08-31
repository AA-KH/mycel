from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from workforce.employees.models import Employee

class ExecutionSnapshot(BaseModel):
    """
    An immutable snapshot of an employee at the time of execution.
    Ensures that if the employee definition changes midway, the execution isn't impacted.
    """
    employee_id: str
    employee_version: str # e.g., git hash, updated_at timestamp, or explicit version
    team_id: str = "default"  # Used for team-level API key routing
    
    identity_summary: str
    title: str
    personality: str
    communication_style: str
    
    skills: Dict[str, Any] = Field(default_factory=dict)
    reasoning_profile_id: str
    tools: List[str] = Field(default_factory=list)
    permissions: Dict[str, Any] = Field(default_factory=dict)
    memory_config: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_employee(cls, employee: Employee) -> 'ExecutionSnapshot':
        """Constructs a safe execution snapshot from a current employee definition."""
        return cls(
            employee_id=employee.employee_id,
            employee_version=str(employee.updated_at.timestamp()) if employee.updated_at else "1.0",
            team_id=getattr(employee, "team_id", "default") or "default",
            identity_summary=employee.identity.summary,
            title=employee.identity.title,
            personality=employee.identity.personality,
            communication_style=employee.identity.communication_style,
            skills={s_name: s.level for s_name, s in employee.skills.items()} if hasattr(employee, 'skills') else {},
            reasoning_profile_id=employee.reasoning_profile_id,
            tools=employee.tools if hasattr(employee, 'tools') and employee.tools else [],
            permissions={k: v.value for k, v in employee.permissions.items()} if hasattr(employee, 'permissions') and employee.permissions else {},
            memory_config=employee.memory_config.model_dump() if hasattr(employee, 'memory_config') and employee.memory_config else {},
        )

    class Config:
        frozen = True
