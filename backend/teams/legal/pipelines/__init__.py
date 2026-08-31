from .legal_pipeline import pipeline_instance as legal_pipeline
from .legal_research import pipeline_instance as legal_research_pipeline
from .contract_review_pipeline import pipeline_instance as contract_review_pipeline
from .compliance_pipeline import pipeline_instance as compliance_pipeline

__all__ = [
    "legal_pipeline",
    "legal_research_pipeline",
    "contract_review_pipeline",
    "compliance_pipeline"
]
