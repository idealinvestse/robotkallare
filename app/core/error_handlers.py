"""
Error Handling Middleware and Handlers for GDial
Provides centralized error handling for the FastAPI application.
"""

import logging
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from twilio.base.exceptions import TwilioRestException

from app.core.exceptions import (
    GDialException,
    ValidationError,
    DatabaseError,
    TwilioError,
    ErrorCode
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handler for the application."""
    
    @staticmethod
    def format_error_response(
        error_code: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        Format error response in a consistent structure.
        
        Args:
            error_code: Standardized error code
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details
            request_id: Request tracking ID
        
        Returns:
            JSONResponse with formatted error
        """
        content = {
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            }
        }
        
        if request_id:
            content["error"]["request_id"] = request_id
        
        return JSONResponse(
            status_code=status_code,
            content=content
        )
    
    @staticmethod
    async def handle_gdial_exception(
        request: Request,
        exc: GDialException
    ) -> JSONResponse:
        """Handle custom GDial exceptions."""
        request_id = request.headers.get("X-Request-ID")
        
        # Log the error with appropriate level
        if exc.status_code >= 500:
            logger.error(
                f"Server error: {exc.error_code} - {exc.message}",
                extra={
                    "error_code": exc.error_code,
                    "details": exc.details,
                    "request_id": request_id,
                    "path": request.url.path
                }
            )
        else:
            logger.warning(
                f"Client error: {exc.error_code} - {exc.message}",
                extra={
                    "error_code": exc.error_code,
                    "details": exc.details,
                    "request_id": request_id,
                    "path": request.url.path
                }
            )
        
        return ErrorHandler.format_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=request_id
        )
    
    @staticmethod
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI validation errors."""
        request_id = request.headers.get("X-Request-ID")
        
        # Extract validation error details
        errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(
            f"Validation error on {request.url.path}",
            extra={
                "errors": errors,
                "request_id": request_id
            }
        )
        
        return ErrorHandler.format_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": errors},
            request_id=request_id
        )
    
    @staticmethod
    async def handle_http_exception(
        request: Request,
        exc: HTTPException
    ) -> JSONResponse:
        """Handle standard HTTP exceptions."""
        request_id = request.headers.get("X-Request-ID")
        
        # Map HTTP status codes to error codes
        error_code_map = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR
        }
        
        error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "request_id": request_id,
                "path": request.url.path
            }
        )
        
        return ErrorHandler.format_error_response(
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id
        )
    
    @staticmethod
    async def handle_database_error(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle database-related errors."""
        request_id = request.headers.get("X-Request-ID")
        
        if isinstance(exc, IntegrityError):
            # Handle constraint violations
            message = "Database constraint violation"
            error_code = ErrorCode.CONSTRAINT_VIOLATION
            status_code = 409
            
            # Try to extract more specific information
            if "UNIQUE constraint failed" in str(exc):
                message = "Resource already exists"
                error_code = ErrorCode.ALREADY_EXISTS
            elif "FOREIGN KEY constraint failed" in str(exc):
                message = "Referenced resource does not exist"
                error_code = ErrorCode.NOT_FOUND
                status_code = 404
        
        elif isinstance(exc, OperationalError):
            message = "Database connection error"
            error_code = ErrorCode.CONNECTION_FAILED
            status_code = 503
        
        elif isinstance(exc, DataError):
            message = "Invalid data for database operation"
            error_code = ErrorCode.VALIDATION_ERROR
            status_code = 400
        
        else:
            message = "Database operation failed"
            error_code = ErrorCode.DATABASE_ERROR
            status_code = 500
        
        logger.error(
            f"Database error: {type(exc).__name__} - {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "request_id": request_id,
                "path": request.url.path
            }
        )
        
        return ErrorHandler.format_error_response(
            error_code=error_code,
            message=message,
            status_code=status_code,
            details={"error_type": type(exc).__name__},
            request_id=request_id
        )
    
    @staticmethod
    async def handle_twilio_error(
        request: Request,
        exc: TwilioRestException
    ) -> JSONResponse:
        """Handle Twilio API errors."""
        request_id = request.headers.get("X-Request-ID")
        
        # Map Twilio error codes to our error codes
        if exc.code == 20003:
            error_code = ErrorCode.TWILIO_AUTH_FAILED
            message = "Twilio authentication failed"
            status_code = 401
        elif exc.code == 21211:
            error_code = ErrorCode.TWILIO_INVALID_NUMBER
            message = "Invalid phone number"
            status_code = 400
        elif exc.code == 20429:
            error_code = ErrorCode.TWILIO_RATE_LIMIT
            message = "Twilio rate limit exceeded"
            status_code = 429
        else:
            error_code = ErrorCode.TWILIO_ERROR
            message = f"Twilio error: {exc.msg}"
            status_code = 502
        
        logger.error(
            f"Twilio error: {exc.code} - {exc.msg}",
            extra={
                "twilio_code": exc.code,
                "twilio_message": exc.msg,
                "request_id": request_id,
                "path": request.url.path
            }
        )
        
        return ErrorHandler.format_error_response(
            error_code=error_code,
            message=message,
            status_code=status_code,
            details={
                "twilio_code": exc.code,
                "twilio_message": exc.msg
            },
            request_id=request_id
        )
    
    @staticmethod
    async def handle_generic_error(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exceptions."""
        request_id = request.headers.get("X-Request-ID")
        
        # Log the full traceback for debugging
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "request_id": request_id,
                "path": request.url.path
            }
        )
        
        # Return a generic error response (don't expose internals)
        return ErrorHandler.format_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An internal server error occurred",
            status_code=500,
            request_id=request_id
        )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom GDial exceptions
    app.add_exception_handler(GDialException, ErrorHandler.handle_gdial_exception)
    
    # FastAPI validation errors
    app.add_exception_handler(RequestValidationError, ErrorHandler.handle_validation_error)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, ErrorHandler.handle_http_exception)
    app.add_exception_handler(StarletteHTTPException, ErrorHandler.handle_http_exception)
    
    # Database errors
    app.add_exception_handler(IntegrityError, ErrorHandler.handle_database_error)
    app.add_exception_handler(OperationalError, ErrorHandler.handle_database_error)
    app.add_exception_handler(DataError, ErrorHandler.handle_database_error)
    
    # Twilio errors
    app.add_exception_handler(TwilioRestException, ErrorHandler.handle_twilio_error)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, ErrorHandler.handle_generic_error)
    
    logger.info("Error handlers registered successfully")
