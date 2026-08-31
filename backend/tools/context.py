from pydantic import BaseModel
from typing import Optional

class ToolExecutionContext(BaseModel):
    """
    Context passed to a Tool Executor and eventually to the Tool itself.
    """
    request_id: str
    execution_id: str
    task_id: str
    employee_id: str
    company_id: str
    workspace_id: Optional[str] = None
