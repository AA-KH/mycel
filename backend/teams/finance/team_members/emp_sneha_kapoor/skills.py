from workforce.employees.models import SkillProficiency

skills = {
    "accounting":            SkillProficiency(level=92, experience="Extensive"),
    "reconciliation":        SkillProficiency(level=90, experience="Extensive"),
    "compliance":            SkillProficiency(level=85, experience="Advanced"),
    "financial_reporting":   SkillProficiency(level=80, experience="Advanced"),
    "budgeting":             SkillProficiency(level=70, experience="Intermediate"),
    "cost_analysis":         SkillProficiency(level=68, experience="Intermediate"),
    "data_analysis":         SkillProficiency(level=65, experience="Intermediate"),
    "risk_assessment":       SkillProficiency(level=62, experience="Intermediate"),
}
