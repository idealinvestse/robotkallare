"""Basic integration tests for refactored backend components."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

from app.config.settings_service import SettingsService
from app.services.dialer_service import DialerService
from app.dependencies.container import DIContainer
from app.validation.validators import validate_phone_number, validate_message
from app.cache.cache_manager import CacheManager
from app.middleware.rate_limiting import RateLimiter, TokenBucket
from app.monitoring.health_checks import HealthChecker


class TestBasicIntegration:
    """Basic integration tests for refactored components."""
    
    @pytest.fixture
    def test_engine(self):
        """Create in-memory SQLite engine for testing."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def test_session(self, test_engine):
        """Create test database session."""
        from sqlmodel import Session
        with Session(test_engine) as session:
            yield session
    
    @pytest.fixture
    def di_container(self):
        """Create DI container for testing."""
        return DIContainer()
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager for testing."""
        return CacheManager()
    
    def test_settings_service_integration(self, test_session):
        """Test SettingsService integration with database."""
        # Create settings service
        settings_service = SettingsService(test_session)
        
        # Test setting and getting a value
        key = "test_setting"
        value = "test_value"
        
        # This should work without errors
        result = settings_service.get_system_setting(key, "default")
        assert result == "default"  # Should return default since setting doesn't exist
        
        # Test that service has expected methods
        assert hasattr(settings_service, 'get_system_setting')
        assert hasattr(settings_service, 'set_system_setting')
    
    @patch('app.services.dialer_service.TwilioCallService')
    def test_dialer_service_integration(self, mock_twilio_service, test_session):
        """Test DialerService integration with dependencies."""
        # Create dialer service
        dialer_service = DialerService(test_session)
        
        # Verify service is properly initialized
        assert dialer_service.session == test_session
        assert hasattr(dialer_service, 'twilio_service')
        assert hasattr(dialer_service, 'call_repository')
        assert hasattr(dialer_service, 'contact_repository')
        
        # Test that async methods are available
        assert asyncio.iscoroutinefunction(dialer_service.start_call_run)
        assert asyncio.iscoroutinefunction(dialer_service.dial_contact)
    
    def test_validation_integration(self):
        """Test validation functions work correctly."""
        # Test phone number validation
        valid_phone = "+1234567890"
        invalid_phone = "invalid"
        
        assert validate_phone_number(valid_phone) is True
        assert validate_phone_number(invalid_phone) is False
        
        # Test message validation
        valid_message = "Hello, this is a test message."
        empty_message = ""
        
        assert validate_message(valid_message) is True
        assert validate_message(empty_message) is False
    
    def test_cache_manager_integration(self, cache_manager):
        """Test CacheManager basic functionality."""
        # Test basic cache operations
        key = "test_key"
        value = "test_value"
        
        # Set and get value
        cache_manager.set(key, value, ttl=60)
        cached_value = cache_manager.get(key)
        
        assert cached_value == value
        
        # Test cache miss
        missing_value = cache_manager.get("non_existent_key")
        assert missing_value is None
    
    def test_rate_limiter_integration(self):
        """Test RateLimiter basic functionality."""
        # Create rate limiter with small capacity for testing
        rate_limiter = RateLimiter(
            capacity=5,
            refill_rate=1.0,
            refill_period=1.0
        )
        
        # Test that we can make requests within limit
        client_id = "test_client"
        
        # Should allow first few requests
        for _ in range(5):
            assert rate_limiter.is_allowed(client_id) is True
        
        # Should deny next request (over limit)
        assert rate_limiter.is_allowed(client_id) is False
    
    def test_token_bucket_integration(self):
        """Test TokenBucket basic functionality."""
        bucket = TokenBucket(capacity=3, refill_rate=1.0)
        
        # Should allow requests up to capacity
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        assert bucket.consume(1) is True
        
        # Should deny next request (bucket empty)
        assert bucket.consume(1) is False
    
    @pytest.mark.asyncio
    async def test_health_checker_integration(self):
        """Test HealthChecker basic functionality."""
        health_checker = HealthChecker()
        
        # Test that health checker can be created and has expected methods
        assert hasattr(health_checker, 'check_database')
        assert hasattr(health_checker, 'check_all')
        
        # Test that check methods are async
        assert asyncio.iscoroutinefunction(health_checker.check_database)
        assert asyncio.iscoroutinefunction(health_checker.check_all)
    
    def test_di_container_integration(self, di_container):
        """Test DIContainer basic functionality."""
        # Test that container can be created
        assert di_container is not None
        
        # Test that container has expected methods
        assert hasattr(di_container, 'get_twilio_client')
        assert hasattr(di_container, 'get_session')
        assert hasattr(di_container, 'health_check')
    
    @patch('app.services.dialer_service.TwilioCallService')
    def test_services_integration_flow(self, mock_twilio_service, test_session, cache_manager):
        """Test integration flow between multiple services."""
        # Create services
        settings_service = SettingsService(test_session)
        dialer_service = DialerService(test_session)
        
        # Test that services can work together
        # 1. Settings service can provide configuration
        setting_value = settings_service.get_system_setting("test_key", "default_value")
        assert setting_value == "default_value"
        
        # 2. Cache can store and retrieve data
        cache_key = "service_data"
        cache_value = {"service": "dialer", "status": "ready"}
        cache_manager.set(cache_key, cache_value, ttl=300)
        
        cached_data = cache_manager.get(cache_key)
        assert cached_data == cache_value
        
        # 3. Dialer service is properly initialized
        assert dialer_service.session == test_session
        assert hasattr(dialer_service, 'twilio_service')
        
        # 4. Validation works for service inputs
        test_phone = "+1234567890"
        test_message = "Integration test message"
        
        assert validate_phone_number(test_phone) is True
        assert validate_message(test_message) is True
    
    def test_error_handling_integration(self, test_session):
        """Test error handling across integrated components."""
        # Test settings service with invalid data
        settings_service = SettingsService(test_session)
        
        # Should handle None gracefully
        result = settings_service.get_system_setting(None, "fallback")
        # Should either return fallback or handle gracefully
        
        # Test validation with edge cases
        assert validate_phone_number(None) is False
        assert validate_phone_number("") is False
        assert validate_message(None) is False
        
        # Test cache with invalid keys
        cache_manager = CacheManager()
        result = cache_manager.get(None)
        # Should handle gracefully without crashing
