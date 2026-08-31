"""
Design Asset Creation Pipeline

A 7-stage pipeline for visual design tasks.

Workflow adapted from OpenMontage's production philosophy:
  research → proposal → concept → assets → review → iterate → deliver

The stages below map that philosophy to Mycel's native pipeline model.
OpenMontage is NOT a runtime dependency — only its staged workflow concept
was adapted. No OpenMontage code, SDKs, or packages are used.
"""

from execution.pipelines.models import TeamPipeline, PipelineStage, PipelineInputContract, PipelineStatus

design_asset_creation = TeamPipeline(
    pipeline_id="design_asset_creation",
    team_id="creative",
    name="design_asset_creation",
    display_name="Design Asset Creation Pipeline",
    status=PipelineStatus.ACTIVE,
    input_contract=PipelineInputContract(input_type="standard_task"),
    stages=[
        PipelineStage(
            stage_id="brief_intake",
            name="brief_intake",
            display_name="Brief Intake",
            order=1,
            stage_definition_id="brief_intake_def",
            # Required: understand the task — audience, objective, brand constraints
        ),
        PipelineStage(
            stage_id="creative_concept",
            name="creative_concept",
            display_name="Creative Concept",
            order=2,
            stage_definition_id="creative_concept_def",
            # Generate 2-3 distinct creative directions (Adapted from OpenMontage's "proposal" stage)
        ),
        PipelineStage(
            stage_id="visual_direction",
            name="visual_direction",
            display_name="Visual Direction",
            order=3,
            stage_definition_id="visual_direction_def",
            # Lock one direction. Set taste/style: typography, colour palette, tone.
            # Inspired by OpenMontage's "taste-direction" meta skill concept.
        ),
        PipelineStage(
            stage_id="storyboard_layout",
            name="storyboard_layout",
            display_name="Storyboard / Layout",
            order=4,
            stage_definition_id="storyboard_layout_def",
            # Plan layout before generation — avoids expensive regeneration loops.
            # Adapted from OpenMontage's "scene_plan" stage philosophy.
        ),
        PipelineStage(
            stage_id="asset_generation",
            name="asset_generation",
            display_name="Asset Generation",
            order=5,
            stage_definition_id="asset_generation_def",
            # AI-assisted generation + bounded iteration (max 3 rounds).
            # Uses: image.generate → image.variation → design.canvas
        ),
        PipelineStage(
            stage_id="design_review",
            name="design_review",
            display_name="Design Review",
            order=6,
            stage_definition_id="design_review_def",
            # Quality gate: composition, typography, brand consistency, readability.
            # Fails stage if quality criteria not met → returns to asset_generation.
        ),
        PipelineStage(
            stage_id="final_delivery",
            name="final_delivery",
            display_name="Final Delivery",
            order=7,
            stage_definition_id="final_delivery_def",
            # Artifact validation + upload to Cloudinary storage provider.
        ),
    ]
)
