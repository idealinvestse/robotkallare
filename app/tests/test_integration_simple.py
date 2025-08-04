"""Simple integration tests for refactored backend components."""
import pytest
from unittest.mock import Mock, patch

from app.config.settings_service import SettingsService
from app.services.dialer_service import DialerService
from app.validation.validators import validate_phone_number, validate_message
from app.cache.cache_manager import CacheManager
from app.middleware.rate_limiting import TokenBucket


class TestSimpleIntegration:
    """Simple integration tests for refactored components."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock()
    
    def test_settings_service_basic_integration(self, mock_session):
        """Test SettingsService basic integration."""
        # Create settings service
        settings_service = SettingsService(mock_session)
        
        # Test that service is properly initialized
        assert settings_service.session == mock_session
        
        # Test that service has expected methods
        assert hasattr(settings_service, 'get_system_setting')
        assert hasattr(settings_service, 'set_system_setting')
        assert hasattr(settings_service, 'get_sms_settings')
        assert hasattr(settings_service, 'export_settings')
    
    @patch('app.services.dialer_service.TwilioCallService')
    def test_dialer_service_basic_integration(self, mock_twilio_service, mock_session):
        """Test DialerService basic integration."""
        # Create dialer service
        dialer_service = DialerService(mock_session)
        
        # Verify service is properly initialized
        assert dialer_service.session == mock_session
        assert hasattr(dialer_service, 'twilio_service')
        assert hasattr(dialer_service, 'call_repository')
        assert hasattr(dialer_service, 'contact_repository')
        
        # Test that expected methods are available
        expected_methods = [
            'start_call_run',
            'dial_contact', 
            'get_call_run_stats',
            'update_call_run_status'
        ]
        
        for method in expected_methods:
            assert hasattr(dialer_service, method)
            assert callable(getattr(dialer_service, method))
    
    def test_validation_integration(self):
        """Test validation functions integration."""
        # Test phone number validation
        valid_phones = ["+1234567890", "+46701234567", "+44123456789"]
        invalid_phones = ["invalid", "", None, "123", "abc123"]
        
        for phone in valid_phones:
            assert validate_phone_number(phone) is True, f"Should validate {phone}"
        
        for phone in invalid_phones:
            assert validate_phone_number(phone) is False, f"Should not validate {phone}"
        
        # Test message validation
        valid_messages = ["Hello world", "Test message 123", "Åäö test"]
        invalid_messages = ["", None, " ", "\n", "\t"]
        
        for message in valid_messages:
            assert validate_message(message) is True, f"Should validate '{message}'"
        
        for message in invalid_messages:
            assert validate_message(message) is False, f"Should not validate '{message}'"
    
    def test_cache_manager_integration(self):
        """Test CacheManager integration."""
        cache_manager = CacheManager()
        
        # Test basic cache operations
        test_cases = [
            ("string_key", "string_value"),
            ("int_key", 12345),
            ("dict_key", {"nested": "data", "count": 42}),
            ("list_key", [1, 2, 3, "mixed", {"nested": True}])
        ]
        
        for key, value in test_cases:
            # Set value with TTL
            cache_manager.set(key, value, ttl=60)
            
            # Get value back
            cached_value = cache_manager.get(key)
            assert cached_value == value, f"Cache failed for {key}: {value}"
        
        # Test cache miss
        missing_value = cache_manager.get("non_existent_key")
        assert missing_value is None
        
        # Test cache clear
        cache_manager.clear()
        for key, _ in test_cases:
            assert cache_manager.get(key) is None
    
    def test_token_bucket_integration(self):
        """Test TokenBucket integration."""
        # Test different bucket configurations
        test_configs = [
            (5, 1.0),  # capacity=5, refill_rate=1.0
            (10, 2.0), # capacity=10, refill_rate=2.0
            (1, 0.5),  # capacity=1, refill_rate=0.5
        ]
        
        for capacity, refill_rate in test_configs:
            bucket = TokenBucket(capacity=capacity, refill_rate=refill_rate)
            
            # Should allow requests up to capacity
            for i in range(capacity):
                assert bucket.consume(1) is True, f"Request {i+1} should be allowed"
            
            # Should deny next request (bucket empty)
            assert bucket.consume(1) is False, "Should deny when bucket is empty"
    
    def test_services_workflow_integration(self, mock_session):
        """Test integration workflow between services."""
        # Create services
        settings_service = SettingsService(mock_session)
        cache_manager = CacheManager()
        
        # Simulate a workflow
        # 1. Get configuration from settings
        config_key = "max_retries"
        max_retries = settings_service.get_system_setting(config_key, 3)
        
        # 2. Cache the configuration
        cache_key = f"config_{config_key}"
        cache_manager.set(cache_key, max_retries, ttl=300)
        
        # 3. Retrieve from cache
        cached_config = cache_manager.get(cache_key)
        assert cached_config == max_retries
        
        # 4. Validate some input data
        phone = "+1234567890"
        message = "Test integration message"
        
        assert validate_phone_number(phone) is True
        assert validate_message(message) is True
        
        # 5. Use rate limiting
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        assert bucket.consume(1) is True  # Should allow request
    
    def test_error_handling_integration(self, mock_session):
        """Test error handling across components."""
        # Test settings service error handling
        settings_service = SettingsService(mock_session)
        
        # Should handle None keys gracefully
        try:
            result = settings_service.get_system_setting(None, "fallback")
            # Should either return fallback or handle gracefully
        except Exception as e:
            # If it raises an exception, it should be a reasonable one
            assert isinstance(e, (TypeError, ValueError, AttributeError))
        
        # Test validation error handling
        edge_cases = [None, "", " ", "\n", "\t", 123, [], {}]
        
        for case in edge_cases:
            # Should not crash on edge cases
            try:
                phone_result = validate_phone_number(case)
                message_result = validate_message(case)
                # Results should be boolean
                assert isinstance(phone_result, bool)
                assert isinstance(message_result, bool)
            except Exception as e:
                # If exceptions are raised, they should be reasonable
                assert isinstance(e, (TypeError, ValueError, AttributeError))
        
        # Test cache error handling
        cache_manager = CacheManager()
        
        # Should handle None keys gracefully
        try:
            result = cache_manager.get(None)
            # Should return None or handle gracefully
        except Exception as e:
            # Should not crash the application
            assert isinstance(e, (TypeError, ValueError, KeyError))
    
    @patch('app.services.dialer_service.TwilioCallService')
    def test_component_isolation(self, mock_twilio_service, mock_session):
        """Test that components are properly isolated."""
        # Create multiple instances of services
        settings_service1 = SettingsService(mock_session)
        settings_service2 = SettingsService(mock_session)
        
        dialer_service1 = DialerService(mock_session)
        dialer_service2 = DialerService(mock_session)
        
        # Services should be independent instances
        assert settings_service1 is not settings_service2
        assert dialer_service1 is not dialer_service2
        
        # But they should share the same session
        assert settings_service1.session == settings_service2.session
        assert dialer_service1.session == dialer_service2.session
        
        # Cache managers should be independent
        cache1 = CacheManager()
        cache2 = CacheManager()
        
        # Set different values in each cache
        cache1.set("test", "value1")
        cache2.set("test", "value2")
        
        # They should maintain separate state
        assert cache1.get("test") == "value1"
        assert cache2.get("test") == "value2"
