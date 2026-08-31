# Individual skill definitions
from .individual.software_development import software_development
from .individual.programming import programming
from .individual.debugging import debugging
from .individual.software_architecture import software_architecture
from .individual.system_design import system_design
from .individual.api_development import api_development
from .individual.database_management import database_management
from .individual.frontend_development import frontend_development
from .individual.backend_development import backend_development
from .individual.testing import testing
from .individual.code_review import code_review
from .individual.version_control import version_control
from .individual.technical_documentation import technical_documentation

# Core skills (most important for developer team)
CORE_SKILLS = [
    software_development,
    programming,
    debugging,
    software_architecture,
    system_design,
    api_development,
    database_management,
    testing,
    code_review,
    version_control,
    technical_documentation
]

# All engineering skills including specialized ones
ENGINEERING_SKILLS = CORE_SKILLS
