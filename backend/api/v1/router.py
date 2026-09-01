"""
Main V1 Router.
Consolidates all v1 specific endpoints.
"""

from fastapi import APIRouter
from .routes import health, employees
from .routes import companies, departments, teams, positions, skills, tools, knowledge, reasoning, pipelines, stage_definitions, quality, outputs, intelligence

router = APIRouter()

# Register v1 routes
router.include_router(health.router, tags=["System"])
router.include_router(companies.router, tags=["Organization (Companies)"])
router.include_router(departments.router, tags=["Organization (Departments)"])
router.include_router(teams.router, tags=["Organization (Teams)"])
router.include_router(positions.router, tags=["Organization (Positions)"])
router.include_router(skills.router, tags=["Workforce (Skills)"])
router.include_router(tools.router, tags=["Tools"])
router.include_router(knowledge.router, tags=["Knowledge"])
router.include_router(reasoning.router, tags=["Reasoning"])
router.include_router(stage_definitions.router, tags=["Pipelines"])
router.include_router(pipelines.router, tags=["Pipelines"])
router.include_router(outputs.router, tags=["Outputs"])
router.include_router(quality.router, tags=["Quality"])
router.include_router(employees.router, tags=["Employees"])

router.include_router(intelligence.router, tags=["Intelligence Team"])

# Real-time WebSocket and broadcast
from .routes.realtime import router as realtime_router
router.include_router(realtime_router, tags=["Realtime"])
