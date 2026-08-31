"""
REST API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from datetime import datetime, timezone, timedelta
import jwt
from core.mongodb import mongodb_connection
from core.config import settings
import uuid
import hashlib
import secrets

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Get active sessions for the office."""
    db = mongodb_connection.db
    # Filter stale sessions (> 12 hours)
    twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
    
    cursor = db.agent_sessions.find({
        "last_heartbeat_at": {"$gte": twelve_hours_ago}
    })
    sessions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if isinstance(doc.get("last_heartbeat_at"), datetime):
            doc["last_heartbeat_at"] = doc["last_heartbeat_at"].isoformat()
        sessions.append(doc)
    return sessions

@router.get("/keys")
async def get_keys(current_user: dict = Depends(get_current_user)):
    """Get API keys."""
    db = mongodb_connection.db
    cursor = db.api_keys.find({"user_id": current_user["sub"]})
    keys = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc.get("id", str(doc["_id"]))
        keys.append(doc)
    return keys

@router.post("/keys")
async def create_key(data: dict, current_user: dict = Depends(get_current_user)):
    """Create API key."""
    db = mongodb_connection.db
    name = data.get("name", "New Key")
    user_id = current_user["sub"]
    
    # Generate API key
    raw_key = secrets.token_urlsafe(32)
    api_key = f"avo_{raw_key}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    key_id = str(uuid.uuid4())
    
    await db.api_keys.insert_one({
        "id": key_id,
        "name": name,
        "key_hash": key_hash,
        "user_id": user_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"id": key_id, "api_key": api_key, "name": name}

@router.delete("/keys/{key_id}")
async def delete_key(key_id: str, current_user: dict = Depends(get_current_user)):
    db = mongodb_connection.db
    # Only delete if user owns it
    await db.api_keys.delete_one({"id": key_id, "user_id": current_user["sub"]})
    return {"status": "ok"}
