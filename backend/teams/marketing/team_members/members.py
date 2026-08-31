"""
Marketing Team — Member Registry

Collects all marketing team employee profiles into a single registry.
"""

from teams.marketing.team_members.emp_neha_strategy.profile import neha
from teams.marketing.team_members.emp_dev_marketing.profile import dev
from teams.marketing.team_members.emp_karan_content.profile import karan
from teams.marketing.team_members.emp_simran_growth.profile import simran

MARKETING_TEAM_MEMBERS = {
    "emp_neha_strategy": neha,
    "emp_dev_marketing": dev,
    "emp_karan_content": karan,
    "emp_simran_growth": simran,
}

# Quick lookup by role
MEMBER_BY_ROLE = {
    "marketing_strategist": neha,
    "marketing_analyst": dev,
    "content_creator": karan,
    "growth_specialist": simran,
}
