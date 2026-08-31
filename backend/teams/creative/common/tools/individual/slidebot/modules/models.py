"""
Data Models Module - Pydantic model definitions
"""

from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    invite_code: str


class UserInputRequest(BaseModel):
    session_id: str
    content: str
    page_count: Optional[int] = None  # Page count limit
    page_instructions: Optional[str] = None  # Per-page instructions
    design_principles: Optional[str] = None  # User custom design principles
    template_settings: Optional[dict] = None  # Template settings (color, font, etc.)


class RefineRequest(BaseModel):
    session_id: str
    feedback: str


class GenerateImageRequest(BaseModel):
    session_id: str
    page_index: int


class GenerateAllImagesRequest(BaseModel):
    session_id: str


class BaseRequest(BaseModel):
    session_id: str


class RefinePageRequest(BaseModel):
    session_id: str
    page_index: int
    feedback: str


class OutlineUpdateRequest(BaseModel):
    """Outline direct update request (used for frontend sync after editing)"""
    session_id: str
    outline_json: list
