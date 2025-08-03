"""Unit tests for health checks and monitoring."""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from app.monitoring.health_checks import (
    HealthCheckResult,
    HealthChecker,
    get_health_checker
)


class TestHealthCheckResult:
    """Test cases for HealthCheckResult."""
    
    def test_health_check_result_init(self):
        """Test HealthCheckResult initialization."""
        result = HealthCheckResult(
            name="test_check",
            status="healthy",
            message="All good",
            details={"key": "value"}
        )
        
        assert result.name == "test_check"
        assert result.status == "healthy"
        assert result.message == "All good"
        assert result.details == {"key": "value"}
        assert isinstance(result.timestamp, datetime)
    
    def test_health_check_result_to_dict(self):
        """Test converting HealthCheckResult to dictionary."""
        result = HealthCheckResult(
            name="test_check",
            status="healthy",
            message="All good"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["name"] == "test_check"
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "All good"
        assert "timestamp" in result_dict
        assert isinstance(result_dict["timestamp"], str)
    
    def test_health_check_result_default_details(self):
        """Test HealthCheckResult with default details."""
        result = HealthCheckResult("test", "healthy")
        
        assert result.details == {}
        
        result_dict = result.to_dict()
        assert result_dict["details"] == {}


class TestHealthChecker:
    """Test cases for HealthChecker."""
    
    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance for testing."""
        return HealthChecker()
    
    @patch('app.monitoring.health_checks.get_container')
    @patch('app.monitoring.health_checks.get_cache_manager')
    def test_health_checker_init(self, mock_get_cache_manager, mock_get_container, health_checker):
        """Test HealthChecker initialization."""
        mock_container = Mock()
        mock_cache_manager = Mock()
        mock_get_container.return_value = mock_container
        mock_get_cache_manager.return_value = mock_cache_manager
        
        checker = HealthChecker()
        
        assert checker.container == mock_container
        assert checker.cache_manager == mock_cache_manager
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_session')
    @patch('app.monitoring.health_checks.get_async_session')
    @patch('app.monitoring.health_checks.async_db_manager')
    async def test_check_database_health_success(self, mock_async_db_manager, mock_get_async_session, mock_get_session, health_checker):
        """Test successful database health check."""
        # Mock sync session
        mock_sync_session = Mock()
        mock_sync_session.exec.return_value.first.return_value = 1
        mock_get_session.return_value = iter([mock_sync_session])
        
        # Mock async session
        mock_async_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_async_session.execute.return_value = mock_result
        mock_get_async_session.return_value.__aenter__.return_value = mock_async_session
        
        # Mock connection info
        mock_async_db_manager.get_connection_info.return_value = {"status": "connected"}
        
        # Run health check
        result = await health_checker.check_database_health()
        
        assert result.name == "database"
        assert result.status == "healthy"
        assert "Database is accessible" in result.message
        assert "response_time_ms" in result.details
        assert "connection_info" in result.details
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_session')
    async def test_check_database_health_failure(self, mock_get_session, health_checker):
        """Test database health check failure."""
        # Mock session to raise exception
        mock_get_session.side_effect = Exception("Database connection failed")
        
        # Run health check
        result = await health_checker.check_database_health()
        
        assert result.name == "database"
        assert result.status == "unhealthy"
        assert "Database connection failed" in result.message
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_settings')
    async def test_check_twilio_health_success(self, mock_get_settings, health_checker):
        """Test successful Twilio health check."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.TWILIO_ACCOUNT_SID = "test_sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_get_settings.return_value = mock_settings
        
        # Mock Twilio client
        mock_twilio_client = Mock()
        mock_account = Mock()
        mock_account.status = "active"
        mock_account.type = "Full"
        mock_twilio_client.api.accounts.return_value.fetch.return_value = mock_account
        
        health_checker.container = Mock()
        health_checker.container.twilio_client = mock_twilio_client
        
        # Run health check
        result = await health_checker.check_twilio_health()
        
        assert result.name == "twilio"
        assert result.status == "healthy"
        assert "Twilio API is accessible" in result.message
        assert result.details["account_status"] == "active"
        assert result.details["account_type"] == "Full"
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_settings')
    async def test_check_twilio_health_missing_credentials(self, mock_get_settings, health_checker):
        """Test Twilio health check with missing credentials."""
        # Mock settings with missing credentials
        mock_settings = Mock()
        mock_settings.TWILIO_ACCOUNT_SID = None
        mock_settings.TWILIO_AUTH_TOKEN = "test_token"
        mock_get_settings.return_value = mock_settings
        
        # Run health check
        result = await health_checker.check_twilio_health()
        
        assert result.name == "twilio"
        assert result.status == "unhealthy"
        assert "Twilio credentials not configured" in result.message
    
    @pytest.mark.asyncio
    async def test_check_cache_health_success(self, health_checker):
        """Test successful cache health check."""
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_cache_manager.get.return_value = {"timestamp": time.time(), "test": True}
        mock_cache_manager.get_stats.return_value = {
            "total_entries": 100,
            "entries_with_ttl": 50,
            "memory_usage_bytes": 1024
        }
        
        health_checker.cache_manager = mock_cache_manager
        
        # Run health check
        result = await health_checker.check_cache_health()
        
        assert result.name == "cache"
        assert result.status == "healthy"
        assert "Cache system is working" in result.message
        assert "stats" in result.details
    
    @pytest.mark.asyncio
    async def test_check_cache_health_failure(self, health_checker):
        """Test cache health check failure."""
        # Mock cache manager to raise exception
        mock_cache_manager = Mock()
        mock_cache_manager.set.side_effect = Exception("Cache error")
        
        health_checker.cache_manager = mock_cache_manager
        
        # Run health check
        result = await health_checker.check_cache_health()
        
        assert result.name == "cache"
        assert result.status == "unhealthy"
        assert "Cache system error" in result.message
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_rabbitmq_connection')
    async def test_check_rabbitmq_health_success(self, mock_get_rabbitmq_connection, health_checker):
        """Test successful RabbitMQ health check."""
        # Mock RabbitMQ connection
        mock_connection = Mock()
        mock_connection.is_closed = False
        mock_get_rabbitmq_connection.return_value = mock_connection
        
        # Run health check
        result = await health_checker.check_rabbitmq_health()
        
        assert result.name == "rabbitmq"
        assert result.status == "healthy"
        assert "RabbitMQ connection is active" in result.message
        assert result.details["connection_state"] == "open"
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_rabbitmq_connection')
    async def test_check_rabbitmq_health_failure(self, mock_get_rabbitmq_connection, health_checker):
        """Test RabbitMQ health check failure."""
        # Mock RabbitMQ connection failure
        mock_get_rabbitmq_connection.side_effect = Exception("Connection failed")
        
        # Run health check
        result = await health_checker.check_rabbitmq_health()
        
        assert result.name == "rabbitmq"
        assert result.status == "degraded"
        assert "RabbitMQ check failed" in result.message
    
    @pytest.mark.asyncio
    @patch('shutil.disk_usage')
    async def test_check_disk_space_healthy(self, mock_disk_usage, health_checker):
        """Test disk space check when healthy."""
        # Mock disk usage: total=100GB, used=50GB, free=50GB
        mock_disk_usage.return_value = (100 * 1024**3, 50 * 1024**3, 50 * 1024**3)
        
        # Run health check
        result = await health_checker.check_disk_space()
        
        assert result.name == "disk_space"
        assert result.status == "healthy"
        assert "50.00GB free" in result.message
        assert result.details["free_gb"] == 50.0
        assert result.details["used_percent"] == 50.0
    
    @pytest.mark.asyncio
    @patch('shutil.disk_usage')
    async def test_check_disk_space_critical(self, mock_disk_usage, health_checker):
        """Test disk space check when critical."""
        # Mock disk usage: total=100GB, used=99.5GB, free=0.5GB
        mock_disk_usage.return_value = (100 * 1024**3, 99.5 * 1024**3, 0.5 * 1024**3)
        
        # Run health check
        result = await health_checker.check_disk_space()
        
        assert result.name == "disk_space"
        assert result.status == "unhealthy"
        assert "Critical" in result.message
        assert "0.50GB disk space remaining" in result.message
    
    @pytest.mark.asyncio
    @patch('psutil.virtual_memory')
    async def test_check_memory_usage_healthy(self, mock_virtual_memory, health_checker):
        """Test memory usage check when healthy."""
        # Mock memory info: 16GB total, 8GB used (50%)
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 8 * 1024**3
        mock_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_memory
        
        # Run health check
        result = await health_checker.check_memory_usage()
        
        assert result.name == "memory"
        assert result.status == "healthy"
        assert "50.0%" in result.message
        assert result.details["used_percent"] == 50.0
    
    @pytest.mark.asyncio
    @patch('psutil.virtual_memory')
    async def test_check_memory_usage_critical(self, mock_virtual_memory, health_checker):
        """Test memory usage check when critical."""
        # Mock memory info: 16GB total, 15.2GB used (95%)
        mock_memory = Mock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 0.8 * 1024**3
        mock_memory.percent = 95.0
        mock_virtual_memory.return_value = mock_memory
        
        # Run health check
        result = await health_checker.check_memory_usage()
        
        assert result.name == "memory"
        assert result.status == "unhealthy"
        assert "Critical" in result.message
        assert "95.0%" in result.message
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_no_psutil(self, health_checker):
        """Test memory usage check when psutil is not available."""
        with patch('app.monitoring.health_checks.psutil', None):
            # This should be handled by ImportError in the actual implementation
            # For testing, we'll mock the ImportError
            with patch('psutil.virtual_memory', side_effect=ImportError("psutil not available")):
                result = await health_checker.check_memory_usage()
                
                assert result.name == "memory"
                assert result.status == "degraded"
                assert "psutil not available" in result.message
    
    @pytest.mark.asyncio
    async def test_run_all_checks_healthy(self, health_checker):
        """Test running all health checks when all are healthy."""
        # Mock all individual check methods to return healthy results
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                # Mock all checks to return healthy results
                                mock_db.return_value = HealthCheckResult("database", "healthy")
                                mock_twilio.return_value = HealthCheckResult("twilio", "healthy")
                                mock_cache.return_value = HealthCheckResult("cache", "healthy")
                                mock_rabbitmq.return_value = HealthCheckResult("rabbitmq", "healthy")
                                mock_disk.return_value = HealthCheckResult("disk_space", "healthy")
                                mock_memory.return_value = HealthCheckResult("memory", "healthy")
                                
                                # Run all checks
                                result = await health_checker.run_all_checks()
                                
                                assert result["status"] == "healthy"
                                assert len(result["checks"]) == 6
                                assert result["summary"]["healthy"] == 6
                                assert result["summary"]["unhealthy"] == 0
    
    @pytest.mark.asyncio
    async def test_run_all_checks_mixed(self, health_checker):
        """Test running all health checks with mixed results."""
        # Mock individual check methods with mixed results
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                # Mock mixed results
                                mock_db.return_value = HealthCheckResult("database", "healthy")
                                mock_twilio.return_value = HealthCheckResult("twilio", "unhealthy")
                                mock_cache.return_value = HealthCheckResult("cache", "degraded")
                                mock_rabbitmq.return_value = HealthCheckResult("rabbitmq", "healthy")
                                mock_disk.return_value = HealthCheckResult("disk_space", "healthy")
                                mock_memory.return_value = HealthCheckResult("memory", "healthy")
                                
                                # Run all checks
                                result = await health_checker.run_all_checks()
                                
                                assert result["status"] == "unhealthy"  # Overall status should be unhealthy
                                assert result["summary"]["healthy"] == 4
                                assert result["summary"]["degraded"] == 1
                                assert result["summary"]["unhealthy"] == 1
    
    @pytest.mark.asyncio
    async def test_run_all_checks_exception_handling(self, health_checker):
        """Test running all health checks with exceptions."""
        # Mock one check to raise an exception
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                # Mock exception in one check
                                mock_db.side_effect = Exception("Database check failed")
                                mock_twilio.return_value = HealthCheckResult("twilio", "healthy")
                                mock_cache.return_value = HealthCheckResult("cache", "healthy")
                                mock_rabbitmq.return_value = HealthCheckResult("rabbitmq", "healthy")
                                mock_disk.return_value = HealthCheckResult("disk_space", "healthy")
                                mock_memory.return_value = HealthCheckResult("memory", "healthy")
                                
                                # Run all checks
                                result = await health_checker.run_all_checks()
                                
                                assert result["status"] == "unhealthy"
                                assert len(result["checks"]) == 6  # Should still have 6 entries
                                # One check should be marked as unhealthy due to exception
                                unhealthy_checks = [c for c in result["checks"] if c["status"] == "unhealthy"]
                                assert len(unhealthy_checks) >= 1
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_session')
    async def test_get_readiness_check_ready(self, mock_get_session, health_checker):
        """Test readiness check when ready."""
        # Mock successful database connection
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = 1
        mock_get_session.return_value = iter([mock_session])
        
        # Run readiness check
        result = await health_checker.get_readiness_check()
        
        assert result["status"] == "ready"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    @patch('app.monitoring.health_checks.get_session')
    async def test_get_readiness_check_not_ready(self, mock_get_session, health_checker):
        """Test readiness check when not ready."""
        # Mock database connection failure
        mock_get_session.side_effect = Exception("Database not available")
        
        # Run readiness check
        result = await health_checker.get_readiness_check()
        
        assert result["status"] == "not_ready"
        assert "error" in result
        assert "Database not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_liveness_check(self, health_checker):
        """Test liveness check."""
        # Run liveness check
        result = await health_checker.get_liveness_check()
        
        assert result["status"] == "alive"
        assert "timestamp" in result
        assert "uptime_seconds" in result
        assert isinstance(result["uptime_seconds"], (int, float))


class TestHealthCheckerSingleton:
    """Test health checker singleton behavior."""
    
    def test_get_health_checker_singleton(self):
        """Test that get_health_checker returns the same instance."""
        checker1 = get_health_checker()
        checker2 = get_health_checker()
        
        assert checker1 is checker2
        assert isinstance(checker1, HealthChecker)


class TestHealthCheckIntegration:
    """Test health check integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_health_check_performance(self):
        """Test health check performance."""
        health_checker = HealthChecker()
        
        # Mock all dependencies to respond quickly
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                # Mock quick responses
                                mock_db.return_value = HealthCheckResult("database", "healthy")
                                mock_twilio.return_value = HealthCheckResult("twilio", "healthy")
                                mock_cache.return_value = HealthCheckResult("cache", "healthy")
                                mock_rabbitmq.return_value = HealthCheckResult("rabbitmq", "healthy")
                                mock_disk.return_value = HealthCheckResult("disk_space", "healthy")
                                mock_memory.return_value = HealthCheckResult("memory", "healthy")
                                
                                # Measure time
                                start_time = time.time()
                                result = await health_checker.run_all_checks()
                                end_time = time.time()
                                
                                # Should complete quickly (less than 1 second)
                                assert (end_time - start_time) < 1.0
                                assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_concurrent_execution(self):
        """Test concurrent health check execution."""
        health_checker = HealthChecker()
        
        # Mock all checks
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                # Mock async responses with delays
                                async def delayed_response(name, status):
                                    await asyncio.sleep(0.1)  # Small delay
                                    return HealthCheckResult(name, status)
                                
                                mock_db.side_effect = lambda: delayed_response("database", "healthy")
                                mock_twilio.side_effect = lambda: delayed_response("twilio", "healthy")
                                mock_cache.side_effect = lambda: delayed_response("cache", "healthy")
                                mock_rabbitmq.side_effect = lambda: delayed_response("rabbitmq", "healthy")
                                mock_disk.side_effect = lambda: delayed_response("disk_space", "healthy")
                                mock_memory.side_effect = lambda: delayed_response("memory", "healthy")
                                
                                # Run multiple concurrent health checks
                                tasks = [health_checker.run_all_checks() for _ in range(3)]
                                results = await asyncio.gather(*tasks)
                                
                                # All should succeed
                                assert len(results) == 3
                                for result in results:
                                    assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self):
        """Test health check timeout handling."""
        health_checker = HealthChecker()
        
        # Mock a check that takes too long
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                
                async def slow_check():
                    await asyncio.sleep(5)  # Very slow
                    return HealthCheckResult("database", "healthy")
                
                mock_db.side_effect = slow_check
                mock_twilio.return_value = HealthCheckResult("twilio", "healthy")
                
                # Run with timeout
                try:
                    result = await asyncio.wait_for(
                        health_checker.run_all_checks(),
                        timeout=2.0
                    )
                    # Should not reach here due to timeout
                    assert False, "Expected timeout"
                except asyncio.TimeoutError:
                    # Expected timeout
                    pass
    
    def test_health_check_result_serialization(self):
        """Test health check result serialization."""
        result = HealthCheckResult(
            name="test_check",
            status="healthy",
            message="All good",
            details={"response_time": 123.45, "count": 10}
        )
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Should be JSON serializable
        import json
        json_str = json.dumps(result_dict)
        
        # Should be able to deserialize
        deserialized = json.loads(json_str)
        
        assert deserialized["name"] == "test_check"
        assert deserialized["status"] == "healthy"
        assert deserialized["details"]["response_time"] == 123.45
    
    @pytest.mark.asyncio
    async def test_health_check_memory_usage(self):
        """Test health check memory usage."""
        health_checker = HealthChecker()
        
        # Mock all checks to return large details
        large_details = {"data": "x" * 1000}  # 1KB of data per check
        
        with patch.object(health_checker, 'check_database_health') as mock_db:
            with patch.object(health_checker, 'check_twilio_health') as mock_twilio:
                with patch.object(health_checker, 'check_cache_health') as mock_cache:
                    with patch.object(health_checker, 'check_rabbitmq_health') as mock_rabbitmq:
                        with patch.object(health_checker, 'check_disk_space') as mock_disk:
                            with patch.object(health_checker, 'check_memory_usage') as mock_memory:
                                
                                mock_db.return_value = HealthCheckResult("database", "healthy", details=large_details)
                                mock_twilio.return_value = HealthCheckResult("twilio", "healthy", details=large_details)
                                mock_cache.return_value = HealthCheckResult("cache", "healthy", details=large_details)
                                mock_rabbitmq.return_value = HealthCheckResult("rabbitmq", "healthy", details=large_details)
                                mock_disk.return_value = HealthCheckResult("disk_space", "healthy", details=large_details)
                                mock_memory.return_value = HealthCheckResult("memory", "healthy", details=large_details)
                                
                                # Run health check
                                result = await health_checker.run_all_checks()
                                
                                # Should handle large data without issues
                                assert result["status"] == "healthy"
                                assert len(result["checks"]) == 6
                                
                                # Each check should have the large details
                                for check in result["checks"]:
                                    assert len(check["details"]["data"]) == 1000
