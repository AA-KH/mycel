from fastapi import APIRouter, Depends, HTTPException
from core.mongodb import mongodb_connection
from core.security import get_current_operator, CurrentOperatorDep

router = APIRouter()

@router.get("/{project_id}")
async def get_project(project_id: str, operator: CurrentOperatorDep):
    db = mongodb_connection.db
    project = await db.projects.find_one({"project_id": project_id, "user_id": operator.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
