from workforce.employees.models import SkillProficiency

skills = {
    "testing": SkillProficiency(level=90, experience="Expert"),
    "unit_testing": SkillProficiency(level=80, experience="Advanced"),
    "integration_testing": SkillProficiency(level=80, experience="Advanced"),
    "e2e_testing": SkillProficiency(level=75, experience="Advanced"),
    "test_automation": SkillProficiency(level=85, experience="Advanced"),
    "code_review": SkillProficiency(level=70, experience="Intermediate"),
    "quality_assurance": SkillProficiency(level=80, experience="Advanced"),
    "debugging": SkillProficiency(level=70, experience="Intermediate"),
    "technical_documentation": SkillProficiency(level=65, experience="Intermediate"),
    "troubleshooting": SkillProficiency(level=75, experience="Advanced"),
    "python": SkillProficiency(level=70, experience="Intermediate"),
    "javascript": SkillProficiency(level=65, experience="Intermediate"),
    "selenium": SkillProficiency(level=75, experience="Advanced"),
    "cypress": SkillProficiency(level=70, experience="Intermediate"),
}
