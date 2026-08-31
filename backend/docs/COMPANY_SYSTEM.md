# Company + Team System

This document describes the organizational foundation built in Phase 2 for Mycel.

## Core Hierarchy

The organizational structure defines where future AI employees will be positioned.

1. **Company**: The top-level tenant. 
2. **Department**: A functional group within a company.
3. **Team**: A specific division within a department, holding a distinct mission.
4. **Position**: A required role within a team describing responsibilities and capability requirements.

> **Crucial Concept**: A *Position* is NOT an *Employee*. A Position is an open slot with requirements (e.g., "Senior Backend Engineer" requiring Python 80%). The Employee is the AI identity (e.g., "Kabir Singh") that will eventually occupy that slot in Phase 3.

## Business Rules

1. **Uniqueness**: `slug` fields are unique within a company scope (i.e. two companies can have an "engineering" department, but one company cannot have two).
2. **Consistency**: When creating a Team, the specified Department must belong to the same Company. When creating a Position, the Team must belong to the same Company.
3. **Archival constraints**: If a Company is archived, you cannot create new Departments, Teams, or Positions within it. Same logic cascades down.

## API Endpoints

Located under `/api/v1/companies`:
- `POST /` - Create Company
- `GET /{id}` - Get Company
- `PATCH /{id}` - Update Company
- `GET /{id}/organization` - Fetch full nested tree of Dept -> Team -> Position
- `POST /{id}/departments` - Create Department
- `POST /{id}/departments/{dept_id}/teams` - Create Team
- `POST /{id}/teams/{team_id}/positions` - Create Position
- (Plus corresponding GET/PATCH listing endpoints)

## Multi-Tenancy

Every entity (`Department`, `Team`, `Position`) contains a `company_id`. All repository lookups and service verifications enforce that cross-company data access is blocked. A user modifying a Team must provide the `company_id` to route correctly.

## Event System

All organizational changes emit standard events to RabbitMQ:
- `company.created`, `company.updated`, `company.archived`
- `department.created`, `department.updated`, `department.archived`
- `team.created`, `team.updated`, `team.archived`
- `position.created`, `position.updated`, `position.opened`, `position.closed`

## Seed Data

For development, `backend/scripts/seed_company.py` generates the `Mycel` company with an 8-department structure and placeholder positions. Run this script to populate your local MongoDB.
