# Individual tool definitions
from .individual.filesystem_read import filesystem_read
from .individual.filesystem_write import filesystem_write
from .individual.terminal_execute import terminal_execute
from .individual.git_operations import git_operations
from .individual.database_query import database_query
from .individual.browser_devtools import browser_devtools
from .individual.docker_operations import docker_operations
from .individual.kubernetes_operations import kubernetes_operations
from .individual.code_generator import CodeGenerator, CodeExecutor, CodeTester

# Core tools (essential for developer team)
CORE_TOOLS = [
    filesystem_read,
    filesystem_write,
    terminal_execute,
    git_operations
]

# All engineering tools including specialized ones
ENGINEERING_TOOLS = CORE_TOOLS + [
    database_query,
    browser_devtools,
    docker_operations,
    kubernetes_operations
]
