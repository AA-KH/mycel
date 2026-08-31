from typing import List, Dict, Optional
import logging

from tasks.models import TaskOutcome, OutputSpec, OutputModality, ArtifactType, PreviewType

logger = logging.getLogger(__name__)

class OutputResolver:
    """
    Resolves the semantic intent into a deterministic OutputSpec containing
    the modality, artifact type, and preview type.
    """
    
    # Deterministic mapping for known intents
    _INTENT_MAP = {
        "CREATE_LOGO": {
            "modality": OutputModality.IMAGE,
            "artifact_type": ArtifactType.LOGO,
            "capabilities": ["GRAPHIC_DESIGN"],
            "preview_type": PreviewType.IMAGE
        },
        "CREATE_PROMOTIONAL_POSTER": {
            "modality": OutputModality.IMAGE,
            "artifact_type": ArtifactType.POSTER,
            "capabilities": ["GRAPHIC_DESIGN"],
            "preview_type": PreviewType.IMAGE
        },
        "CREATE_BANNER": {
            "modality": OutputModality.IMAGE,
            "artifact_type": ArtifactType.BANNER,
            "capabilities": ["GRAPHIC_DESIGN"],
            "preview_type": PreviewType.IMAGE
        },
        "CREATE_SOCIAL_MEDIA_CREATIVE": {
            "modality": OutputModality.IMAGE,
            "artifact_type": ArtifactType.SOCIAL_MEDIA_CREATIVE,
            "capabilities": ["GRAPHIC_DESIGN"],
            "preview_type": PreviewType.IMAGE
        },
        "CREATE_PROMOTIONAL_WEBSITE": {
            "modality": OutputModality.WEBSITE,
            "artifact_type": ArtifactType.PROMOTIONAL_WEBSITE,
            "capabilities": ["WEB_DEVELOPMENT"],
            "preview_type": PreviewType.LIVE_WEBSITE
        },
        "CREATE_WEBSITE": {
            "modality": OutputModality.WEBSITE,
            "artifact_type": ArtifactType.WEBSITE,
            "capabilities": ["WEB_DEVELOPMENT"],
            "preview_type": PreviewType.LIVE_WEBSITE
        },
        "CREATE_LANDING_PAGE": {
            "modality": OutputModality.WEBSITE,
            "artifact_type": ArtifactType.LANDING_PAGE,
            "capabilities": ["WEB_DEVELOPMENT"],
            "preview_type": PreviewType.LIVE_WEBSITE
        },
        "CREATE_MARKETING_WEBSITE": {
            "modality": OutputModality.WEBSITE,
            "artifact_type": ArtifactType.MARKETING_WEBSITE,
            "capabilities": ["WEB_DEVELOPMENT"],
            "preview_type": PreviewType.LIVE_WEBSITE
        },
        "CREATE_INVESTOR_PITCH_DECK": {
            "modality": OutputModality.PRESENTATION,
            "artifact_type": ArtifactType.PITCH_DECK,
            "capabilities": ["PRESENTATION_CREATION"],
            "preview_type": PreviewType.SLIDE_VIEWER
        },
        "CREATE_PITCH_DECK": {
            "modality": OutputModality.PRESENTATION,
            "artifact_type": ArtifactType.PITCH_DECK,
            "capabilities": ["PRESENTATION_CREATION"],
            "preview_type": PreviewType.SLIDE_VIEWER
        },
        "FINANCIAL_FEASIBILITY": {
            "modality": OutputModality.REPORT,
            "artifact_type": ArtifactType.FINANCIAL_FEASIBILITY_REPORT,
            "capabilities": ["FINANCIAL_ANALYSIS"],
            "preview_type": PreviewType.DOCUMENT_VIEWER
        },
        "MARKET_RESEARCH": {
            "modality": OutputModality.REPORT,
            "artifact_type": ArtifactType.MARKET_RESEARCH_REPORT,
            "capabilities": ["MARKET_RESEARCH"],
            "preview_type": PreviewType.DOCUMENT_VIEWER
        },
        "LEGAL_ASSESSMENT": {
            "modality": OutputModality.REPORT,
            "artifact_type": ArtifactType.LEGAL_ASSESSMENT,
            "capabilities": ["LEGAL_ANALYSIS"],
            "preview_type": PreviewType.DOCUMENT_VIEWER
        },
        "FEASIBILITY_ANALYSIS": {
            "modality": OutputModality.REPORT,
            "artifact_type": ArtifactType.FEASIBILITY_REPORT,
            "capabilities": ["RESEARCH", "SYNTHESIS"],
            "preview_type": PreviewType.DOCUMENT_VIEWER
        }
    }

    def resolve(self, outcome: TaskOutcome) -> TaskOutcome:
        """
        Enhances the TaskOutcome by attaching strongly typed OutputSpecs.
        """
        if not outcome.intent:
            return outcome
            
        intent_key = outcome.intent.upper().strip()
        
        # We can also add substring heuristics or basic LLM fallback here later.
        # For now, deterministic check is priority.
        spec_data = None
        for key, value in self._INTENT_MAP.items():
            if key in intent_key:
                spec_data = value
                break
                
        if spec_data:
            spec = OutputSpec(
                intent=intent_key,
                modality=spec_data["modality"],
                artifact_type=spec_data["artifact_type"],
                required_capabilities=spec_data["capabilities"],
                preview_type=spec_data["preview_type"]
            )
            outcome.output_specs.append(spec)
            logger.info(f"OutputResolver mapped intent '{intent_key}' -> Modality: {spec.modality}, Artifact: {spec.artifact_type}")
        else:
            logger.debug(f"OutputResolver found no deterministic match for intent: {intent_key}")
            
        return outcome
