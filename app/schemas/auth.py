from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Schema for user login request body."""
    email: str
    password: str

class TokenResponse(BaseModel):
    """Schema for the response containing the access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int # Expiry time in seconds from now
