"""
Simple test health endpoint to debug issues
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/health")
async def test_health():
    """Simple health check without dependencies."""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Test health endpoint working"
        },
        status_code=status.HTTP_200_OK
    )

@router.get("/error")
async def test_error():
    """Test error handling."""
    raise ValueError("Test error to check error handling")
