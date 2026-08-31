from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

from .models import TaskIntent, Plan, Observation, Critique

class ReasoningContext(BaseModel):
    """
    Context isolated for a specific reasoning execution session.
    """
    reasoning_id: str = Field(default_factory=lambda: f"reason_{uuid.uuid4().hex[:8]}")
    execution_id: str
    task_id: str
    employee_id: str
    
    intent: Optional[TaskIntent] = None
    plan: Optional[Plan] = None
    
    observations: List[Observation] = Field(default_factory=list)
    critiques: List[Critique] = Field(default_factory=list)
    
    # Internal variables for compression
    compressed_summary: str = ""
    max_observations_before_compression: int = 20

    def add_observation(self, obs: Observation):
        self.observations.append(obs)
        if len(self.observations) > self.max_observations_before_compression:
            self.compress_context()
            
    def compress_context(self):
        """
        Compresses old observations into a summary to keep context window manageable.
        In a real system, this would call an LLM to summarize self.observations[:-5].
        For now, we just simulate truncation.
        """
        if len(self.observations) > 5:
            older = self.observations[:-5]
            self.compressed_summary += f" [Summarized {len(older)} past observations]"
            self.observations = self.observations[-5:]

    def to_llm_context(self) -> str:
        """
        Formats the current context efficiently for the LLM.
        """
        ctx = f"Reasoning Session: {self.reasoning_id}\n"
        if self.intent:
            ctx += f"Goal: {self.intent.goal}\n"
            ctx += f"Expected Output: {self.intent.output_type}\n"
        
        if self.compressed_summary:
            ctx += f"Past Summary: {self.compressed_summary}\n"
            
        if self.observations:
            ctx += "Recent Observations:\n"
            for o in self.observations[-3:]:
                ctx += f"- Step {o.step_id} [{o.status}]: {o.summary}\n"
                if o.data:
                    ctx += f"  Data: {o.data}\n"
                
        if self.critiques:
            ctx += "Recent Critiques:\n"
            last_critique = self.critiques[-1]
            ctx += f"- Status: {last_critique.status}, Action: {last_critique.recommended_action}\n"
            
        return ctx
