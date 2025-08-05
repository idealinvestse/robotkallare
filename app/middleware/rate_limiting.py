"""Rate limiting middleware for API protection."""
import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter with sliding window."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.last_cleanup = time.time()
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for the given identifier.
        
        Args:
            identifier: Unique identifier (IP address, API key, etc.)
            
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Get request history for this identifier
        request_times = self.requests[identifier]
        
        # Remove requests outside the current window
        cutoff_time = current_time - self.window_seconds
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Check if under the limit
        if len(request_times) < self.max_requests:
            request_times.append(current_time)
            return True
        
        return False
    
    def get_reset_time(self, identifier: str) -> Optional[float]:
        """
        Get the time when the rate limit will reset for the identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Unix timestamp when limit resets, or None if no limit
        """
        request_times = self.requests.get(identifier)
        if not request_times:
            return None
        
        # The limit will reset when the oldest request falls out of the window
        return request_times[0] + self.window_seconds
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old entries to prevent memory leaks."""
        cutoff_time = current_time - self.window_seconds * 2  # Keep some buffer
        
        identifiers_to_remove = []
        for identifier, request_times in self.requests.items():
            # Remove old requests
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            # If no recent requests, mark for removal
            if not request_times:
                identifiers_to_remove.append(identifier)
        
        # Remove empty entries
        for identifier in identifiers_to_remove:
            del self.requests[identifier]


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(
        self,
        default_limit: int = 1000,
        window_seconds: int = 60,
        per_endpoint_limits: Optional[Dict[str, int]] = None,
        exempt_paths: Optional[list] = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            default_limit: Default requests per window
            window_seconds: Time window in seconds
            per_endpoint_limits: Custom limits per endpoint
            exempt_paths: Paths exempt from rate limiting
        """
        self.default_limiter = RateLimiter(default_limit, window_seconds)
        self.endpoint_limiters = {}
        self.window_seconds = window_seconds
        self.exempt_paths = exempt_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        
        # Create custom limiters for specific endpoints
        if per_endpoint_limits:
            for endpoint, limit in per_endpoint_limits.items():
                self.endpoint_limiters[endpoint] = RateLimiter(limit, window_seconds)
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_identifier(request)
        
        # Choose appropriate limiter
        limiter = self._get_limiter_for_path(request.url.path)
        
        # Check rate limit
        if not limiter.is_allowed(client_id):
            reset_time = limiter.get_reset_time(client_id)
            retry_after = int(reset_time - time.time()) if reset_time else self.window_seconds
            
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limiting headers
        request_times = limiter.requests.get(client_id, deque())
        remaining = max(0, limiter.max_requests - len(request_times))
        reset_time = limiter.get_reset_time(client_id)
        
        response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        
        if reset_time:
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client."""
        # Try API key first
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if api_key:
            return f"api_key:{api_key[:8]}..."  # Use first 8 chars for logging
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}"
    
    def _get_limiter_for_path(self, path: str) -> RateLimiter:
        """Get appropriate rate limiter for the given path."""
        # Check for exact endpoint matches
        for endpoint, limiter in self.endpoint_limiters.items():
            if path.startswith(endpoint):
                return limiter
        
        # Use default limiter
        return self.default_limiter


# Pre-configured rate limiters for different use cases
class RateLimitProfiles:
    """Pre-configured rate limiting profiles."""
    
    @staticmethod
    def get_api_middleware():
        """Get rate limiting middleware for API endpoints."""
        return RateLimitMiddleware(
            default_limit=1000,  # 1000 requests per minute
            window_seconds=60,
            per_endpoint_limits={
                "/trigger-sms": 100,      # SMS endpoints are more limited
                "/trigger-custom-sms": 50,
                "/trigger-call": 50,      # Call endpoints are more limited
                "/manual-call": 20,
                "/burn-message": 10       # Burn messages are very limited
            },
            exempt_paths=["/health", "/metrics", "/docs", "/openapi.json", "/static"]
        )
    
    @staticmethod
    def get_strict_middleware():
        """Get strict rate limiting for high-security endpoints."""
        return RateLimitMiddleware(
            default_limit=100,   # 100 requests per minute
            window_seconds=60,
            per_endpoint_limits={
                "/admin": 20,
                "/settings": 30,
                "/users": 50
            }
        )
    
    @staticmethod
    def get_development_middleware():
        """Get lenient rate limiting for development."""
        return RateLimitMiddleware(
            default_limit=10000,  # Very high limit for development
            window_seconds=60,
            exempt_paths=["/health", "/metrics", "/docs", "/openapi.json", "/static", "/debug"]
        )


# Aliases and additional classes for test compatibility
TokenBucket = RateLimiter  # Alias for backward compatibility
RateLimitConfig = RateLimitMiddleware  # Alias for configuration
RateLimitProfile = RateLimitProfiles  # Alias for profiles


def get_client_identifier(request: Request) -> str:
    """Get unique identifier for the client (module-level function)."""
    # Try API key first
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if api_key:
        return f"api_key:{api_key[:8]}..."  # Use first 8 chars for logging
    
    # Fall back to IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    
    return f"ip:{request.client.host}"


def create_rate_limit_key(identifier: str, endpoint: str = None) -> str:
    """Create a rate limit key for the given identifier and endpoint."""
    if endpoint:
        return f"{identifier}:{endpoint}"
    return identifier
