"""
Custom Exception Classes for GDial Application
Provides structured error handling across the application.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    
    # General errors (1000-1999)
    INTERNAL_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    NOT_FOUND = "ERR_1002"
    ALREADY_EXISTS = "ERR_1003"
    OPERATION_FAILED = "ERR_1004"
    
    # Authentication/Authorization errors (2000-2999)
    UNAUTHORIZED = "ERR_2000"
    FORBIDDEN = "ERR_2001"
    TOKEN_EXPIRED = "ERR_2002"
    INVALID_CREDENTIALS = "ERR_2003"
    
    # Database errors (3000-3999)
    DATABASE_ERROR = "ERR_3000"
    CONSTRAINT_VIOLATION = "ERR_3001"
    TRANSACTION_FAILED = "ERR_3002"
    CONNECTION_FAILED = "ERR_3003"
    
    # External service errors (4000-4999)
    TWILIO_ERROR = "ERR_4000"
    TWILIO_AUTH_FAILED = "ERR_4001"
    TWILIO_RATE_LIMIT = "ERR_4002"
    TWILIO_INVALID_NUMBER = "ERR_4003"
    EXTERNAL_SERVICE_ERROR = "ERR_4004"
    
    # Business logic errors (5000-5999)
    INVALID_CONTACT = "ERR_5000"
    INVALID_GROUP = "ERR_5001"
    INVALID_MESSAGE = "ERR_5002"
    CAMPAIGN_ERROR = "ERR_5003"
    SCHEDULING_ERROR = "ERR_5004"
    QUOTA_EXCEEDED = "ERR_5005"
    
    # Rate limiting errors (6000-6999)
    RATE_LIMIT_EXCEEDED = "ERR_6000"
    TOO_MANY_REQUESTS = "ERR_6001"


class GDialException(Exception):
    """Base exception class for GDial application."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GDial exception.
        
        Args:
            message: Human-readable error message
            error_code: Standardized error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class ValidationError(GDialException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details
        )


class NotFoundError(GDialException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )


class AlreadyExistsError(GDialException):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} already exists"
        if identifier:
            message = f"{resource} with identifier '{identifier}' already exists"
        super().__init__(
            message=message,
            error_code=ErrorCode.ALREADY_EXISTS,
            status_code=409,
            details={"resource": resource, "identifier": identifier}
        )


class UnauthorizedError(GDialException):
    """Raised when authentication is required but not provided."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401
        )


class ForbiddenError(GDialException):
    """Raised when user lacks permission for an operation."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403
        )


class DatabaseError(GDialException):
    """Raised when a database operation fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details={"operation": operation} if operation else {}
        )


class TwilioError(GDialException):
    """Raised when Twilio API operations fail."""
    
    def __init__(
        self,
        message: str,
        twilio_code: Optional[str] = None,
        twilio_message: Optional[str] = None
    ):
        details = {}
        if twilio_code:
            details["twilio_code"] = twilio_code
        if twilio_message:
            details["twilio_message"] = twilio_message
            
        super().__init__(
            message=message,
            error_code=ErrorCode.TWILIO_ERROR,
            status_code=502,
            details=details
        )


class RateLimitError(GDialException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["limit"] = limit
            
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details
        )


class CampaignError(GDialException):
    """Raised when campaign operations fail."""
    
    def __init__(self, message: str, campaign_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CAMPAIGN_ERROR,
            status_code=400,
            details={"campaign_id": campaign_id} if campaign_id else {}
        )


class SchedulingError(GDialException):
    """Raised when message scheduling fails."""
    
    def __init__(self, message: str, schedule_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SCHEDULING_ERROR,
            status_code=400,
            details={"schedule_id": schedule_id} if schedule_id else {}
        )


class QuotaExceededError(GDialException):
    """Raised when usage quota is exceeded."""
    
    def __init__(
        self,
        resource: str,
        limit: int,
        current: int
    ):
        message = f"Quota exceeded for {resource}. Limit: {limit}, Current: {current}"
        super().__init__(
            message=message,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            status_code=429,
            details={
                "resource": resource,
                "limit": limit,
                "current": current
            }
        )
