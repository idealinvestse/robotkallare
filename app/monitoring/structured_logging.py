"""Structured logging system with correlation IDs and metrics."""
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from contextvars import ContextVar
from functools import wraps

from app.config import get_settings

settings = get_settings()

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
request_path_var: ContextVar[Optional[str]] = ContextVar('request_path', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context information if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        request_path = request_path_var.get()
        if request_path:
            log_data["request_path"] = request_path
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, logger_name: str = "performance"):
        """Initialize performance logger."""
        self.logger = logging.getLogger(logger_name)
    
    def log_operation_time(
        self, 
        operation: str, 
        duration_ms: float, 
        success: bool = True,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log operation timing information.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            success: Whether the operation was successful
            extra_data: Additional data to log
        """
        log_data = {
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Operation {operation} completed", extra=log_data)
    
    def log_database_query(
        self, 
        query_type: str, 
        table: str, 
        duration_ms: float,
        row_count: Optional[int] = None
    ) -> None:
        """Log database query performance."""
        self.log_operation_time(
            f"db_{query_type}",
            duration_ms,
            extra_data={
                "table": table,
                "query_type": query_type,
                "row_count": row_count
            }
        )
    
    def log_api_call(
        self, 
        service: str, 
        endpoint: str, 
        duration_ms: float,
        status_code: Optional[int] = None,
        success: bool = True
    ) -> None:
        """Log external API call performance."""
        self.log_operation_time(
            f"api_{service}",
            duration_ms,
            success=success,
            extra_data={
                "service": service,
                "endpoint": endpoint,
                "status_code": status_code
            }
        )


class BusinessLogger:
    """Logger for business events and user actions."""
    
    def __init__(self, logger_name: str = "business"):
        """Initialize business logger."""
        self.logger = logging.getLogger(logger_name)
    
    def log_sms_sent(
        self, 
        contact_id: str, 
        message_id: str, 
        phone_number: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log SMS sending event."""
        log_data = {
            "event": "sms_sent",
            "contact_id": contact_id,
            "message_id": message_id,
            "phone_number": phone_number[-4:] if phone_number else None,  # Only last 4 digits for privacy
            "success": success
        }
        
        if error_message:
            log_data["error_message"] = error_message
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"SMS {'sent' if success else 'failed'}", extra=log_data)
    
    def log_call_made(
        self, 
        contact_id: str, 
        message_id: str, 
        phone_number: str,
        call_sid: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log call making event."""
        log_data = {
            "event": "call_made",
            "contact_id": contact_id,
            "message_id": message_id,
            "phone_number": phone_number[-4:] if phone_number else None,
            "call_sid": call_sid,
            "success": success
        }
        
        if error_message:
            log_data["error_message"] = error_message
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Call {'initiated' if success else 'failed'}", extra=log_data)
    
    def log_user_action(
        self, 
        action: str, 
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log user action for audit trail."""
        log_data = {
            "event": "user_action",
            "action": action,
            "user_id": user_id or user_id_var.get(),
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        self.logger.info(f"User action: {action}", extra=log_data)


class SecurityLogger:
    """Logger for security events and potential threats."""
    
    def __init__(self, logger_name: str = "security"):
        """Initialize security logger."""
        self.logger = logging.getLogger(logger_name)
    
    def log_authentication_attempt(
        self, 
        user_id: Optional[str], 
        ip_address: str,
        success: bool = True,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempt."""
        log_data = {
            "event": "auth_attempt",
            "user_id": user_id,
            "ip_address": ip_address,
            "success": success
        }
        
        if failure_reason:
            log_data["failure_reason"] = failure_reason
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Authentication {'successful' if success else 'failed'}", extra=log_data)
    
    def log_rate_limit_exceeded(
        self, 
        ip_address: str, 
        endpoint: str,
        limit: int,
        window_seconds: int
    ) -> None:
        """Log rate limit violation."""
        log_data = {
            "event": "rate_limit_exceeded",
            "ip_address": ip_address,
            "endpoint": endpoint,
            "limit": limit,
            "window_seconds": window_seconds
        }
        
        self.logger.warning("Rate limit exceeded", extra=log_data)
    
    def log_suspicious_activity(
        self, 
        activity_type: str, 
        ip_address: str,
        details: Dict[str, Any]
    ) -> None:
        """Log suspicious activity."""
        log_data = {
            "event": "suspicious_activity",
            "activity_type": activity_type,
            "ip_address": ip_address,
            "details": details
        }
        
        self.logger.error("Suspicious activity detected", extra=log_data)


def setup_structured_logging() -> None:
    """Setup structured logging configuration."""
    # Create structured formatter
    formatter = StructuredFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler with structured formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler for persistent logging
    try:
        file_handler = logging.FileHandler('logs/gdial.log')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, IOError):
        # If we can't create log file, continue with console only
        pass
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def set_user_context(user_id: str, request_path: Optional[str] = None) -> None:
    """Set user context for logging."""
    user_id_var.set(user_id)
    if request_path:
        request_path_var.set(request_path)


def log_with_timing(operation_name: str, logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            perf_logger = PerformanceLogger()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger.log_operation_time(operation_name, duration_ms, success=True)
                func_logger.debug(f"{operation_name} completed in {duration_ms:.2f}ms")
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger.log_operation_time(
                    operation_name, 
                    duration_ms, 
                    success=False,
                    extra_data={"error": str(e)}
                )
                func_logger.error(f"{operation_name} failed after {duration_ms:.2f}ms: {str(e)}")
                
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            perf_logger = PerformanceLogger()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger.log_operation_time(operation_name, duration_ms, success=True)
                func_logger.debug(f"{operation_name} completed in {duration_ms:.2f}ms")
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger.log_operation_time(
                    operation_name, 
                    duration_ms, 
                    success=False,
                    extra_data={"error": str(e)}
                )
                func_logger.error(f"{operation_name} failed after {duration_ms:.2f}ms: {str(e)}")
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global logger instances
performance_logger = PerformanceLogger()
business_logger = BusinessLogger()
security_logger = SecurityLogger()
