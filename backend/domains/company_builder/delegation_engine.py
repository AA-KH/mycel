"""
Delegation Engine

Builds a structured DelegationGraph from orchestration results.
This gives full transparency on which manager delegated what to which member,
so the frontend can render a visual node tree.
"""

import logging
from typing import Dict, Any, List

from domains.company_builder.delegation_models import (
    DelegationGraph, TeamDelegation, MemberAssignment
)

logger = logging.getLogger(__name__)

# Static team metadata used to enrich the delegation graph
TEAM_METADATA = {
    "research": {
        "color": "#5e81f4",
        "manager_name": "Research Director",
        "manager_role": "Head of Market Research",
        "manager_avatar": "/avatars/research_manager.png",
        "members": [
            {
                "member_id": "emp_arjun_research",
                "member_name": "Arjun Mehta",
                "member_role": "Market Research Analyst",
                "member_avatar": "/avatars/arjun.png",
            },
            {
                "member_id": "emp_priya_data",
                "member_name": "Priya Sharma",
                "member_role": "Data Scientist",
                "member_avatar": "/avatars/priya.png",
            }
        ]
    },
    "legal": {
        "color": "#f4a261",
        "manager_name": "Legal Director",
        "manager_role": "Head of Legal & Compliance",
        "manager_avatar": "/avatars/legal_manager.png",
        "members": [
            {
                "member_id": "emp_raj_legal",
                "member_name": "Raj Kapoor",
                "member_role": "Corporate Lawyer",
                "member_avatar": "/avatars/raj.png",
            },
            {
                "member_id": "emp_ananya_compliance",
                "member_name": "Ananya Singh",
                "member_role": "Compliance Officer",
                "member_avatar": "/avatars/ananya.png",
            }
        ]
    },
    "finance": {
        "color": "#2ec4b6",
        "manager_name": "Finance Director",
        "manager_role": "Chief Financial Analyst",
        "manager_avatar": "/avatars/finance_manager.png",
        "members": [
            {
                "member_id": "emp_vikram_finance",
                "member_name": "Vikram Nair",
                "member_role": "Financial Analyst",
                "member_avatar": "/avatars/vikram.png",
            },
            {
                "member_id": "emp_neha_budget",
                "member_name": "Neha Joshi",
                "member_role": "Budget Strategist",
                "member_avatar": "/avatars/neha.png",
            }
        ]
    },
    "creative": {
        "color": "#e040fb",
        "manager_name": "Creative Director",
        "manager_role": "Head of Brand & Design",
        "manager_avatar": "/avatars/creative_manager.png",
        "members": [
            {
                "member_id": "emp_riya_designer",
                "member_name": "Riya Sharma",
                "member_role": "Senior Graphic Designer",
                "member_avatar": "/avatars/riya.png",
            },
            {
                "member_id": "emp_kabir_brand",
                "member_name": "Kabir Ahmed",
                "member_role": "Brand Strategist",
                "member_avatar": "/avatars/kabir.png",
            }
        ]
    },
    "marketing": {
        "color": "#ff6b6b",
        "manager_name": "Marketing Director",
        "manager_role": "Head of Growth & Marketing",
        "manager_avatar": "/avatars/marketing_manager.png",
        "members": [
            {
                "member_id": "emp_divya_growth",
                "member_name": "Divya Patel",
                "member_role": "Growth Hacker",
                "member_avatar": "/avatars/divya.png",
            }
        ]
    },
    "developer": {
        "color": "#69db7c",
        "manager_name": "Tech Director",
        "manager_role": "Head of Engineering",
        "manager_avatar": "/avatars/dev_manager.png",
        "members": [
            {
                "member_id": "emp_kabir_dev",
                "member_name": "Kabir Sharma",
                "member_role": "Full Stack Developer",
                "member_avatar": "/avatars/kabir_dev.png",
            }
        ]
    },
}


# Stage → which teams get involved, and what tasks each member does
STAGE_DELEGATION_MAP: Dict[str, List[Dict]] = {
    "FEASIBILITY_ANALYSIS": [
        {
            "team_id": "research",
            "objective": "Conduct market size, demographic, and competitive landscape research",
            "tasks": [
                {"member_idx": 0, "title": "Market Sizing & TAM Analysis", "description": "Analyze total addressable market, segments, and growth projections", "output": "Market Research Report"},
                {"member_idx": 1, "title": "Competitive Landscape Data", "description": "Map competitors, their positioning, and market gaps", "output": "Competitor Analysis Dataset"},
            ]
        },
        {
            "team_id": "legal",
            "objective": "Analyze regulatory environment, required licenses, and compliance risks",
            "tasks": [
                {"member_idx": 0, "title": "Regulatory & Licensing Review", "description": "Identify all required licenses, permits, and regulatory filings", "output": "Legal Requirements Checklist"},
                {"member_idx": 1, "title": "Compliance Risk Assessment", "description": "Evaluate data privacy, IP, and industry-specific compliance risks", "output": "Risk Assessment Report"},
            ]
        },
        {
            "team_id": "finance",
            "objective": "Project financial feasibility including costs, revenue, and funding needs",
            "tasks": [
                {"member_idx": 0, "title": "P&L Projection (3-Year)", "description": "Build income statement projections for first 3 years of operation", "output": "Financial Model (XLSX)"},
                {"member_idx": 1, "title": "Funding Requirements & ROI", "description": "Calculate seed capital requirements and break-even analysis", "output": "Investor Funding Brief"},
            ]
        },
    ],
    "GROWTH_STRATEGY": [
        {
            "team_id": "marketing",
            "objective": "Define go-to-market and customer acquisition strategy",
            "tasks": [
                {"member_idx": 0, "title": "GTM Strategy & Channel Mix", "description": "Define acquisition channels, CAC targets, and growth loops", "output": "Growth Strategy Document"},
            ]
        },
        {
            "team_id": "research",
            "objective": "Identify ICP (Ideal Customer Profile) and segment audiences",
            "tasks": [
                {"member_idx": 0, "title": "ICP & Persona Definition", "description": "Research and define top 3 customer personas with pain points", "output": "Customer Persona Profiles"},
            ]
        },
    ],
    "BRAND_IDENTITY": [
        {
            "team_id": "creative",
            "objective": "Define brand visual language, colors, and tone of voice",
            "tasks": [
                {"member_idx": 0, "title": "Visual Identity System", "description": "Select color palette, typography, and iconographic style", "output": "Brand Style Guide"},
                {"member_idx": 1, "title": "Brand Voice & Messaging", "description": "Define tone of voice, tagline, and key brand messages", "output": "Brand Messaging Framework"},
            ]
        }
    ],
    "LOGO_CREATION": [
        {
            "team_id": "creative",
            "objective": "Design the company logo aligned to brand identity",
            "tasks": [
                {"member_idx": 0, "title": "Logo Design (3 Concepts)", "description": "Create 3 logo concepts based on the brand style guide", "output": "Logo Files (SVG, PNG)"},
            ]
        }
    ],
    "POSTER_CREATION": [
        {
            "team_id": "creative",
            "objective": "Design a high-impact promotional poster",
            "tasks": [
                {"member_idx": 0, "title": "Promotional Poster Design", "description": "Design a brand-consistent marketing poster for social and print", "output": "Poster (A3, 300DPI)"},
            ]
        }
    ],
    "WEBSITE_CREATION": [
        {
            "team_id": "developer",
            "objective": "Build a responsive promotional landing page",
            "tasks": [
                {"member_idx": 0, "title": "Landing Page Development", "description": "Build a modern, responsive HTML/CSS/JS landing page with the brand assets", "output": "Website (HTML Bundle)"},
            ]
        },
        {
            "team_id": "creative",
            "objective": "Design website wireframes and visual assets",
            "tasks": [
                {"member_idx": 0, "title": "Website UI Design", "description": "Create wireframes and high-fidelity UI components for the landing page", "output": "Figma Design File"},
            ]
        }
    ],
    "PITCH_DECK_CREATION": [
        {
            "team_id": "marketing",
            "objective": "Assemble a compelling investor pitch deck",
            "tasks": [
                {"member_idx": 0, "title": "Pitch Deck Narrative", "description": "Write the story arc — problem, solution, market, traction, ask", "output": "Pitch Deck Script"},
            ]
        },
        {
            "team_id": "creative",
            "objective": "Design all slides with brand visuals",
            "tasks": [
                {"member_idx": 0, "title": "Slide Design (15 Slides)", "description": "Design all 15 slides with charts, icons, and brand visuals", "output": "Pitch Deck (PPTX + PDF)"},
            ]
        }
    ],
    "REQUIREMENTS_DISCOVERY": [
        {
            "team_id": "research",
            "objective": "Understand company vision, goals, and target market",
            "tasks": [
                {"member_idx": 0, "title": "Requirements Gathering", "description": "Document business goals, constraints, and success criteria", "output": "Requirements Document"},
            ]
        }
    ],
}


def build_delegation_graph(workflow_id: str, stage: str, prompt: str) -> DelegationGraph:
    """
    Constructs a full DelegationGraph for a given stage.
    """
    stage_config = STAGE_DELEGATION_MAP.get(stage, [])
    graph = DelegationGraph(
        workflow_id=workflow_id,
        stage=stage,
        prompt_summary=prompt[:200] + ("..." if len(prompt) > 200 else ""),
    )

    for team_config in stage_config:
        team_id = team_config["team_id"]
        meta = TEAM_METADATA.get(team_id, {})
        members_meta = meta.get("members", [])

        delegation = TeamDelegation(
            team_id=team_id,
            team_name=team_id.upper(),
            team_color=meta.get("color", "#888888"),
            manager_name=meta.get("manager_name", "Team Manager"),
            manager_role=meta.get("manager_role", "Manager"),
            manager_avatar=meta.get("manager_avatar"),
            objective=team_config["objective"],
        )

        for task_def in team_config["tasks"]:
            member_idx = task_def["member_idx"]
            member = members_meta[member_idx] if member_idx < len(members_meta) else {}

            assignment = MemberAssignment(
                member_id=member.get("member_id", f"{team_id}_member_{member_idx}"),
                member_name=member.get("member_name", f"Team Member {member_idx + 1}"),
                member_role=member.get("member_role", "Specialist"),
                member_avatar=member.get("member_avatar"),
                task_title=task_def["title"],
                task_description=task_def["description"],
                expected_output=task_def["output"],
                status="ASSIGNED",
                team_color=meta.get("color", "#888888"),
            )
            delegation.members.append(assignment)

        graph.teams.append(delegation)

    graph.compute_totals()
    logger.info(f"Built DelegationGraph for stage={stage}, teams={len(graph.teams)}, tasks={graph.total_tasks}")
    return graph
