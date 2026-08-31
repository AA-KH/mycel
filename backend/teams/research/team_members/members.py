"""
Research Team — Member Registry

Collects all research team employee profiles into a single registry.
"""

from teams.research.team_members.emp_meera_kapoor.profile import meera
from teams.research.team_members.emp_aarav_mehta.profile import aarav
from teams.research.team_members.emp_aditya_singh.profile import aditya
from teams.research.team_members.emp_nisha_rao.profile import nisha

RESEARCH_TEAM_MEMBERS = {
    "emp_meera_kapoor": meera,
    "emp_aarav_mehta": aarav,
    "emp_aditya_singh": aditya,
    "emp_nisha_rao": nisha,
}

# Quick lookup by role
MEMBER_BY_ROLE = {
    "research_analyst": meera,
    "researcher": aarav,
    "fact_checker": aditya,
    "research_writer": nisha,
}
