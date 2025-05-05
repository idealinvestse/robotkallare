import os
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration --- 
# Fetch from environment variables, provide defaults if needed
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_should_be_in_env") # IMPORTANT: Use a strong, random key in .env
ALGORITHM = os.getenv("ALGORITHM", "HS256") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# --- Password Hashing --- 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Token Handling --- 
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- TODO: Add functions for token decoding and user dependency --- 
# Example:
# def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(...)
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#     user = get_user(db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user
