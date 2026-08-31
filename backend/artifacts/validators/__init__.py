from .base import BaseValidator
from .media import VideoValidator, ImageValidator
from .document import DocumentValidator

def get_validator_for_type(artifact_type: str) -> BaseValidator:
    validators = {
        "video": VideoValidator(),
        "image": ImageValidator(),
        "document": DocumentValidator(),
        "pdf": DocumentValidator(),
        "text": DocumentValidator()
    }
    
    # Fallback to document validator for everything else
    return validators.get(artifact_type, DocumentValidator())
