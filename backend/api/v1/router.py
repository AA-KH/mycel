"""
Main V1 Router.
Consolidates all v1 specific endpoints.
"""

from fastapi import APIRouter, Depends
from core.auth import get_current_user
from .routes import health, employees, chat
from .routes import companies, departments, teams, positions, skills, tools, knowledge, reasoning, pipelines, stage_definitions, quality, outputs, intelligence, network, resilience, council, project, agents, documents, monitor

router = APIRouter()

# Register v1 routes
router.include_router(health.router, tags=["System"])

protected_deps = [Depends(get_current_user)]

router.include_router(agents.router, prefix="/agents", tags=["Agents"], dependencies=protected_deps)
router.include_router(documents.router, tags=["Documents"], dependencies=protected_deps)
router.include_router(companies.router, tags=["Organization (Companies)"], dependencies=protected_deps)
router.include_router(departments.router, tags=["Organization (Departments)"], dependencies=protected_deps)
router.include_router(teams.router, tags=["Organization (Teams)"], dependencies=protected_deps)
router.include_router(positions.router, tags=["Organization (Positions)"], dependencies=protected_deps)
router.include_router(skills.router, tags=["Workforce (Skills)"], dependencies=protected_deps)
router.include_router(tools.router, tags=["Tools"], dependencies=protected_deps)
router.include_router(knowledge.router, tags=["Knowledge"], dependencies=protected_deps)
router.include_router(reasoning.router, tags=["Reasoning"], dependencies=protected_deps)
router.include_router(stage_definitions.router, tags=["Pipelines"], dependencies=protected_deps)
router.include_router(pipelines.router, tags=["Pipelines"], dependencies=protected_deps)
router.include_router(outputs.router, tags=["Outputs"], dependencies=protected_deps)
router.include_router(quality.router, tags=["Quality"], dependencies=protected_deps)
router.include_router(employees.router, tags=["Employees"], dependencies=protected_deps)
router.include_router(project.router, prefix="/projects", tags=["Projects"]) # Dependency applied inside create_project

router.include_router(intelligence.router, tags=["Intelligence Team"], dependencies=protected_deps)
router.include_router(network.router, tags=["Network Team"], dependencies=protected_deps)
router.include_router(resilience.router, tags=["Resilience Team"], dependencies=protected_deps)
router.include_router(council.router, tags=["Council Team"], dependencies=protected_deps)

# Webhook for monitoring subsystem
router.include_router(monitor.router, prefix="/monitor", tags=["Monitor Integration"])

# Real-time WebSocket and broadcast
from .routes.realtime import router as realtime_router
router.include_router(realtime_router, prefix="/realtime", tags=["Realtime"])

# ArmorIQ Human-in-the-Loop approval endpoint
from .routes.realtime.approvals import router as approvals_router
router.include_router(approvals_router, prefix="/realtime", tags=["ArmorIQ"])

# Chat / RAG
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
