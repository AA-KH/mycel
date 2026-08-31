from typing import List, Optional
import logging

from tasks.models import OutputSpec
from tools.models import ToolDefinition
from tools.registry.core import ToolRegistry

logger = logging.getLogger(__name__)

class ToolResolver:
    """
    Resolves the required tool based on the OutputSpec.
    """
    def __init__(self, tool_registry: ToolRegistry):
        self._registry = tool_registry

    def resolve_tool_for_output(self, output_spec: OutputSpec) -> Optional[ToolDefinition]:
        """
        Finds a tool that supports the requested capability, output modality, and artifact type.
        """
        all_tools = self._registry.list_all_definitions()
        
        for tool in all_tools:
            # Check Capabilities
            if output_spec.required_capabilities:
                has_cap = any(cap in tool.capabilities for cap in output_spec.required_capabilities)
                if not has_cap:
                    continue
            
            # Check Modality
            if output_spec.modality.value not in tool.output_modalities:
                continue
                
            # Check Artifact Type
            if output_spec.artifact_type.value not in tool.artifact_types:
                continue
                
            # If all checks pass, we found our tool
            logger.info(f"ToolResolver selected '{tool.id}' for OutputSpec {output_spec.artifact_type.value}")
            return tool
            
        logger.warning(f"ToolResolver found NO matching tool for OutputSpec {output_spec.artifact_type.value}")
        return None
