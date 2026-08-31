"""
Seed script for development data in Phase 2.
Idempotently creates the Mycel organization hierarchy.
"""

import asyncio
import os
import sys

# Ensure backend directory is in PYTHONPATH for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mongodb import mongodb_connection
from organization.models import (
    Company, Department, Team, Position, CompanyStatus, Level
)
from infrastructure.database.repositories.base import BaseRepository

async def create_indexes():
    """Create appropriate MongoDB indexes for the organization domain."""
    print("Creating database indexes...")
    db = mongodb_connection.db

    # Company indexes
    await db.companies.create_index("slug", unique=True)
    
    # Department indexes
    await db.departments.create_index([("company_id", 1), ("slug", 1)], unique=True)
    
    # Team indexes
    await db.teams.create_index([("company_id", 1), ("slug", 1)], unique=True)
    await db.teams.create_index([("department_id", 1)])
    
    # Position indexes
    await db.positions.create_index([("company_id", 1), ("slug", 1)], unique=True)
    await db.positions.create_index([("team_id", 1)])
    print("Indexes created.")

async def seed_data():
    print("Connecting to MongoDB...")
    await mongodb_connection.connect()
    
    try:
        await create_indexes()

        db = mongodb_connection.db
        company_repo = BaseRepository[Company](db, "companies", Company)
        dept_repo = BaseRepository[Department](db, "departments", Department)
        team_repo = BaseRepository[Team](db, "teams", Team)
        pos_repo = BaseRepository[Position](db, "positions", Position)

        print("Seeding Mycel Company...")
        # 1. Company
        existing_company = await db.companies.find_one({"slug": "mycel"})
        if not existing_company:
            company = Company(
                name="Mycel",
                slug="mycel",
                description="AI Company Operating System",
                status=CompanyStatus.ACTIVE
            )
            company = await company_repo.create(company)
            print(f"Created company: {company.name} ({company.id})")
        else:
            company = Company(**existing_company, id=str(existing_company["_id"]))
            print(f"Found company: {company.name} ({company.id})")

        # 2. Departments
        departments = [
            ("Engineering", "engineering", "Software and infrastructure engineering"),
            ("Product", "product", "Product Management and Research"),
            ("Design", "design", "UI/UX and Creative Design"),
            ("Research", "research", "Market and Technical Research"),
            ("Marketing", "marketing", "Content, Growth, and Social Media"),
            ("Finance", "finance", "Finance and Accounting"),
            ("HR", "hr", "Human Resources"),
            ("Operations", "operations", "Business Operations")
        ]

        created_depts = {}
        for name, slug, desc in departments:
            existing = await db.departments.find_one({"company_id": company.id, "slug": slug})
            if not existing:
                dept = Department(
                    company_id=company.id,
                    name=name,
                    slug=slug,
                    description=desc,
                    status=CompanyStatus.ACTIVE
                )
                dept = await dept_repo.create(dept)
                created_depts[slug] = dept
                print(f"  Created department: {dept.name}")
            else:
                created_depts[slug] = Department(**existing, id=str(existing["_id"]))

        # 3. Teams
        teams = [
            ("engineering", "Backend", "backend", "Build reliable backend systems"),
            ("engineering", "Frontend", "frontend", "Build pixel-perfect UI"),
            ("engineering", "QA", "qa", "Ensure quality"),
            ("engineering", "DevOps", "devops", "Infrastructure and pipelines"),
            ("research", "Market Research", "market-research", "Understand the market"),
            ("research", "Technical Research", "technical-research", "Advanced AI research"),
            ("marketing", "Content", "content", "Create engaging content"),
            ("marketing", "Growth", "growth", "Drive user acquisition"),
            ("design", "UI/UX", "ui-ux", "Design user experiences"),
            ("design", "Creative", "creative", "Brand and visuals"),
        ]

        created_teams = {}
        for dept_slug, name, slug, mission in teams:
            dept = created_depts.get(dept_slug)
            if not dept:
                continue

            existing = await db.teams.find_one({"company_id": company.id, "slug": slug})
            if not existing:
                team = Team(
                    company_id=company.id,
                    department_id=dept.id,
                    name=name,
                    slug=slug,
                    mission=mission,
                    status=CompanyStatus.ACTIVE
                )
                team = await team_repo.create(team)
                created_teams[slug] = team
                print(f"    Created team: {team.name}")
            else:
                created_teams[slug] = Team(**existing, id=str(existing["_id"]))

        # 4. Positions
        positions = [
            ("backend", "Backend Engineer", "backend-engineer", Level.MID),
            ("frontend", "Frontend Engineer", "frontend-engineer", Level.MID),
            ("qa", "QA Engineer", "qa-engineer", Level.JUNIOR),
            ("technical-research", "Research Specialist", "research-specialist", Level.SENIOR),
            ("market-research", "Market Researcher", "market-researcher", Level.MID),
            ("ui-ux", "UI/UX Designer", "ui-ux-designer", Level.MID),
            ("creative", "Video Editor", "video-editor", Level.MID),
            ("growth", "Marketing Strategist", "marketing-strategist", Level.SENIOR)
        ]

        for team_slug, title, slug, level in positions:
            team = created_teams.get(team_slug)
            if not team:
                continue

            existing = await db.positions.find_one({"company_id": company.id, "slug": slug})
            if not existing:
                pos = Position(
                    company_id=company.id,
                    department_id=team.department_id,
                    team_id=team.id,
                    title=title,
                    slug=slug,
                    level=level
                )
                pos = await pos_repo.create(pos)
                print(f"      Created position: {pos.title}")

        print("Seeding complete.")

    finally:
        await mongodb_connection.close()

if __name__ == "__main__":
    asyncio.run(seed_data())
