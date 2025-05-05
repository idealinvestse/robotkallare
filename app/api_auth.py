import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from .schemas.auth import TokenResponse
from .security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES

# In a real app, you'd have functions to create/verify tokens and check users

from sqlmodel import Session
from sqlalchemy import select, or_
from app.models import User
from app.database import get_session

# --- Helper Function ---
def get_user_by_credential(session: Session, credential: str):
    """Retrieve user from DB by username or email."""
    stmt = select(User).where(or_(User.username == credential, User.email == credential))
    # Ensure we get a User instance rather than a row mapping
    return session.exec(stmt).scalars().first()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """Authenticates user and returns a JWT access token."""
    logging.info(f"Login attempt for user: {form_data.username}")

    user = get_user_by_credential(session, form_data.username)

    if not user or user.disabled:
        logging.warning(f"Login failed: User '{form_data.username}' not found or disabled.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(form_data.password, user.hashed_password):
        logging.warning(f"Login failed: Incorrect password for user '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
        # Add other claims like roles or permissions if needed: "scopes": user["scopes"]
    )
    
    logging.info(f"Login successful for: {user.username}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )

# Add other auth routes here (e.g., /refresh, /register, /me) later
