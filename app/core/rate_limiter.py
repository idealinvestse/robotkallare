"""
Rate Limiting Module for GDial
Implements rate limiting to prevent API abuse and ensure fair usage.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from redis import Redis
import json

from app.core.exceptions import RateLimitError, ErrorCode

logger = logging.getLogger(__name__)


class RateLimitStrategy:
    """Base class for rate limiting strategies."""
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed.
        
        Args:
            key: Unique identifier for rate limiting
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        raise NotImplementedError


class InMemoryRateLimiter(RateLimitStrategy):
    """In-memory rate limiter using sliding window."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        """
        Initialize in-memory rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            burst_size: Max burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # Store request timestamps for each key
        self.minute_windows: Dict[str, deque] = defaultdict(deque)
        self.hour_windows: Dict[str, deque] = defaultdict(deque)
        self.burst_buckets: Dict[str, int] = defaultdict(int)
        self.last_reset: Dict[str, float] = {}
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed based on rate limits."""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(key, current_time)
        
        # Check burst limit
        if not self._check_burst_limit(key, current_time):
            return False, 1  # Retry after 1 second for burst
        
        # Check minute limit
        minute_count = len(self.minute_windows[key])
        if minute_count >= self.requests_per_minute:
            oldest_minute = self.minute_windows[key][0]
            retry_after = int(60 - (current_time - oldest_minute)) + 1
            return False, retry_after
        
        # Check hour limit
        hour_count = len(self.hour_windows[key])
        if hour_count >= self.requests_per_hour:
            oldest_hour = self.hour_windows[key][0]
            retry_after = int(3600 - (current_time - oldest_hour)) + 1
            return False, retry_after
        
        # Record the request
        self.minute_windows[key].append(current_time)
        self.hour_windows[key].append(current_time)
        self.burst_buckets[key] += 1
        
        return True, None
    
    def _cleanup_old_entries(self, key: str, current_time: float):
        """Remove entries older than the window."""
        # Clean minute window (60 seconds)
        while self.minute_windows[key] and \
              current_time - self.minute_windows[key][0] > 60:
            self.minute_windows[key].popleft()
        
        # Clean hour window (3600 seconds)
        while self.hour_windows[key] and \
              current_time - self.hour_windows[key][0] > 3600:
            self.hour_windows[key].popleft()
    
    def _check_burst_limit(self, key: str, current_time: float) -> bool:
        """Check burst limit using token bucket algorithm."""
        # Reset burst bucket every second
        if key not in self.last_reset or \
           current_time - self.last_reset[key] >= 1.0:
            self.burst_buckets[key] = 0
            self.last_reset[key] = current_time
        
        return self.burst_buckets[key] < self.burst_size


class RedisRateLimiter(RateLimitStrategy):
    """Redis-based rate limiter for distributed systems."""
    
    def __init__(
        self,
        redis_client: Redis,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        """
        Initialize Redis rate limiter.
        
        Args:
            redis_client: Redis client instance
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
        """
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """Check if request is allowed using Redis."""
        current_time = time.time()
        
        # Use Redis pipelines for atomic operations
        pipe = self.redis.pipeline()
        
        # Minute window key
        minute_key = f"rate_limit:minute:{key}"
        minute_window_start = current_time - 60
        
        # Hour window key
        hour_key = f"rate_limit:hour:{key}"
        hour_window_start = current_time - 3600
        
        # Remove old entries and count current
        pipe.zremrangebyscore(minute_key, 0, minute_window_start)
        pipe.zcard(minute_key)
        pipe.zremrangebyscore(hour_key, 0, hour_window_start)
        pipe.zcard(hour_key)
        
        results = pipe.execute()
        minute_count = results[1]
        hour_count = results[3]
        
        # Check limits
        if minute_count >= self.requests_per_minute:
            # Get oldest entry to calculate retry_after
            oldest = self.redis.zrange(minute_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(60 - (current_time - oldest[0][1])) + 1
                return False, retry_after
            return False, 60
        
        if hour_count >= self.requests_per_hour:
            # Get oldest entry to calculate retry_after
            oldest = self.redis.zrange(hour_key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(3600 - (current_time - oldest[0][1])) + 1
                return False, retry_after
            return False, 3600
        
        # Add current request
        pipe = self.redis.pipeline()
        pipe.zadd(minute_key, {str(current_time): current_time})
        pipe.expire(minute_key, 60)
        pipe.zadd(hour_key, {str(current_time): current_time})
        pipe.expire(hour_key, 3600)
        pipe.execute()
        
        return True, None


class RateLimiter:
    """Main rate limiter class with multiple strategies."""
    
    def __init__(
        self,
        strategy: Optional[RateLimitStrategy] = None,
        enabled: bool = True,
        whitelist: Optional[set] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            strategy: Rate limiting strategy to use
            enabled: Whether rate limiting is enabled
            whitelist: Set of IPs to whitelist
        """
        self.strategy = strategy or InMemoryRateLimiter()
        self.enabled = enabled
        self.whitelist = whitelist or set()
        
        # Track rate limit statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "whitelisted_requests": 0
        }
    
    def get_client_key(self, request: Request) -> str:
        """
        Get unique client identifier from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Unique client key
        """
        # Try to get authenticated user ID
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check rate limit for request.
        
        Args:
            request: FastAPI request object
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if not self.enabled:
            return
        
        self.stats["total_requests"] += 1
        
        # Get client identifier
        client_key = self.get_client_key(request)
        
        # Check whitelist
        if client_key in self.whitelist:
            self.stats["whitelisted_requests"] += 1
            return
        
        # Add endpoint to key for endpoint-specific limits
        endpoint_key = f"{client_key}:{request.url.path}"
        
        # Check rate limit
        is_allowed, retry_after = self.strategy.is_allowed(endpoint_key)
        
        if not is_allowed:
            self.stats["blocked_requests"] += 1
            
            logger.warning(
                f"Rate limit exceeded for {client_key} on {request.url.path}",
                extra={
                    "client_key": client_key,
                    "endpoint": request.url.path,
                    "retry_after": retry_after
                }
            )
            
            raise RateLimitError(
                message="Rate limit exceeded. Please try again later.",
                retry_after=retry_after,
                limit=self.strategy.requests_per_minute
            )
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        return {
            **self.stats,
            "block_rate": (
                self.stats["blocked_requests"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0 else 0
            )
        }


class EndpointRateLimiter:
    """Rate limiter with endpoint-specific configurations."""
    
    def __init__(self):
        """Initialize endpoint rate limiter."""
        self.endpoint_limits = {
            # Authentication endpoints - stricter limits
            "/api/auth/login": (10, 100),  # 10/min, 100/hour
            "/api/auth/register": (5, 50),
            
            # SMS/Call endpoints - moderate limits
            "/api/trigger-sms": (30, 500),
            "/api/trigger-call": (30, 500),
            "/api/trigger-campaign": (10, 100),
            
            # Read endpoints - relaxed limits
            "/api/contacts": (100, 2000),
            "/api/groups": (100, 2000),
            "/api/messages": (100, 2000),
            
            # Default for all other endpoints
            "default": (60, 1000)
        }
        
        self.limiters = {}
    
    def get_limiter(self, endpoint: str) -> RateLimiter:
        """Get rate limiter for specific endpoint."""
        if endpoint not in self.limiters:
            # Get limits for endpoint
            limits = self.endpoint_limits.get(
                endpoint,
                self.endpoint_limits["default"]
            )
            
            # Create limiter with endpoint-specific limits
            strategy = InMemoryRateLimiter(
                requests_per_minute=limits[0],
                requests_per_hour=limits[1]
            )
            
            self.limiters[endpoint] = RateLimiter(strategy=strategy)
        
        return self.limiters[endpoint]
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check rate limit for request based on endpoint."""
        # Find matching endpoint pattern
        endpoint = request.url.path
        
        # Try exact match first
        if endpoint not in self.endpoint_limits:
            # Try prefix match for parameterized routes
            for pattern in self.endpoint_limits.keys():
                if endpoint.startswith(pattern.rsplit("/", 1)[0]):
                    endpoint = pattern
                    break
            else:
                endpoint = "default"
        
        limiter = self.get_limiter(endpoint)
        await limiter.check_rate_limit(request)


# Global rate limiter instance
rate_limiter = EndpointRateLimiter()


def get_rate_limiter() -> EndpointRateLimiter:
    """Get the global rate limiter instance."""
    return rate_limiter


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, rate_limiter: EndpointRateLimiter):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            rate_limiter: Rate limiter instance
        """
        self.app = app
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or rate limit error
        """
        try:
            # Check rate limit
            await self.rate_limiter.check_rate_limit(request)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = "60"
            response.headers["X-RateLimit-Remaining"] = "59"  # Simplified
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except RateLimitError as e:
            # Return rate limit error response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=e.to_dict(),
                headers={
                    "Retry-After": str(e.details.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(e.details.get("limit", 60))
                }
            )


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response from next handler or rate limit error
    """
    try:
        # Check rate limit
        await rate_limiter.check_rate_limit(request)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        client_key = rate_limiter.limiters.get(
            request.url.path, 
            rate_limiter.limiters.get("default")
        ).get_client_key(request)
        
        response.headers["X-RateLimit-Limit"] = "60"
        response.headers["X-RateLimit-Remaining"] = "59"  # Simplified
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
        
    except RateLimitError as e:
        # Return rate limit error response
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=e.to_dict(),
            headers={
                "Retry-After": str(e.details.get("retry_after", 60)),
                "X-RateLimit-Limit": str(e.details.get("limit", 60))
            }
        )
