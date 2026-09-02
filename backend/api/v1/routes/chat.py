from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from core.mongodb import mongodb_connection
from core.groq_engine import engine_manager
from core.vector_store import MongoDBVectorStore
from core.auth import get_current_user
from core.logger import logger

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    project_id: str
    messages: List[ChatMessage]

@router.post("/rag")
async def chat_rag(request: ChatRequest, _ = Depends(get_current_user)):
    """
    RAG-enabled chat endpoint.
    Retrieves context from MongoDBVectorStore based on the last user message,
    pulls the project architecture report, and generates an answer.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
        
    last_user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), None)
    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    db = mongodb_connection.db
    
    # 1. Fetch Project Details
    project = await db.projects.find_one({"project_id": request.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    architecture_report = project.get("architecture_report", {})
    
    # 2. Retrieve Context via Vector Store
    vector_store = MongoDBVectorStore()
    docs = await vector_store.search(request.project_id, last_user_message, top_k=4)
    
    context_text = "\n\n".join([doc["text"] for doc in docs])
    
    # 3. Construct System Prompt
    system_prompt = f"""You are "The Architect" — the AI assistant of MYCEL Mission Control.
You are helping the user understand the supply-chain architecture for their project '{project.get('productName') or project.get('businessType')}'.

### THE ARCHITECTURE BLUEPRINT (JSON)
{architecture_report}

### ADDITIONAL KNOWLEDGE BASE CONTEXT (From Uploaded Documents)
{context_text if context_text else 'No specific documents retrieved for this query.'}

Rules:
- Ground every answer in the blueprint and knowledge base context above.
- If something is not covered, say so plainly.
- Keep answers concise and clear — short paragraphs or tight bullet lists. No markdown headings.
- Stay in character as the mission's architect assistant.
"""
    
    # 4. Construct Messages
    groq_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages[-5:]:  # Keep last 5 messages for context
        groq_messages.append({"role": msg.role, "content": msg.content})
        
    # 5. Call LLM
    try:
        response = await engine_manager.chat_completion(
            model="qwen/qwen3.8-27b",  # Organization's standard model on Groq
            messages=groq_messages,
            team_id="atlas"  # Use Atlas's keys since it's the architect
        )
        answer = response.choices[0].message.content
        return {"role": "assistant", "content": answer}
    except Exception as e:
        logger.error(f"RAG Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")
