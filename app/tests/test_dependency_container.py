"""Unit tests for dependency injection container."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session

from app.dependencies.container import (
    DIContainer,
    get_container,
    get_twilio_client,
    get_database_session,
    get_settings_service,
    get_cache_manager
)


class TestDIContainer:
    """Test cases for DIContainer."""
    
    @pytest.fixture
    def container(self):
        """Create a fresh DIContainer instance for testing."""
        return DIContainer()
    
    def test_container_init(self, container):
        """Test DIContainer initialization."""
        assert container._twilio_client is None
        assert container._settings_service is None
        assert container._cache_manager is None
    
    @patch('app.dependencies.container.Client')
    @patch('app.dependencies.container.get_settings')
    def test_twilio_client_creation(self, mock_get_settings, mock_twilio_client, container):
        """Test Twilio client creation and caching."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_get_settings.return_value = mock_settings
        
        # Mock Twilio client
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance
        
        # First call should create client
        client1 = container.twilio_client
        assert client1 == mock_client_instance
        mock_twilio_client.assert_called_once_with("test_sid", "test_token")
        
        # Second call should return cached client
        client2 = container.twilio_client
        assert client2 == mock_client_instance
        assert client1 is client2
        # Should not call Twilio client constructor again
        assert mock_twilio_client.call_count == 1
    
    @patch('app.dependencies.container.get_settings')
    def test_twilio_client_missing_credentials(self, mock_get_settings, container):
        """Test Twilio client creation with missing credentials."""
        # Mock settings with missing credentials
        mock_settings = Mock()
        mock_settings.TWILIO_ACCOUNT_SID = None
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(ValueError) as exc_info:
            _ = container.twilio_client
        
        assert "Twilio credentials not configured" in str(exc_info.value)
    
    @patch('app.dependencies.container.get_session')
    def test_database_session(self, mock_get_session, container):
        """Test database session dependency."""
        # Mock session generator
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = iter([mock_session])
        
        # Get session
        session = container.database_session
        assert session == mock_session
        mock_get_session.assert_called_once()
    
    @patch('app.dependencies.container.SettingsService')
    @patch('app.dependencies.container.get_session')
    def test_settings_service_creation(self, mock_get_session, mock_settings_service_class, container):
        """Test settings service creation and caching."""
        # Mock session
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock settings service
        mock_service_instance = Mock()
        mock_settings_service_class.return_value = mock_service_instance
        
        # First call should create service
        service1 = container.settings_service
        assert service1 == mock_service_instance
        mock_settings_service_class.assert_called_once_with(mock_session)
        
        # Second call should return cached service
        service2 = container.settings_service
        assert service2 == mock_service_instance
        assert service1 is service2
        # Should not create service again
        assert mock_settings_service_class.call_count == 1
    
    @patch('app.dependencies.container.get_cache_manager')
    def test_cache_manager_dependency(self, mock_get_cache_manager, container):
        """Test cache manager dependency."""
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_get_cache_manager.return_value = mock_cache_manager
        
        # Get cache manager
        cache_manager = container.cache_manager
        assert cache_manager == mock_cache_manager
        mock_get_cache_manager.assert_called_once()
    
    def test_container_reset(self, container):
        """Test resetting container state."""
        # Set some cached values
        with patch('app.dependencies.container.Client') as mock_client:
            with patch('app.dependencies.container.get_settings') as mock_settings:
                mock_settings.return_value = Mock(
                    TWILIO_ACCOUNT_SID="test_sid",
                    TWILIO_AUTH_TOKEN="test_token"
                )
                mock_client.return_value = Mock()
                
                # Access properties to cache them
                _ = container.twilio_client
                assert container._twilio_client is not None
        
        # Reset container
        container.reset()
        
        # Cached values should be cleared
        assert container._twilio_client is None
        assert container._settings_service is None
        assert container._cache_manager is None
    
    def test_container_health_check(self, container):
        """Test container health check."""
        with patch.object(container, 'twilio_client') as mock_twilio:
            with patch.object(container, 'database_session') as mock_db:
                with patch.object(container, 'cache_manager') as mock_cache:
                    # Mock healthy dependencies
                    mock_twilio.api.accounts.return_value.fetch.return_value = Mock(status="active")
                    mock_db.exec.return_value.first.return_value = 1
                    mock_cache.get_stats.return_value = {"total_entries": 10}
                    
                    # Health check should pass
                    health_status = container.health_check()
                    
                    assert health_status["status"] == "healthy"
                    assert "twilio" in health_status["components"]
                    assert "database" in health_status["components"]
                    assert "cache" in health_status["components"]
    
    def test_container_health_check_unhealthy(self, container):
        """Test container health check with unhealthy dependencies."""
        with patch.object(container, 'twilio_client') as mock_twilio:
            # Mock Twilio failure
            mock_twilio.api.accounts.return_value.fetch.side_effect = Exception("API Error")
            
            health_status = container.health_check()
            
            assert health_status["status"] == "unhealthy"
            assert health_status["components"]["twilio"]["status"] == "unhealthy"


class TestContainerSingleton:
    """Test container singleton behavior."""
    
    def test_get_container_singleton(self):
        """Test that get_container returns the same instance."""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
        assert isinstance(container1, DIContainer)
    
    def test_container_persistence(self):
        """Test container persistence across calls."""
        container = get_container()
        
        # Mock and cache a dependency
        with patch('app.dependencies.container.get_cache_manager') as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            
            # Access cache manager to cache it
            cache_manager1 = container.cache_manager
            
            # Get container again and access cache manager
            container2 = get_container()
            cache_manager2 = container2.cache_manager
            
            # Should be the same cached instance
            assert cache_manager1 is cache_manager2


class TestFastAPIDependencies:
    """Test FastAPI dependency functions."""
    
    @patch('app.dependencies.container.get_container')
    def test_get_twilio_client_dependency(self, mock_get_container):
        """Test get_twilio_client FastAPI dependency."""
        # Mock container and client
        mock_container = Mock()
        mock_client = Mock()
        mock_container.twilio_client = mock_client
        mock_get_container.return_value = mock_container
        
        # Call dependency function
        client = get_twilio_client()
        
        assert client == mock_client
        mock_get_container.assert_called_once()
    
    @patch('app.dependencies.container.get_container')
    def test_get_database_session_dependency(self, mock_get_container):
        """Test get_database_session FastAPI dependency."""
        # Mock container and session
        mock_container = Mock()
        mock_session = Mock(spec=Session)
        mock_container.database_session = mock_session
        mock_get_container.return_value = mock_container
        
        # Call dependency function
        session = get_database_session()
        
        assert session == mock_session
        mock_get_container.assert_called_once()
    
    @patch('app.dependencies.container.get_container')
    def test_get_settings_service_dependency(self, mock_get_container):
        """Test get_settings_service FastAPI dependency."""
        # Mock container and service
        mock_container = Mock()
        mock_service = Mock()
        mock_container.settings_service = mock_service
        mock_get_container.return_value = mock_container
        
        # Call dependency function
        service = get_settings_service()
        
        assert service == mock_service
        mock_get_container.assert_called_once()
    
    @patch('app.dependencies.container.get_container')
    def test_get_cache_manager_dependency(self, mock_get_container):
        """Test get_cache_manager FastAPI dependency."""
        # Mock container and cache manager
        mock_container = Mock()
        mock_cache_manager = Mock()
        mock_container.cache_manager = mock_cache_manager
        mock_get_container.return_value = mock_container
        
        # Call dependency function
        cache_manager = get_cache_manager()
        
        assert cache_manager == mock_cache_manager
        mock_get_container.assert_called_once()


class TestContainerIntegration:
    """Test container integration scenarios."""
    
    @patch('app.dependencies.container.Client')
    @patch('app.dependencies.container.get_settings')
    @patch('app.dependencies.container.get_session')
    @patch('app.dependencies.container.SettingsService')
    def test_full_container_integration(
        self, 
        mock_settings_service_class,
        mock_get_session,
        mock_get_settings,
        mock_twilio_client
    ):
        """Test full container integration with all dependencies."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_get_settings.return_value = mock_settings
        
        # Mock Twilio client
        mock_client_instance = Mock()
        mock_twilio_client.return_value = mock_client_instance
        
        # Mock database session
        mock_session = Mock(spec=Session)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock settings service
        mock_service_instance = Mock()
        mock_settings_service_class.return_value = mock_service_instance
        
        # Get container and access all dependencies
        container = get_container()
        
        twilio_client = container.twilio_client
        db_session = container.database_session
        settings_service = container.settings_service
        cache_manager = container.cache_manager
        
        # Verify all dependencies are correctly created
        assert twilio_client == mock_client_instance
        assert db_session == mock_session
        assert settings_service == mock_service_instance
        assert cache_manager is not None
        
        # Verify caching works
        twilio_client2 = container.twilio_client
        settings_service2 = container.settings_service
        
        assert twilio_client is twilio_client2
        assert settings_service is settings_service2
    
    def test_container_error_handling(self):
        """Test container error handling."""
        container = DIContainer()
        
        # Test with invalid Twilio credentials
        with patch('app.dependencies.container.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                TWILIO_ACCOUNT_SID=None,
                TWILIO_AUTH_TOKEN=None
            )
            
            with pytest.raises(ValueError):
                _ = container.twilio_client
    
    def test_container_lazy_loading(self):
        """Test that dependencies are lazily loaded."""
        container = DIContainer()
        
        # Initially, no dependencies should be cached
        assert container._twilio_client is None
        assert container._settings_service is None
        assert container._cache_manager is None
        
        # Access one dependency
        with patch('app.dependencies.container.get_cache_manager') as mock_cache:
            mock_cache.return_value = Mock()
            _ = container.cache_manager
            
            # Only cache manager should be cached
            assert container._cache_manager is not None
            assert container._twilio_client is None
            assert container._settings_service is None
    
    @pytest.mark.asyncio
    async def test_container_async_compatibility(self):
        """Test that container works in async contexts."""
        container = get_container()
        
        # Mock dependencies for async context
        with patch.object(container, 'cache_manager') as mock_cache:
            mock_cache.get.return_value = "cached_value"
            
            # Should work in async context
            cache_manager = container.cache_manager
            result = cache_manager.get("test_key")
            
            assert result == "cached_value"
    
    def test_container_thread_safety(self):
        """Test container thread safety."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                container = get_container()
                
                # Access cache manager (thread-safe operation)
                with patch.object(container, 'cache_manager') as mock_cache:
                    mock_cache.get_stats.return_value = {"entries": 0}
                    
                    cache_manager = container.cache_manager
                    stats = cache_manager.get_stats()
                    results.append(stats)
                    
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
    
    def test_container_memory_management(self):
        """Test container memory management."""
        container = DIContainer()
        
        # Create and cache dependencies
        with patch('app.dependencies.container.get_cache_manager') as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            
            # Access cache manager to cache it
            _ = container.cache_manager
            assert container._cache_manager is not None
        
        # Reset container to free memory
        container.reset()
        
        # Cached dependencies should be cleared
        assert container._cache_manager is None
    
    def test_container_configuration_changes(self):
        """Test container behavior with configuration changes."""
        container = DIContainer()
        
        # Initial configuration
        with patch('app.dependencies.container.get_settings') as mock_settings:
            with patch('app.dependencies.container.Client') as mock_client:
                mock_settings.return_value = Mock(
                    TWILIO_ACCOUNT_SID="sid1",
                    TWILIO_AUTH_TOKEN="token1"
                )
                mock_client_instance1 = Mock()
                mock_client.return_value = mock_client_instance1
                
                # Get Twilio client
                client1 = container.twilio_client
                assert client1 == mock_client_instance1
        
        # Configuration change - reset container
        container.reset()
        
        # New configuration
        with patch('app.dependencies.container.get_settings') as mock_settings:
            with patch('app.dependencies.container.Client') as mock_client:
                mock_settings.return_value = Mock(
                    TWILIO_ACCOUNT_SID="sid2",
                    TWILIO_AUTH_TOKEN="token2"
                )
                mock_client_instance2 = Mock()
                mock_client.return_value = mock_client_instance2
                
                # Get Twilio client again
                client2 = container.twilio_client
                assert client2 == mock_client_instance2
                assert client2 is not client1
