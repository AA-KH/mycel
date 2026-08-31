"""
Session Management Module - Session state and message management
"""

from typing import Dict
from datetime import datetime

from .prompts import DEFAULT_DESIGN_PRINCIPLES


# ============ Session State Enum ============

class SessionStage:
    INPUT = "input"              # User input
    OUTLINE = "outline"          # Generate outline
    OUTLINE_REFINE = "outline_refine"  # Outline refinement
    STYLE = "style"              # Generate design style
    STYLE_REFINE = "style_refine"      # Style refinement
    GENERATE = "generate"        # Generate images
    COMPLETE = "complete"        # Complete


# ============ Session Storage ============

sessions: Dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    """Get or create session"""
    if session_id not in sessions:
        sessions[session_id] = {
            "stage": SessionStage.INPUT,
            "user_input": "",
            "outline_text": "",
            "outline_json": [],
            "style_text": "",
            "style_json": [],
            "generated_images": [],
            "reference_image_path": None,
            "messages": [],
            # User Settings
            "page_count": None,  # Page count limit
            "page_instructions": "",  # Page instructions
            "design_principles": DEFAULT_DESIGN_PRINCIPLES,  # Design principles
            # Audio transcript content
            "audio_transcript": "",  # Audio transcript text
            # Support document content
            "support_docs_text": "",  # Extracted document text
            "support_docs_files": [],  # Uploaded document list [{filename, path, text_length}]
            # Page materials
            "page_materials": {},  # {page_index_str: [{type, path, filename, description}, ...]}
        }
    return sessions[session_id]


def add_message(session_id: str, role: str, content: str):
    """Add message to session"""
    session = get_session(session_id)
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
