"""
Per-operator onboarding setup.

The frontend calls GET /api/setup/me straight after login: if the operator
already has a completed setup we send them to mission control (their
blueprint already exists), otherwise they run the nine-step wizard.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from core.logger import logger
from core.mongodb import mongodb_connection
from core.auth import CurrentOperatorDep
from .schemas import SetupPayload, SetupStatus

router = APIRouter()

COLLECTION = "operator_setups"


def _db():
    return mongodb_connection.db if mongodb_connection.client is not None else None


@router.get("/me", response_model=SetupStatus)
async def get_my_setup(operator: CurrentOperatorDep) -> SetupStatus:
    """Has this operator already built their network?"""
    db = _db()
    if db is None:
        logger.error("Setup lookup with no MongoDB connection")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable. MongoDB connection is down."
        )

    record = await db[COLLECTION].find_one({"user_id": operator.user_id}, {"_id": 0})
    if not record:
        return SetupStatus(has_setup=False, setup=None)

    return SetupStatus(
        has_setup=bool(record.get("completed")),
        setup=record.get("setup"),
        completed_at=record.get("completed_at"),
    )


@router.post("/me", response_model=SetupStatus)
async def save_my_setup(payload: SetupPayload, operator: CurrentOperatorDep) -> SetupStatus:
    """Upsert the operator's wizard answers and mark onboarding complete."""
    db = _db()
    now = datetime.now(timezone.utc)
    setup = payload.model_dump()

    if db is None:
        logger.error("Setup save with no MongoDB connection")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable. MongoDB connection is down."
        )

    try:
        await db[COLLECTION].update_one(
            {"user_id": operator.user_id},
            {
                "$set": {
                    "user_id": operator.user_id,
                    "email": operator.email,
                    "setup": setup,
                    "completed": not payload.is_draft,
                    "completed_at": now if not payload.is_draft else None,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
    except Exception as error:
        logger.error("Failed to persist operator setup", extra={"error": str(error)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save your setup — try again",
        )

    return SetupStatus(has_setup=True, setup=setup, completed_at=now)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def reset_my_setup(operator: CurrentOperatorDep) -> None:
    """Clear the operator's setup so they can rebuild from scratch."""
    db = _db()
    if db is not None:
        await db[COLLECTION].delete_one({"user_id": operator.user_id})
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable. MongoDB connection is down."
        )
