import logging
from typing import Dict, Any

from tools.base import BaseTool
from tools.context import ToolExecutionContext
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from tools.providers.builder_io import BuilderWebsiteProvider, WebsiteGenerationRequest

logger = logging.getLogger(__name__)

class WebsiteGeneratorTool(BaseTool):
    """
    Tool that implements WEBSITE_GENERATION capability using BuilderWebsiteProvider.
    It constructs the generation request from company context and returns the actual artifact.
    """
    
    def __init__(self):
        super().__init__()
        self._provider = BuilderWebsiteProvider()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="website.generate",
            name="Website Generator",
            category="web_development",
            description="Generates a complete, functional React/Tailwind website (Landing Page, Promotional Site) based on company context.",
            input_schema={
                "type": "object",
                "required": ["company_name", "task_description"],
                "properties": {
                    "company_name": {"type": "string", "description": "Name of the company"},
                    "task_description": {"type": "string", "description": "Description of the website to build"},
                    "context": {"type": "string", "description": "Synthesized memory context (brand, audience, growth strategy)"}
                }
            },
            capabilities=["WEB_DEVELOPMENT", "WEBSITE_GENERATION", "UI_IMPLEMENTATION", "FRONTEND_DEVELOPMENT"],
            output_modalities=["WEBSITE", "CODE"],
            artifact_types=["WEBSITE", "LANDING_PAGE", "MARKETING_WEBSITE", "PROMOTIONAL_WEBSITE"],
            preview_types=["LIVE_WEBSITE", "SOURCE_CODE"],
            risk_level="low",
            idempotent=True,
            timeout_seconds=60
        )

    async def execute(self, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            task_description = arguments["task_description"]
            company_name = arguments["company_name"]
            memory_context = arguments.get("context", "")
            
            # Simple context parsing (in production, use structured memory)
            industry = "Technology"
            target_audience = "General Audience"
            brand_identity = "Modern, Professional"
            growth_strategy = "Organic Growth"
            
            # Attempt to extract context from the memory string
            # This is a naive extraction since the orchestrator dumps memory into a text context.
            if "Target Audience:" in memory_context:
                target_audience = memory_context.split("Target Audience:")[1].split("\n")[0].strip()
            if "Brand Identity:" in memory_context:
                brand_identity = memory_context.split("Brand Identity:")[1].split("\n")[0].strip()
            if "Industry:" in memory_context:
                industry = memory_context.split("Industry:")[1].split("\n")[0].strip()
                
            request = WebsiteGenerationRequest(
                company_name=company_name,
                industry=industry,
                target_audience=target_audience,
                business_model="B2B/B2C SaaS",
                value_proposition=task_description,
                brand_identity=brand_identity,
                growth_strategy=growth_strategy,
                website_type="PROMOTIONAL_WEBSITE"
            )
            
            # Invoke provider boundary
            result = await self._provider.generate_website(request)
            
            if result.get("status") != "SUCCESS":
                return ToolResult(
                    tool_name=self.definition.id,
                    status="error",
                    output={},
                    error=result.get("reason", "Unknown provider error")
                )
                
            return ToolResult(
                tool_name=self.definition.id,
                status="success",
                output=result.get("artifact", {})
            )
            
        except Exception as e:
            logger.error(f"Website generation tool failed: {e}")
            return ToolResult(
                tool_name=self.definition.id,
                status="error",
                output={},
                error=str(e)
            )
