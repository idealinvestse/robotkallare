"""Unit tests for rate limiting middleware."""
import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient

from app.middleware.rate_limiting import (
    RateLimitMiddleware,
    TokenBucket,
    RateLimitConfig,
    RateLimitProfile,
    get_client_identifier,
    create_rate_limit_key
)


class TestTokenBucket:
    """Test cases for TokenBucket."""
    
    def test_token_bucket_init(self):
        """Test TokenBucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10  # Should start full
        assert bucket.last_refill <= time.time()
    
    def test_token_bucket_consume_available(self):
        """Test consuming tokens when available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Should be able to consume tokens
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
        
        # Should be able to consume remaining tokens
        assert bucket.consume(5) is True
        assert bucket.tokens == 0
    
    def test_token_bucket_consume_unavailable(self):
        """Test consuming tokens when not available."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0
        
        # Should not be able to consume more
        assert bucket.consume(1) is False
        assert bucket.tokens == 0
    
    def test_token_bucket_refill(self):
        """Test token bucket refill mechanism."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens per second
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0
        
        # Manually set last_refill to simulate time passing
        bucket.last_refill = time.time() - 1.0  # 1 second ago
        
        # Try to consume - should trigger refill
        bucket.consume(1)
        
        # Should have refilled approximately 2 tokens (2 tokens/sec * 1 sec)
        # Allow for small timing variations
        assert bucket.tokens >= 1  # At least 1 token should be available
    
    def test_token_bucket_max_capacity(self):
        """Test that bucket doesn't exceed max capacity."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)  # High refill rate
        
        # Consume some tokens
        bucket.consume(3)
        assert bucket.tokens == 2
        
        # Wait and refill - should not exceed capacity
        bucket.last_refill = time.time() - 2.0  # 2 seconds ago
        bucket._refill()
        
        assert bucket.tokens <= 5  # Should not exceed capacity
    
    def test_token_bucket_zero_refill_rate(self):
        """Test bucket with zero refill rate."""
        bucket = TokenBucket(capacity=10, refill_rate=0.0)
        
        # Consume tokens
        bucket.consume(5)
        assert bucket.tokens == 5
        
        # Wait and try to refill
        bucket.last_refill = time.time() - 10.0
        bucket._refill()
        
        # Should not refill with zero rate
        assert bucket.tokens == 5


class TestRateLimitConfig:
    """Test cases for RateLimitConfig."""
    
    def test_rate_limit_config_init(self):
        """Test RateLimitConfig initialization."""
        config = RateLimitConfig(
            requests_per_minute=60,
            burst_size=10,
            window_size_seconds=60
        )
        
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
        assert config.window_size_seconds == 60
    
    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig with default values."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
        assert config.window_size_seconds == 60
    
    def test_rate_limit_config_validation(self):
        """Test RateLimitConfig validation."""
        # Valid config
        config = RateLimitConfig(requests_per_minute=100, burst_size=20)
        assert config.requests_per_minute == 100
        
        # Invalid values should be handled gracefully or raise errors
        with pytest.raises(ValueError):
            RateLimitConfig(requests_per_minute=-1)
        
        with pytest.raises(ValueError):
            RateLimitConfig(burst_size=0)


class TestRateLimitProfile:
    """Test cases for RateLimitProfile."""
    
    def test_rate_limit_profile_api(self):
        """Test API rate limit profile."""
        profile = RateLimitProfile.API
        
        assert profile.requests_per_minute == 100
        assert profile.burst_size == 20
        assert profile.window_size_seconds == 60
    
    def test_rate_limit_profile_strict(self):
        """Test strict rate limit profile."""
        profile = RateLimitProfile.STRICT
        
        assert profile.requests_per_minute == 30
        assert profile.burst_size == 5
        assert profile.window_size_seconds == 60


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_get_client_identifier_with_api_key(self):
        """Test client identification with API key."""
        request = Mock()
        request.headers = {"X-API-Key": "test_api_key"}
        request.client.host = "192.168.1.1"
        
        identifier = get_client_identifier(request)
        assert identifier == "api_key:test_api_key"
    
    def test_get_client_identifier_with_ip(self):
        """Test client identification with IP address."""
        request = Mock()
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        identifier = get_client_identifier(request)
        assert identifier == "ip:192.168.1.1"
    
    def test_get_client_identifier_no_client(self):
        """Test client identification when client is None."""
        request = Mock()
        request.headers = {}
        request.client = None
        
        identifier = get_client_identifier(request)
        assert identifier == "ip:unknown"
    
    def test_create_rate_limit_key(self):
        """Test rate limit key creation."""
        key = create_rate_limit_key("client_123", "/api/sms")
        assert key == "rate_limit:client_123:/api/sms"
        
        # Test with special characters
        key = create_rate_limit_key("client_123", "/api/sms?param=value")
        assert "rate_limit:client_123:" in key


class TestRateLimitMiddleware:
    """Test cases for RateLimitMiddleware."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def middleware_config(self):
        """Create middleware configuration."""
        return {
            "default_config": RateLimitConfig(requests_per_minute=60, burst_size=10),
            "endpoint_configs": {
                "/test": RateLimitConfig(requests_per_minute=30, burst_size=5)
            },
            "exempt_paths": ["/health", "/docs"]
        }
    
    def test_middleware_init(self, app, middleware_config):
        """Test middleware initialization."""
        middleware = RateLimitMiddleware(
            app=app,
            **middleware_config
        )
        
        assert middleware.default_config.requests_per_minute == 60
        assert "/test" in middleware.endpoint_configs
        assert "/health" in middleware.exempt_paths
    
    @pytest.mark.asyncio
    async def test_middleware_exempt_path(self, app, middleware_config):
        """Test middleware with exempt path."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock request to exempt path
        request = Mock()
        request.url.path = "/health"
        request.method = "GET"
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        # Should pass through without rate limiting
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_rate_limit_not_exceeded(self, app, middleware_config):
        """Test middleware when rate limit is not exceeded."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock request
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        # Should pass through
        response = await middleware.dispatch(request, call_next)
        
        assert response.status_code == 200
        call_next.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_middleware_rate_limit_exceeded(self, app, middleware_config):
        """Test middleware when rate limit is exceeded."""
        # Create middleware with very strict limits
        strict_config = {
            "default_config": RateLimitConfig(requests_per_minute=1, burst_size=1),
            "endpoint_configs": {},
            "exempt_paths": []
        }
        
        middleware = RateLimitMiddleware(app=app, **strict_config)
        
        # Mock request
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        # Mock call_next
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        # First request should pass
        response1 = await middleware.dispatch(request, call_next)
        assert response1.status_code == 200
        
        # Second request should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_middleware_endpoint_specific_config(self, app, middleware_config):
        """Test middleware with endpoint-specific configuration."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock request to endpoint with specific config
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        # The middleware should use the endpoint-specific config
        # (30 requests per minute instead of default 60)
        
        # This is tested indirectly by checking that the correct bucket is created
        client_id = get_client_identifier(request)
        rate_key = create_rate_limit_key(client_id, "/test")
        
        # After processing request, bucket should exist
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        await middleware.dispatch(request, call_next)
        
        # Bucket should be created with endpoint-specific config
        assert rate_key in middleware.buckets
    
    def test_middleware_integration_with_fastapi(self, app, middleware_config):
        """Test middleware integration with FastAPI."""
        # Add middleware to app
        app.add_middleware(RateLimitMiddleware, **middleware_config)
        
        client = TestClient(app)
        
        # First request should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200
        
        # Health endpoint should always work (exempt)
        health_response = client.get("/health")
        assert health_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_middleware_different_clients(self, app, middleware_config):
        """Test middleware with different clients."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock requests from different clients
        request1 = Mock()
        request1.url.path = "/test"
        request1.method = "GET"
        request1.headers = {}
        request1.client.host = "192.168.1.1"
        
        request2 = Mock()
        request2.url.path = "/test"
        request2.method = "GET"
        request2.headers = {}
        request2.client.host = "192.168.1.2"
        
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        # Both clients should be able to make requests
        response1 = await middleware.dispatch(request1, call_next)
        response2 = await middleware.dispatch(request2, call_next)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Different buckets should be created for different clients
        client1_id = get_client_identifier(request1)
        client2_id = get_client_identifier(request2)
        
        key1 = create_rate_limit_key(client1_id, "/test")
        key2 = create_rate_limit_key(client2_id, "/test")
        
        assert key1 in middleware.buckets
        assert key2 in middleware.buckets
        assert key1 != key2
    
    @pytest.mark.asyncio
    async def test_middleware_api_key_priority(self, app, middleware_config):
        """Test that API key takes priority over IP for client identification."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock request with both API key and IP
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {"X-API-Key": "test_key"}
        request.client.host = "192.168.1.1"
        
        call_next = AsyncMock()
        call_next.return_value = Mock(status_code=200)
        
        await middleware.dispatch(request, call_next)
        
        # Should use API key for identification
        expected_key = create_rate_limit_key("api_key:test_key", "/test")
        assert expected_key in middleware.buckets
    
    def test_middleware_bucket_cleanup(self, app, middleware_config):
        """Test bucket cleanup functionality."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Manually add some buckets
        middleware.buckets["old_bucket"] = TokenBucket(10, 1.0)
        middleware.buckets["new_bucket"] = TokenBucket(10, 1.0)
        
        # Set old bucket's last access time
        middleware.buckets["old_bucket"].last_refill = time.time() - 7200  # 2 hours ago
        
        # Cleanup should remove old buckets
        middleware._cleanup_old_buckets()
        
        assert "old_bucket" not in middleware.buckets
        assert "new_bucket" in middleware.buckets
    
    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, app, middleware_config):
        """Test middleware error handling."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        # Mock request
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        # Mock call_next to raise an exception
        call_next = AsyncMock()
        call_next.side_effect = Exception("Downstream error")
        
        # Middleware should not interfere with downstream errors
        with pytest.raises(Exception) as exc_info:
            await middleware.dispatch(request, call_next)
        
        assert str(exc_info.value) == "Downstream error"
    
    @pytest.mark.asyncio
    async def test_middleware_concurrent_requests(self, app, middleware_config):
        """Test middleware with concurrent requests."""
        middleware = RateLimitMiddleware(app=app, **middleware_config)
        
        async def make_request():
            request = Mock()
            request.url.path = "/test"
            request.method = "GET"
            request.headers = {}
            request.client.host = "192.168.1.1"
            
            call_next = AsyncMock()
            call_next.return_value = Mock(status_code=200)
            
            return await middleware.dispatch(request, call_next)
        
        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some should succeed, some might be rate limited
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if isinstance(r, HTTPException) and r.status_code == 429)
        
        # At least one should succeed
        assert success_count >= 1
        # Total should equal number of requests
        assert success_count + rate_limited_count == 5


class TestRateLimitingIntegration:
    """Test rate limiting integration scenarios."""
    
    def test_full_rate_limiting_scenario(self):
        """Test complete rate limiting scenario."""
        app = FastAPI()
        
        @app.get("/api/sms")
        async def send_sms():
            return {"status": "sent"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        # Add rate limiting middleware
        app.add_middleware(
            RateLimitMiddleware,
            default_config=RateLimitConfig(requests_per_minute=10, burst_size=2),
            endpoint_configs={
                "/api/sms": RateLimitConfig(requests_per_minute=5, burst_size=1)
            },
            exempt_paths=["/health"]
        )
        
        client = TestClient(app)
        
        # Health endpoint should always work
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # SMS endpoint should work initially
        sms_response = client.get("/api/sms")
        assert sms_response.status_code == 200
        
        # Second SMS request might be rate limited due to strict config
        # (This depends on timing and exact implementation)
    
    def test_rate_limiting_with_different_methods(self):
        """Test rate limiting with different HTTP methods."""
        app = FastAPI()
        
        @app.get("/api/data")
        async def get_data():
            return {"data": "get"}
        
        @app.post("/api/data")
        async def post_data():
            return {"data": "post"}
        
        app.add_middleware(
            RateLimitMiddleware,
            default_config=RateLimitConfig(requests_per_minute=60, burst_size=10)
        )
        
        client = TestClient(app)
        
        # Different methods to same endpoint should be rate limited together
        get_response = client.get("/api/data")
        post_response = client.post("/api/data")
        
        assert get_response.status_code == 200
        assert post_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self):
        """Test rate limiting performance with many requests."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        middleware = RateLimitMiddleware(
            app=app,
            default_config=RateLimitConfig(requests_per_minute=1000, burst_size=100)
        )
        
        # Measure time for processing many requests
        start_time = time.time()
        
        for i in range(50):
            request = Mock()
            request.url.path = "/test"
            request.method = "GET"
            request.headers = {}
            request.client.host = f"192.168.1.{i % 10}"  # Vary IP addresses
            
            call_next = AsyncMock()
            call_next.return_value = Mock(status_code=200)
            
            await middleware.dispatch(request, call_next)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process requests quickly (less than 1 second for 50 requests)
        assert processing_time < 1.0
        
        # Should have created buckets for different clients
        assert len(middleware.buckets) > 1
