"""
Real Estate Domain — Mycel Autonomous Company Demo

This domain implements the Real Estate vertical slice within the existing
Mycel architecture. It does NOT replace or duplicate any Mycel core system.

Entry points:
    - api.py: FastAPI router (mounted by main.py)
    - router.py: Intent → Capability → Security → Tool → Response pipeline
    - ingestion.py: Excel upload + MongoDB persistence
    - voice.py: STT/TTS provider abstraction
    - models.py: Domain models + ConversationState store
    - tools/: ToolRegistry-compatible tools
"""
