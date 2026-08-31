"""
Delivery API Router (Phase 14)

Exposes the Output Delivery System via REST endpoints.

Endpoints:
  POST /api/delivery/tasks/{task_id}/deliver
      Trigger delivery packaging for a task.

  GET  /api/delivery/tasks/{task_id}
      Return all delivery packages for a task.

  GET  /api/delivery/{package_id}
      Return a specific delivery package (marks as delivered).
"""

import logging
from fastapi import APIRouter, HTTPException

from delivery.models import DeliveryRequest, DeliveryFormat, DeliveryResult
from delivery.resolver import DeliveryResolver
from delivery.packager import DeliveryPackager
from delivery.signer import DeliveryURLSigner
from delivery.repository import DeliveryRepository
from delivery.service import DeliveryService

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Dependency factories (simple singletons for Phase 14)
# ─────────────────────────────────────────────────────────────────────────────

_resolver = DeliveryResolver()
_packager = DeliveryPackager()
_signer = DeliveryURLSigner()
_repository = DeliveryRepository()
_service = DeliveryService(_resolver, _packager, _signer, _repository)


def get_service() -> DeliveryService:
    return _service


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/tasks/{task_id}/deliver",
    response_model=DeliveryResult,
    summary="Trigger output delivery for a task",
)
async def trigger_delivery(task_id: str, body: DeliveryRequest):
    """
    Packages, signs, and persists the delivery for all READY artifacts
    associated with the given task.
    """
    body.task_id = task_id   # Ensure path param takes precedence
    service = get_service()
    result = await service.deliver(body)
    return result


@router.get(
    "/tasks/{task_id}",
    response_model=list[DeliveryResult],
    summary="Get all deliveries for a task",
)
async def get_task_deliveries(task_id: str):
    """Return all delivery packages for the given task."""
    service = get_service()
    results = await service.get_task_deliveries(task_id)
    return results


@router.get(
    "/{package_id}",
    response_model=DeliveryResult,
    summary="Retrieve a specific delivery package",
)
async def get_delivery(package_id: str):
    """
    Retrieves a delivery package by ID.
    Increments delivery_count and marks the package as DELIVERED.
    Returns 404 if the package does not exist.
    """
    service = get_service()
    result = await service.get_delivery(package_id)
    if not result:
        raise HTTPException(status_code=404, detail="Delivery package not found.")
    return result
