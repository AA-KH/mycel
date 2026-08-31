"""
Auth Module - API Routes for JWT
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from core.config import settings
from core.mongodb import mongodb_connection
from .schemas import UserLogin, UserRegister, TokenResponse

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=1440) # 24 hours
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    db = mongodb_connection.db if mongodb_connection.client is not None else None
    if db is not None:
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(user.password)
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_password,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc)
    }
    if db is not None:
        await db.users.insert_one(new_user)
    
    token_data = {"sub": user_id, "email": user.email, "role": "user"}
    access_token = create_access_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        user={"id": user_id, "email": user.email, "name": user.name, "is_admin": False}
    )

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    db = mongodb_connection.db if mongodb_connection.client is not None else None
    if db is not None:
        db_user = await db.users.find_one({"email": user.email})
        
        if not db_user or not pwd_context.verify(user.password, db_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = db_user["id"]
        is_admin = db_user.get("is_admin", False)
        name = db_user.get("name")
    else:
        # Mock login if DB is down
        user_id = str(uuid.uuid4())
        is_admin = True
        name = "Mock User"
    
    token_data = {"sub": user_id, "email": user.email, "role": "admin" if is_admin else "user"}
    access_token = create_access_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        user={"id": user_id, "email": user.email, "name": name, "is_admin": is_admin}
    )

@router.get("/me")
async def get_me():
    # Will be protected by dependency in the api_router
    pass
