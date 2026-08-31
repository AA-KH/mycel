from workforce.employees.models import SkillProficiency

skills = {
    "software_development": SkillProficiency(level=65, experience="Intermediate"),
    "devops": SkillProficiency(level=85, experience="Advanced"),
    "version_control": SkillProficiency(level=85, experience="Expert"),
    "ci_cd": SkillProficiency(level=80, experience="Advanced"),
    "containerization": SkillProficiency(level=80, experience="Advanced"),
    "cloud_services": SkillProficiency(level=75, experience="Advanced"),
    "infrastructure_as_code": SkillProficiency(level=70, experience="Intermediate"),
    "monitoring": SkillProficiency(level=70, experience="Intermediate"),
    "security_awareness": SkillProficiency(level=60, experience="Intermediate"),
    "troubleshooting": SkillProficiency(level=75, experience="Advanced"),
    "docker": SkillProficiency(level=85, experience="Expert"),
    "kubernetes": SkillProficiency(level=75, experience="Advanced"),
    "git": SkillProficiency(level=85, experience="Expert"),
}
