from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class TaskIntent(BaseModel):
    """
    Normalized representation of what the task actually requires.

    For creative media tasks, the media_operation, input_artifact_ids,
    output_artifact_type, and media_metadata fields are populated by the
    CreativeReviewStrategy during the understand() phase.
    """
    goal: str
    output_type: str = Field(description="E.g., text, video, image, code, json")
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

    # Creative media extension — populated for creative/media tasks
    media_operation: Optional[str] = Field(
        None,
        description=(
            "The resolved media operation. One of: TEXT_TO_IMAGE, IMAGE_TO_IMAGE, "
            "IMAGE_VARIATION, TEXT_TO_VIDEO, IMAGE_TO_VIDEO, MULTI_IMAGE_TO_VIDEO, IMAGE_ANIMATION. "
            "None for non-media tasks."
        )
    )
    input_artifact_ids: List[str] = Field(
        default_factory=list,
        description="ArtifactReference IDs of any source assets the user provided."
    )
    output_artifact_type: str = Field(
        "image",
        description="The type of artifact to produce: 'image' or 'video'."
    )
    media_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional creative parameters: duration_seconds, fps, motion_prompt, "
            "aspect_ratio, style, purpose, etc."
        )
    )


class PlanNode(BaseModel):
    """
    A specific step in a plan graph.
    """
    id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    required_capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="IDs of steps that must complete first")
    expected_output: Dict[str, Any] = Field(default_factory=dict)
    verification: List[str] = Field(default_factory=list)
    status: str = "pending" # pending, running, completed, failed, blocked

class Plan(BaseModel):
    """
    The structured execution plan.
    """
    goal: str
    constraints: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    steps: List[PlanNode] = Field(default_factory=list)
    verification_requirements: List[str] = Field(default_factory=list)
    version: int = 1

class Observation(BaseModel):
    """
    Structured feedback from executing a step or tool.
    """
    observation_id: str = Field(default_factory=lambda: f"obs_{uuid.uuid4().hex[:8]}")
    step_id: str
    type: str = Field(description="e.g., tool_result, clarification, verification")
    status: str
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Critique(BaseModel):
    """
    Evaluation of observations and revision plans.
    """
    status: str = Field(description="needs_revision, proceed, blocked")
    issues: List[Dict[str, str]] = Field(default_factory=list)
    recommended_action: str
    reasoning: str

class ReasoningResult(BaseModel):
    """
    The final output of the reasoning engine for an execution.
    """
    reasoning_id: str
    strategy: str
    goal: str
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    plan: Optional[Plan] = None
    verification_requirements: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    status: str
    final_output: Optional[Dict[str, Any]] = None
