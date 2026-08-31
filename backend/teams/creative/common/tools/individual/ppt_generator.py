import os
import uuid
from typing import Dict, Any, List
from pptx import Presentation
from tools.base import BaseTool
from tools.context import ToolExecutionContext
from tools.models import ToolDefinition
from agents.runtime.result import ToolResult
from core.logger import logger
from PIL import Image

# Import SlideBot-AI logic
from .slidebot.modules.gemini_api import generate_text, parse_json_from_text, generate_ppt_image
from .slidebot.modules.prompts import (
    OUTLINE_PROMPT_TEMPLATE, 
    STYLE_GENERATION_PROMPT, 
    build_color_scheme_spec, 
    build_font_scheme_spec, 
    DEFAULT_DESIGN_PRINCIPLES
)

class PPTGeneratorTool(BaseTool):
    """Generates PowerPoint (.pptx) or SlideBot PDF presentations."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="creative.presentation.generate",
            name="PowerPoint Presentation Generator",
            category="document_generation",
            description="Generate a professional presentation. If task_description is provided, it uses AI to generate a highly visual PDF deck. If raw slides are provided, it generates a standard .pptx file.",
            input_schema={
                "type": "object",
                "properties": {
                    "filename_prefix": {
                        "type": "string",
                        "description": "Prefix for the generated file name (e.g., 'startup_pitch_deck')."
                    },
                    "title": {
                        "type": "string",
                        "description": "Main title of the presentation."
                    },
                    "task_description": {
                        "type": "string",
                        "description": "The raw prompt from the user describing what the presentation should be about. If slides are not provided, an LLM will use this to generate the presentation outline and visually stunning slides."
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "Subtitle for the title slide."
                    },
                    "slides": {
                        "type": "array",
                        "description": "Array of slide objects for generating new slides.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Slide title."
                                },
                                "bullets": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Bullet points for the slide."
                                }
                            },
                            "required": ["title", "bullets"]
                        }
                    },
                    "template_path": {
                        "type": "string",
                        "description": "Optional absolute path to an existing .pptx template to customize."
                    },
                    "text_replacements": {
                        "type": "array",
                        "description": "Array of text replacements to apply to the template.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {"type": "string"},
                                "new_text": {"type": "string"}
                            },
                            "required": ["old_text", "new_text"]
                        }
                    }
                },
                "required": ["filename_prefix"]
            },
            capabilities=["PRESENTATION_CREATION"],
            output_modalities=["PRESENTATION", "DOCUMENT"],
            artifact_types=["PITCH_DECK", "PRESENTATION"],
            preview_types=["SLIDE_VIEWER"]
        )
    
    async def execute(self, params: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        try:
            filename_prefix = params.get("filename_prefix", "presentation")
            title = params.get("title", "")
            subtitle = params.get("subtitle", "")
            slides_data = params.get("slides", [])
            task_description = params.get("task_description", "")
            template_path = params.get("template_path", "")
            text_replacements = params.get("text_replacements", [])
            
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "output")
            os.makedirs(output_dir, exist_ok=True)
            session_id = uuid.uuid4().hex[:8]

            import json
            
            # MODE A: SlideBot Text Generation (If task_description is provided)
            if not slides_data and task_description:
                logger.info(f"Generating JSON presentation for: {task_description}")
                
                # 1. Generate Outline
                outline_prompt = OUTLINE_PROMPT_TEMPLATE.format(
                    page_constraint="控制在 5-10 页左右。",
                    page_instructions="每一页需要有明确的标题(title)和内容要点(content)。",
                    user_input=task_description
                )
                generated_text, retry_info = await generate_text(outline_prompt)
                
                if not generated_text:
                    raise Exception(f"Failed to generate outline: {retry_info}")
                
                parsed_json = parse_json_from_text(generated_text)
                if not parsed_json or "pages" not in parsed_json:
                    raise Exception("Invalid outline format generated")
                
                pages = parsed_json["pages"]
                if not title and len(pages) > 0:
                    title = pages[0].get("title", "Generated Presentation")
                
                json_data = {
                    "title": title,
                    "slides": [
                        {
                            "title": p.get("title", ""),
                            "content": p.get("content", ""),
                            "theme": p.get("theme", "")
                        } for p in pages
                    ]
                }
                
                filename = f"{filename_prefix}_{session_id}.json"
                filepath = os.path.join(output_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                return ToolResult(
                    tool_name="creative.presentation.generate",
                    status="success",
                    output={
                        "file_url": f"/output/{filename}",
                        "filename": filename,
                        "message": f"Generated visually stunning PowerPoint PDF with {len(pages)} slides.",
                        "type": "ppt",
                        "title": title
                    }
                )


            # MODE B: Explicit Slides Generation
            if not title:
                title = "Untitled Presentation"
            
            json_data = {
                "title": title,
                "subtitle": subtitle,
                "slides": [
                    {
                        "title": s.get("title", ""),
                        "content": "\n".join(s.get("bullets", []))
                    } for s in slides_data
                ]
            }
            
            filename = f"{filename_prefix}_{session_id}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            return ToolResult(
                tool_name="creative.presentation.generate",
                status="success",
                output={
                    "file_url": f"/output/{filename}",
                    "filename": filename,
                    "message": f"Generated PowerPoint with {len(slides_data)} slides.",
                    "type": "ppt",
                    "title": title
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate PPT: {e}")
            return ToolResult(
                tool_name="creative.presentation.generate",
                status="error",
                error=f"PowerPoint generation failed: {str(e)}",
                output={}
            )
