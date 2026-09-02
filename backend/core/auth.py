"""
JWT Authentication for Mycel Operators.
"""

from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from datetime import datetime

from .config import settings

_bearer_scheme = HTTPBearer()

class CurrentOperator(BaseModel):
    user_id: str
    email: str
    company_id: str = "mycel" # Defaulting for now
    # Additional claims can be added here

def verify_id_token(token: str) -> dict:
    """Verify an HS256 JWT token and return the decoded payload."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentOperator:
    """FastAPI dependency: extract and verify JWT from Authorization header."""
    payload = verify_id_token(credentials.credentials)
    
    # Map payload to CurrentOperator
    user_id = payload.get("sub") or payload.get("user_id")
    email = payload.get("email")
    company_id = payload.get("company_id", "mycel")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user_id/sub",
        )
        
    return CurrentOperator(
        user_id=str(user_id),
        email=email or "",
        company_id=company_id
    )

CurrentUserDep = Annotated[CurrentOperator, Depends(get_current_user)]
CurrentOperatorDep = Annotated[CurrentOperator, Depends(get_current_user)]
