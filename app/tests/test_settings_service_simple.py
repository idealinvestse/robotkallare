"""Simple tests for SettingsService to verify refactored implementation."""
import pytest
from unittest.mock import Mock, patch
from sqlmodel import Session

from app.config.settings_service import SettingsService
from app.config.settings_models import SystemSetting


class TestSettingsServiceSimple:
    """Simple test cases for SettingsService."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def settings_service(self, mock_session):
        """Create SettingsService instance with mocked session."""
        return SettingsService(mock_session)
    
    def test_init(self, mock_session):
        """Test SettingsService initialization."""
        service = SettingsService(mock_session)
        assert service.session == mock_session
    
    def test_available_methods(self, settings_service):
        """Test that expected methods are available."""
        expected_methods = [
            'get_system_setting',
            'set_system_setting',
            'get_sms_settings',
            'get_dtmf_settings',
            'export_settings',
            'initialize_default_settings'
        ]
        
        for method in expected_methods:
            assert hasattr(settings_service, method), f"Method {method} not found"
    
    @patch('app.config.settings_models.SystemSetting.get_value')
    def test_get_system_setting(self, mock_get_value, settings_service):
        """Test getting a system setting."""
        # Mock the SystemSetting.get_value method
        mock_get_value.return_value = "test_value"
        
        # Call the method
        result = settings_service.get_system_setting("test_key", "default")
        
        # Verify
        assert result == "test_value"
        mock_get_value.assert_called_once_with(settings_service.session, "test_key", "default")
    
    @patch('app.config.settings_models.SystemSetting.set_value')
    def test_set_system_setting(self, mock_set_value, settings_service):
        """Test setting a system setting."""
        # Mock the SystemSetting.set_value method
        mock_setting = Mock()
        mock_set_value.return_value = mock_setting
        
        # Call the method
        result = settings_service.set_system_setting("test_key", "test_value")
        
        # Verify
        assert result == mock_setting
        mock_set_value.assert_called_once()
    
    def test_service_has_session(self, settings_service, mock_session):
        """Test that service has access to session."""
        assert settings_service.session == mock_session
    
    def test_service_methods_callable(self, settings_service):
        """Test that service methods are callable."""
        # These should not raise AttributeError
        assert callable(getattr(settings_service, 'get_system_setting'))
        assert callable(getattr(settings_service, 'set_system_setting'))
        assert callable(getattr(settings_service, 'get_sms_settings'))
        assert callable(getattr(settings_service, 'export_settings'))
