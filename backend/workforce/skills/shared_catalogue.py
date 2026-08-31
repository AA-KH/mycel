from workforce.skills.models import SkillCategory

SHARED_SKILLS = [
    {
        "skill_id": "communication",
        "name": "communication",
        "display_name": "Communication",
        "description": "Clear and effective exchange of information.",
        "domain": "shared",
        "category": SkillCategory.COMMUNICATION
    },
    {
        "skill_id": "documentation",
        "name": "documentation",
        "display_name": "Documentation",
        "description": "Creating accessible and accurate records.",
        "domain": "shared",
        "category": SkillCategory.COMMUNICATION
    },
    {
        "skill_id": "analysis",
        "name": "analysis",
        "display_name": "Analysis",
        "description": "Breaking down complex topics.",
        "domain": "shared",
        "category": SkillCategory.ANALYTICAL
    },
    {
        "skill_id": "problem_solving",
        "name": "problem_solving",
        "display_name": "Problem Solving",
        "description": "Identifying solutions to complex issues.",
        "domain": "shared",
        "category": SkillCategory.ANALYTICAL
    },
    {
        "skill_id": "quality_assurance",
        "name": "quality_assurance",
        "display_name": "Quality Assurance",
        "description": "Ensuring outputs meet defined standards.",
        "domain": "shared",
        "category": SkillCategory.QUALITY
    }
]
