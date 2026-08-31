"""
SlideBot Module Package

Contains the following modules:
- config: Configuration constants
- prompts: Prompt templates
- models: Pydantic data models
- asr: iFLYTEK ASR voice transcription
- invite_codes: Invite code management
- session: Session management
- gemini_api: Gemini API calls
- visit_counter: Visit counting
- doc_extract: Document text extraction
"""

from .config import *
from .prompts import *
from .models import *
from .asr import XfyunASR, parse_xfyun_result, format_dialogue_as_text
from .invite_codes import (
    load_invite_codes, 
    save_invite_codes, 
    verify_invite_code, 
    record_login, 
    get_login_records_from_csv
)
from .session import SessionStage, sessions, get_session, add_message
from .gemini_api import (
    get_image_base64,
    get_image_mime_type,
    parse_json_from_text,
    generate_text,
    generate_ppt_image,
    analyze_template_design
)
from .visit_counter import get_visit_count, increment_visit_count
from .doc_extract import (
    extract_text_from_document,
    extract_table_from_file
)
