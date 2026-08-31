import json
import re
import logging
from typing import Optional
from core.groq_engine import groq_engine
from .models import (
    HiringRequirement,
    SkillRequirement,
    ToolRequirement,
    OutputRequirement,
    ReasoningRequirement
)

logger = logging.getLogger(__name__)

REQUIREMENT_PROMPT = """You are the Hiring Requirement Analyst at Mycel.
Your job is to convert a task description into structured requirements for candidate selection.

Output a strictly valid JSON object matching this structure:
{
  "skills": [
    { "skill_id": "web_research", "minimum_proficiency": 80, "weight": 0.4, "required": false }
  ],
  "tools": [
    { "tool_id": "web.search", "required": true }
  ],
  "outputs": [
    { "type": "research_report", "required": true }
  ],
  "reasoning_profile": {
    "preferred": "research_verify",
    "required": false
  }
}

Use canonical skill IDs (e.g., 'python', 'video_editing', 'web_research').
Use canonical tool IDs (e.g., 'web.search', 'python.execute', 'video.generate').
If a task implies generating an artifact, include it in outputs (e.g. 'source_code', 'video', 'research_report').
Make sure weights across skills sum to 1.0 (approximately).
ONLY RETURN THE RAW JSON. NO MARKDOWN. NO SURROUNDING TEXT.
"""

class HiringRequirementBuilder:
    @classmethod
    async def build_from_task(cls, task_description: str, task_id: str, company_id: str) -> HiringRequirement:
        """Calls Groq to extract structured hiring requirements from a task."""
        messages = [
            {"role": "system", "content": REQUIREMENT_PROMPT},
            {"role": "user", "content": f"Extract requirements for this task:\n\n{task_description}"}
        ]
        
        try:
            response = await groq_engine.chat_completion(
                model="qwen/qwen3.8-27b",
                messages=messages,
                temperature=0.1,
            )
            raw = response.choices[0].message.content or ""
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            parsed = json.loads(json_match.group()) if json_match else json.loads(raw)
            
            skills = [SkillRequirement(**s) for s in parsed.get("skills", [])]
            tools = [ToolRequirement(**t) for t in parsed.get("tools", [])]
            outputs = [OutputRequirement(**o) for o in parsed.get("outputs", [])]
            reasoning = ReasoningRequirement(**parsed.get("reasoning_profile", {}))
            
            return HiringRequirement(
                task_id=task_id,
                company_id=company_id,
                skills=skills,
                tools=tools,
                outputs=outputs,
                reasoning_profile=reasoning
            )
        except Exception as e:
            logger.error(f"Failed to build hiring requirements: {e}. Falling back to default open requirement.")
            return HiringRequirement(task_id=task_id, company_id=company_id)
