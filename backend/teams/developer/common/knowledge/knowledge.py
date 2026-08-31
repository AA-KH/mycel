# Individual knowledge space definitions
from .individual.software_patterns import software_patterns
from .individual.api_standards import api_standards
from .individual.database_design import database_design
from .individual.security_fundamentals import security_fundamentals
from .individual.system_design_principles import system_design_principles
from .individual.ui_ux_principles import ui_ux_principles
from .individual.accessibility_standards import accessibility_standards
from .individual.web_standards import web_standards
from .individual.cloud_architecture import cloud_architecture
from .individual.networking_fundamentals import networking_fundamentals
from .individual.deployment_strategies import deployment_strategies

# Core knowledge spaces (essential for developer team)
CORE_KNOWLEDGE = [
    software_patterns,
    api_standards,
    database_design,
    security_fundamentals,
    system_design_principles
]

# All engineering knowledge including specialized areas
ENGINEERING_KNOWLEDGE = CORE_KNOWLEDGE + [
    ui_ux_principles,
    accessibility_standards,
    web_standards,
    cloud_architecture,
    networking_fundamentals,
    deployment_strategies
]
