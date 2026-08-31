from workforce.employees.models import SkillProficiency

skills = {
    "financial_modeling":    SkillProficiency(level=90, experience="Extensive"),
    "data_analysis":         SkillProficiency(level=88, experience="Extensive"),
    "forecasting":           SkillProficiency(level=85, experience="Advanced"),
    "financial_reporting":   SkillProficiency(level=82, experience="Advanced"),
    "risk_assessment":       SkillProficiency(level=75, experience="Advanced"),
    "accounting":            SkillProficiency(level=70, experience="Intermediate"),
    "cost_analysis":         SkillProficiency(level=72, experience="Intermediate"),
    "budgeting":             SkillProficiency(level=68, experience="Intermediate"),
}
