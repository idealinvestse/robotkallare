"""Unit tests for SettingsService."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session

from app.config.settings_service import SettingsService
from app.config.settings_models import SystemSetting, DtmfSetting, SmsSettings
from app.config.settings_defaults import DEFAULT_SYSTEM_SETTINGS


class TestSettingsService:
    """Test cases for SettingsService."""
    
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
    
    def test_get_setting_exists(self, settings_service, mock_session):
        """Test getting an existing setting."""
        # Arrange
        mock_setting = SystemSetting(key="test_key", value="test_value")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        result = settings_service.get_setting("test_key")
        
        # Assert
        assert result == "test_value"
        mock_session.exec.assert_called_once()
    
    def test_get_setting_not_exists_with_default(self, settings_service, mock_session):
        """Test getting a non-existing setting with default value."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        
        # Act
        result = settings_service.get_setting("non_existing_key", "default_value")
        
        # Assert
        assert result == "default_value"
    
    def test_get_setting_not_exists_no_default(self, settings_service, mock_session):
        """Test getting a non-existing setting without default value."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        
        # Act
        result = settings_service.get_setting("non_existing_key")
        
        # Assert
        assert result is None
    
    def test_set_setting_new(self, settings_service, mock_session):
        """Test setting a new setting."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        
        # Act
        settings_service.set_setting("new_key", "new_value")
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify the setting was created correctly
        added_setting = mock_session.add.call_args[0][0]
        assert isinstance(added_setting, SystemSetting)
        assert added_setting.key == "new_key"
        assert added_setting.value == "new_value"
    
    def test_set_setting_existing(self, settings_service, mock_session):
        """Test updating an existing setting."""
        # Arrange
        mock_setting = SystemSetting(key="existing_key", value="old_value")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        settings_service.set_setting("existing_key", "new_value")
        
        # Assert
        assert mock_setting.value == "new_value"
        mock_session.commit.assert_called_once()
        mock_session.add.assert_not_called()
    
    def test_get_all_settings(self, settings_service, mock_session):
        """Test getting all settings."""
        # Arrange
        mock_settings = [
            SystemSetting(key="key1", value="value1"),
            SystemSetting(key="key2", value="value2")
        ]
        mock_session.exec.return_value.all.return_value = mock_settings
        
        # Act
        result = settings_service.get_all_settings()
        
        # Assert
        expected = {"key1": "value1", "key2": "value2"}
        assert result == expected
    
    def test_delete_setting_exists(self, settings_service, mock_session):
        """Test deleting an existing setting."""
        # Arrange
        mock_setting = SystemSetting(key="test_key", value="test_value")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        result = settings_service.delete_setting("test_key")
        
        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(mock_setting)
        mock_session.commit.assert_called_once()
    
    def test_delete_setting_not_exists(self, settings_service, mock_session):
        """Test deleting a non-existing setting."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None
        
        # Act
        result = settings_service.delete_setting("non_existing_key")
        
        # Assert
        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_initialize_defaults(self, settings_service, mock_session):
        """Test initializing default settings."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None  # No existing settings
        
        # Act
        settings_service.initialize_defaults()
        
        # Assert
        # Should add multiple default settings
        assert mock_session.add.call_count > 0
        mock_session.commit.assert_called_once()
    
    def test_get_sms_settings(self, settings_service, mock_session):
        """Test getting SMS settings."""
        # Arrange
        mock_settings = [
            SystemSetting(key="sms_enabled", value="true"),
            SystemSetting(key="sms_rate_limit", value="10"),
            SystemSetting(key="sms_retry_attempts", value="3")
        ]
        mock_session.exec.return_value.all.return_value = mock_settings
        
        # Act
        result = settings_service.get_sms_settings()
        
        # Assert
        assert isinstance(result, SmsSettings)
        assert result.enabled is True
        assert result.rate_limit == 10
        assert result.retry_attempts == 3
    
    def test_update_sms_settings(self, settings_service, mock_session):
        """Test updating SMS settings."""
        # Arrange
        sms_settings = SmsSettings(
            enabled=False,
            rate_limit=5,
            retry_attempts=2
        )
        
        # Mock existing settings
        mock_session.exec.return_value.first.side_effect = [
            SystemSetting(key="sms_enabled", value="true"),
            SystemSetting(key="sms_rate_limit", value="10"),
            SystemSetting(key="sms_retry_attempts", value="3")
        ]
        
        # Act
        settings_service.update_sms_settings(sms_settings)
        
        # Assert
        assert mock_session.commit.call_count == 3  # One for each setting
    
    def test_get_dtmf_settings(self, settings_service, mock_session):
        """Test getting DTMF settings."""
        # Arrange
        mock_dtmf_settings = [
            DtmfSetting(digit="1", action="transfer", value="+1234567890"),
            DtmfSetting(digit="2", action="hangup", value="")
        ]
        mock_session.exec.return_value.all.return_value = mock_dtmf_settings
        
        # Act
        result = settings_service.get_dtmf_settings()
        
        # Assert
        assert len(result) == 2
        assert result[0].digit == "1"
        assert result[0].action == "transfer"
        assert result[1].digit == "2"
        assert result[1].action == "hangup"
    
    def test_update_dtmf_setting(self, settings_service, mock_session):
        """Test updating a DTMF setting."""
        # Arrange
        mock_dtmf = DtmfSetting(digit="1", action="transfer", value="+1234567890")
        mock_session.exec.return_value.first.return_value = mock_dtmf
        
        # Act
        settings_service.update_dtmf_setting("1", "hangup", "")
        
        # Assert
        assert mock_dtmf.action == "hangup"
        assert mock_dtmf.value == ""
        mock_session.commit.assert_called_once()
    
    def test_export_settings(self, settings_service, mock_session):
        """Test exporting settings to dictionary."""
        # Arrange
        mock_system_settings = [
            SystemSetting(key="key1", value="value1"),
            SystemSetting(key="key2", value="value2")
        ]
        mock_dtmf_settings = [
            DtmfSetting(digit="1", action="transfer", value="+1234567890")
        ]
        
        mock_session.exec.side_effect = [
            Mock(all=Mock(return_value=mock_system_settings)),
            Mock(all=Mock(return_value=mock_dtmf_settings))
        ]
        
        # Act
        result = settings_service.export_settings()
        
        # Assert
        assert "system_settings" in result
        assert "dtmf_settings" in result
        assert result["system_settings"]["key1"] == "value1"
        assert len(result["dtmf_settings"]) == 1
    
    def test_validate_settings_valid(self, settings_service):
        """Test validating valid settings."""
        # Arrange
        settings_dict = {
            "system_settings": {
                "app_name": "GDial",
                "max_concurrent_calls": "10"
            },
            "dtmf_settings": [
                {"digit": "1", "action": "transfer", "value": "+1234567890"}
            ]
        }
        
        # Act
        result = settings_service.validate_settings(settings_dict)
        
        # Assert
        assert result is True
    
    def test_validate_settings_invalid(self, settings_service):
        """Test validating invalid settings."""
        # Arrange
        settings_dict = {
            "system_settings": {
                "max_concurrent_calls": "invalid_number"  # Should be numeric
            }
        }
        
        # Act
        result = settings_service.validate_settings(settings_dict)
        
        # Assert
        assert result is False
    
    def test_backup_settings(self, settings_service, mock_session):
        """Test backing up settings."""
        # Arrange
        mock_system_settings = [
            SystemSetting(key="key1", value="value1")
        ]
        mock_dtmf_settings = [
            DtmfSetting(digit="1", action="transfer", value="+1234567890")
        ]
        
        mock_session.exec.side_effect = [
            Mock(all=Mock(return_value=mock_system_settings)),
            Mock(all=Mock(return_value=mock_dtmf_settings))
        ]
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.dump') as mock_json_dump:
                # Act
                result = settings_service.backup_settings("backup.json")
                
                # Assert
                assert result is True
                mock_open.assert_called_once_with("backup.json", "w")
                mock_json_dump.assert_called_once()
    
    def test_restore_settings(self, settings_service, mock_session):
        """Test restoring settings from backup."""
        # Arrange
        backup_data = {
            "system_settings": {
                "key1": "value1"
            },
            "dtmf_settings": [
                {"digit": "1", "action": "transfer", "value": "+1234567890"}
            ]
        }
        
        with patch('builtins.open', create=True):
            with patch('json.load', return_value=backup_data):
                # Act
                result = settings_service.restore_settings("backup.json")
                
                # Assert
                assert result is True
                mock_session.commit.assert_called()
    
    def test_get_setting_with_type_conversion(self, settings_service, mock_session):
        """Test getting setting with automatic type conversion."""
        # Arrange
        mock_setting = SystemSetting(key="numeric_key", value="123")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        result = settings_service.get_setting("numeric_key", default_value=0, convert_type=int)
        
        # Assert
        assert result == 123
        assert isinstance(result, int)
    
    def test_get_setting_type_conversion_error(self, settings_service, mock_session):
        """Test getting setting with type conversion error."""
        # Arrange
        mock_setting = SystemSetting(key="invalid_numeric", value="not_a_number")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        result = settings_service.get_setting("invalid_numeric", default_value=0, convert_type=int)
        
        # Assert
        assert result == 0  # Should return default value on conversion error
    
    @pytest.mark.asyncio
    async def test_async_operations(self, settings_service, mock_session):
        """Test that service works with async operations."""
        # This test ensures the service can be used in async contexts
        # even though the operations themselves are synchronous
        
        # Arrange
        mock_setting = SystemSetting(key="async_key", value="async_value")
        mock_session.exec.return_value.first.return_value = mock_setting
        
        # Act
        result = settings_service.get_setting("async_key")
        
        # Assert
        assert result == "async_value"
