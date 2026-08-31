"""
Team Agents — Specialized Groq-powered agents for each discipline.
DEPRECATED: Team Agents
This module contains legacy generic agents for hardcoded roles.
Slated for removal once the specialized Workforce (Employee -> Agent) catalogue fully supports required domains in TOS phases.

Each agent has a focused role, appears in the Virtual Office, and
reports its result back to the Manager Agent.
"""
from agents.base_agent import BaseAgent

CODER_PROMPT = """You are an elite Lead Frontend & Full-Stack Engineer at Mycel.
Your job is to write complete, stunning, production-ready code based on requirements.

Guidelines:
- Write complete, fully working code. Never leave placeholders or incomplete snippets.
- When asked for a landing page, website, or web UI:
  - Generate a complete, self-contained single HTML file with Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>) and FontAwesome/Google Fonts.
  - Use high-quality Unsplash image URLs (e.g. https://images.unsplash.com/photo-...) for hero banners, food/coffee items, and avatars.
  - Include interactive JavaScript (mobile navbar toggle, modal dialogs, tab switching, interactive form submission alerts).
  - Design with rich aesthetics: vibrant colors, sleek cards, hero call-to-actions, customer testimonials, interactive pricing/menu cards, and booking/contact forms.
- When asked for backend:
  - Write complete Python/Node code with proper imports, models, and endpoints.
- Output the code inside a standard markdown code block: ```html ... ``` (or ```python ... ```).
- After the code block, add a brief 2-sentence explanation of what was built.
"""

RESEARCHER_PROMPT = """You are an expert Research Analyst and AI Research Agent working at Mycel.
Your job is to deeply research topics and provide structured, actionable findings.

Guidelines:
- Provide thorough, well-structured research
- Cite specific techniques, tools, libraries, or frameworks that are relevant
- Highlight best practices and potential pitfalls
- Organize findings with clear headings
- End with a "Key Takeaways" section with 3-5 bullet points
"""

REVIEWER_PROMPT = """You are a Senior Technical Reviewer and AI Review Agent working at Mycel.
Your job is to critically review work produced by other agents and identify improvements.

Guidelines:
- Evaluate correctness, security, performance, and maintainability
- Be specific about issues — quote exact lines or sections when relevant
- Suggest concrete improvements, not vague ones
- Rate the overall quality (1-10) with a justification
- Provide an "Approved" or "Needs Revision" verdict at the end
"""

TESTER_PROMPT = """You are a QA Engineer and AI Testing Agent working at Mycel.
Your job is to write comprehensive test cases and validation strategies.

Guidelines:
- Write unit tests, integration tests, and edge case tests
- Use pytest syntax for Python, Jest/Vitest syntax for TypeScript
- Cover happy paths, error paths, and boundary conditions
- Include a testing checklist at the end
- Suggest any mocking or test data strategies needed
"""


class CoderAgent(BaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Coder",
            role="coder",
            system_prompt=CODER_PROMPT,
            user_id=user_id
        )
        self.task_id = task_id

    async def run_task(self, task_description: str, model: str = "llama-3.1-8b-instant"):
        if "website" in task_description.lower() or "landing page" in task_description.lower() or "ui" in task_description.lower():
            await self.report_status("working", "Executing Website Generation using Builder.io Provider...")
            from tools.gateway import CoreToolGateway
            from agents.runtime.result import ToolRequest
            import uuid
            
            gateway = CoreToolGateway()
            request = ToolRequest(
                tool_name="website.generate",
                employee_id="sys",
                execution_id=str(uuid.uuid4()),
                arguments={
                    "task_description": task_description, 
                    "company_name": "Mycel Client"
                }
            )
            res = await gateway.execute(request)
            if res.status == "success":
                return res.output.get("content", "<!-- No content generated -->")
            else:
                return f"Failed to generate website: {res.error}"

        # Fallback to LLM generation for generic code tasks
        return await super().run_task(task_description, model)


class ResearcherAgent(BaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Researcher",
            role="researcher",
            system_prompt=RESEARCHER_PROMPT,
            user_id=user_id
        )
        self.task_id = task_id


class ReviewerAgent(BaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Reviewer",
            role="reviewer",
            system_prompt=REVIEWER_PROMPT,
            user_id=user_id
        )
        self.task_id = task_id


class TesterAgent(BaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Tester",
            role="tester",
            system_prompt=TESTER_PROMPT,
            user_id=user_id
        )
        self.task_id = task_id


class GenericAgent(BaseAgent):
    def __init__(self, team_name: str, task_id: str, user_id: str = "system"):
        role_label = " ".join([word.capitalize() for word in team_name.split('-')])
        system_prompt = f"You are the {role_label} at Mycel.\nYour job is to execute tasks related to your specific role with elite proficiency.\n\nGuidelines:\n- Follow instructions carefully.\n- Provide high-quality output.\n- Return strict JSON or markdown as required by the TaskOrchestrator WorkUnit.\n- Do not include conversational filler."
        
        super().__init__(
            name=role_label,
            role=team_name,
            system_prompt=system_prompt,
            user_id=user_id
        )
        self.task_id = task_id

from teams.intelligence.agents import MiraAgent, RaviAgent, AnikaAgent, NoorAgent

# Registry: maps team name string → agent class
TEAM_REGISTRY = {
    "coder": CoderAgent,
    "researcher": ResearcherAgent,
    "reviewer": ReviewerAgent,
    "tester": TesterAgent,
    "mira": MiraAgent,
    "ravi": RaviAgent,
    "anika": AnikaAgent,
    "noor": NoorAgent,
}

def build_team_agent(team_name: str, task_id: str, user_id: str = "system") -> BaseAgent:
    """Instantiate the correct agent class by team name."""
    name_lower = team_name.lower()
    
    # Check single-agent registry
    cls = TEAM_REGISTRY.get(name_lower)
    if cls:
        return cls(task_id=task_id, user_id=user_id)
    else:
        # Generic fallback for dynamic SCM roles (Forecasting, Procurement, etc)
        return GenericAgent(name_lower, task_id=task_id, user_id=user_id)
