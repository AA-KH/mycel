"""
Task Logger — maintains a full audit trail of all tasks in MongoDB.
Every step (planning, delegation, team results, final report) is recorded.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from core.mongodb import mongodb_connection
import logging

logger = logging.getLogger(__name__)

COLLECTION = "task_logs"


async def create_task_log(project_task: str, submitted_by: str = "human") -> str:
    """Create a new task log entry and return the task_id."""
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    doc = {
        "task_id": task_id,
        "project_task": project_task,
        "submitted_at": now,
        "submitted_by": submitted_by,
        "status": "queued",
        "manager_plan": None,
        "team_results": [],
        "final_report": None,
        "completed_at": None,
        "total_duration_seconds": None,
    }

    try:
        db = mongodb_connection.db
        await db[COLLECTION].insert_one(doc)
        logger.info(f"Task log created: {task_id}")
    except Exception as e:
        logger.error(f"Failed to create task log: {e}")

    return task_id


async def update_task_status(task_id: str, status: str):
    """Update top-level task status (queued | in_progress | complete | failed)."""
    try:
        db = mongodb_connection.db
        await db[COLLECTION].update_one(
            {"task_id": task_id},
            {"$set": {"status": status}}
        )
    except Exception as e:
        logger.error(f"Failed to update task status for {task_id}: {e}")


async def log_manager_plan(task_id: str, plan: dict):
    """Save the manager's breakdown plan."""
    try:
        db = mongodb_connection.db
        await db[COLLECTION].update_one(
            {"task_id": task_id},
            {"$set": {"manager_plan": plan, "status": "in_progress"}}
        )
    except Exception as e:
        logger.error(f"Failed to log manager plan for {task_id}: {e}")


async def log_team_result(task_id: str, team: str, subtask: str, result: str):
    """Append a team agent's result to the task log."""
    now = datetime.now(timezone.utc)
    entry = {
        "team": team,
        "subtask": subtask,
        "result": result,
        "completed_at": now.isoformat(),
    }
    try:
        db = mongodb_connection.db
        await db[COLLECTION].update_one(
            {"task_id": task_id},
            {"$push": {"team_results": entry}}
        )
    except Exception as e:
        logger.error(f"Failed to log team result for {task_id}: {e}")


async def log_final_report(task_id: str, report: str, started_at: datetime):
    """Save the manager's final consolidated report and mark task complete."""
    now = datetime.now(timezone.utc)
    duration = int((now - started_at).total_seconds())
    try:
        db = mongodb_connection.db
        await db[COLLECTION].update_one(
            {"task_id": task_id},
            {"$set": {
                "final_report": report,
                "status": "complete",
                "completed_at": now,
                "total_duration_seconds": duration,
            }}
        )
        logger.info(f"Task {task_id} completed in {duration}s")
    except Exception as e:
        logger.error(f"Failed to log final report for {task_id}: {e}")


async def get_task_log(task_id: str) -> Optional[dict]:
    """Retrieve a task log by task_id."""
    try:
        db = mongodb_connection.db
        doc = await db[COLLECTION].find_one({"task_id": task_id})
        if doc:
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("submitted_at"), datetime):
                doc["submitted_at"] = doc["submitted_at"].isoformat()
            if isinstance(doc.get("completed_at"), datetime):
                doc["completed_at"] = doc["completed_at"].isoformat()
        return doc
    except Exception as e:
        logger.error(f"Failed to get task log {task_id}: {e}")
        return None


async def list_task_logs(limit: int = 20) -> list:
    """Return the most recent task logs."""
    try:
        db = mongodb_connection.db
        cursor = db[COLLECTION].find({}).sort("submitted_at", -1).limit(limit)
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("submitted_at"), datetime):
                doc["submitted_at"] = doc["submitted_at"].isoformat()
            if isinstance(doc.get("completed_at"), datetime):
                doc["completed_at"] = doc["completed_at"].isoformat()
            results.append(doc)
        return results
    except Exception as e:
        logger.error(f"Failed to list task logs: {e}")
        return []
