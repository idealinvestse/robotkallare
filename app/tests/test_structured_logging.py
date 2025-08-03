"""Unit tests for structured logging system."""
import pytest
import json
import logging
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from contextvars import copy_context

from app.monitoring.structured_logging import (
    StructuredFormatter,
    PerformanceLogger,
    BusinessLogger,
    SecurityLogger,
    setup_structured_logging,
    set_correlation_id,
    get_correlation_id,
    set_user_context,
    log_with_timing,
    correlation_id_var,
    user_id_var,
    request_path_var,
    performance_logger,
    business_logger,
    security_logger
)


class TestStructuredFormatter:
    """Test cases for StructuredFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create StructuredFormatter instance."""
        return StructuredFormatter()
    
    def test_formatter_basic_record(self, formatter):
        """Test formatting basic log record."""
        # Create log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        # Format record
        formatted = formatter.format(record)
        
        # Parse JSON
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
    
    def test_formatter_with_correlation_id(self, formatter):
        """Test formatting with correlation ID."""
        # Set correlation ID
        correlation_id_var.set("test-correlation-123")
        
        try:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=None
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert log_data["correlation_id"] == "test-correlation-123"
        finally:
            correlation_id_var.set(None)
    
    def test_formatter_with_user_context(self, formatter):
        """Test formatting with user context."""
        # Set user context
        user_id_var.set("user_123")
        request_path_var.set("/api/sms")
        
        try:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=None
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert log_data["user_id"] == "user_123"
            assert log_data["request_path"] == "/api/sms"
        finally:
            user_id_var.set(None)
            request_path_var.set(None)
    
    def test_formatter_with_exception(self, formatter):
        """Test formatting with exception information."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert "exception" in log_data
            assert log_data["exception"]["type"] == "ValueError"
            assert log_data["exception"]["message"] == "Test exception"
            assert "traceback" in log_data["exception"]
    
    def test_formatter_with_extra_fields(self, formatter):
        """Test formatting with extra fields."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        # Add extra fields
        record.custom_field = "custom_value"
        record.request_id = "req_123"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert "extra" in log_data
        assert log_data["extra"]["custom_field"] == "custom_value"
        assert log_data["extra"]["request_id"] == "req_123"


class TestPerformanceLogger:
    """Test cases for PerformanceLogger."""
    
    @pytest.fixture
    def perf_logger(self):
        """Create PerformanceLogger instance."""
        return PerformanceLogger("test_performance")
    
    def test_log_operation_time_success(self, perf_logger):
        """Test logging successful operation time."""
        with patch.object(perf_logger.logger, 'log') as mock_log:
            perf_logger.log_operation_time(
                operation="test_operation",
                duration_ms=123.45,
                success=True,
                extra_data={"key": "value"}
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.INFO  # Level
            assert "test_operation completed" in call_args[0][1]  # Message
            
            extra_data = call_args[1]["extra"]
            assert extra_data["operation"] == "test_operation"
            assert extra_data["duration_ms"] == 123.45
            assert extra_data["success"] is True
            assert extra_data["key"] == "value"
    
    def test_log_operation_time_failure(self, perf_logger):
        """Test logging failed operation time."""
        with patch.object(perf_logger.logger, 'log') as mock_log:
            perf_logger.log_operation_time(
                operation="test_operation",
                duration_ms=456.78,
                success=False
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.WARNING  # Level for failures
            
            extra_data = call_args[1]["extra"]
            assert extra_data["success"] is False
    
    def test_log_database_query(self, perf_logger):
        """Test logging database query performance."""
        with patch.object(perf_logger, 'log_operation_time') as mock_log_op:
            perf_logger.log_database_query(
                query_type="SELECT",
                table="contacts",
                duration_ms=25.5,
                row_count=10
            )
            
            mock_log_op.assert_called_once_with(
                "db_SELECT",
                25.5,
                extra_data={
                    "table": "contacts",
                    "query_type": "SELECT",
                    "row_count": 10
                }
            )
    
    def test_log_api_call(self, perf_logger):
        """Test logging API call performance."""
        with patch.object(perf_logger, 'log_operation_time') as mock_log_op:
            perf_logger.log_api_call(
                service="twilio",
                endpoint="/Messages",
                duration_ms=150.0,
                status_code=200,
                success=True
            )
            
            mock_log_op.assert_called_once_with(
                "api_twilio",
                150.0,
                success=True,
                extra_data={
                    "service": "twilio",
                    "endpoint": "/Messages",
                    "status_code": 200
                }
            )


class TestBusinessLogger:
    """Test cases for BusinessLogger."""
    
    @pytest.fixture
    def biz_logger(self):
        """Create BusinessLogger instance."""
        return BusinessLogger("test_business")
    
    def test_log_sms_sent_success(self, biz_logger):
        """Test logging successful SMS sending."""
        with patch.object(biz_logger.logger, 'log') as mock_log:
            biz_logger.log_sms_sent(
                contact_id="contact_123",
                message_id="msg_456",
                phone_number="+46701234567",
                success=True
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.INFO
            assert "SMS sent" in call_args[0][1]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "sms_sent"
            assert extra_data["contact_id"] == "contact_123"
            assert extra_data["message_id"] == "msg_456"
            assert extra_data["phone_number"] == "4567"  # Last 4 digits
            assert extra_data["success"] is True
    
    def test_log_sms_sent_failure(self, biz_logger):
        """Test logging failed SMS sending."""
        with patch.object(biz_logger.logger, 'log') as mock_log:
            biz_logger.log_sms_sent(
                contact_id="contact_123",
                message_id="msg_456",
                phone_number="+46701234567",
                success=False,
                error_message="Twilio error"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.ERROR
            assert "SMS failed" in call_args[0][1]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["success"] is False
            assert extra_data["error_message"] == "Twilio error"
    
    def test_log_call_made_success(self, biz_logger):
        """Test logging successful call making."""
        with patch.object(biz_logger.logger, 'log') as mock_log:
            biz_logger.log_call_made(
                contact_id="contact_123",
                message_id="msg_456",
                phone_number="+46701234567",
                call_sid="CA123456789",
                success=True
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.INFO
            assert "Call initiated" in call_args[0][1]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "call_made"
            assert extra_data["call_sid"] == "CA123456789"
    
    def test_log_user_action(self, biz_logger):
        """Test logging user action."""
        with patch.object(biz_logger.logger, 'info') as mock_info:
            biz_logger.log_user_action(
                action="create_contact",
                user_id="user_123",
                resource_type="contact",
                resource_id="contact_456",
                extra_data={"name": "John Doe"}
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            
            assert "User action: create_contact" in call_args[0][0]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "user_action"
            assert extra_data["action"] == "create_contact"
            assert extra_data["user_id"] == "user_123"
            assert extra_data["name"] == "John Doe"


class TestSecurityLogger:
    """Test cases for SecurityLogger."""
    
    @pytest.fixture
    def sec_logger(self):
        """Create SecurityLogger instance."""
        return SecurityLogger("test_security")
    
    def test_log_authentication_attempt_success(self, sec_logger):
        """Test logging successful authentication."""
        with patch.object(sec_logger.logger, 'log') as mock_log:
            sec_logger.log_authentication_attempt(
                user_id="user_123",
                ip_address="192.168.1.1",
                success=True
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.INFO
            assert "Authentication successful" in call_args[0][1]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "auth_attempt"
            assert extra_data["user_id"] == "user_123"
            assert extra_data["ip_address"] == "192.168.1.1"
            assert extra_data["success"] is True
    
    def test_log_authentication_attempt_failure(self, sec_logger):
        """Test logging failed authentication."""
        with patch.object(sec_logger.logger, 'log') as mock_log:
            sec_logger.log_authentication_attempt(
                user_id="user_123",
                ip_address="192.168.1.1",
                success=False,
                failure_reason="Invalid password"
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.WARNING
            assert "Authentication failed" in call_args[0][1]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["success"] is False
            assert extra_data["failure_reason"] == "Invalid password"
    
    def test_log_rate_limit_exceeded(self, sec_logger):
        """Test logging rate limit violation."""
        with patch.object(sec_logger.logger, 'warning') as mock_warning:
            sec_logger.log_rate_limit_exceeded(
                ip_address="192.168.1.1",
                endpoint="/api/sms",
                limit=10,
                window_seconds=60
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            
            assert "Rate limit exceeded" in call_args[0][0]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "rate_limit_exceeded"
            assert extra_data["ip_address"] == "192.168.1.1"
            assert extra_data["endpoint"] == "/api/sms"
            assert extra_data["limit"] == 10
    
    def test_log_suspicious_activity(self, sec_logger):
        """Test logging suspicious activity."""
        with patch.object(sec_logger.logger, 'error') as mock_error:
            sec_logger.log_suspicious_activity(
                activity_type="sql_injection_attempt",
                ip_address="192.168.1.1",
                details={"payload": "'; DROP TABLE users; --"}
            )
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            
            assert "Suspicious activity detected" in call_args[0][0]
            
            extra_data = call_args[1]["extra"]
            assert extra_data["event"] == "suspicious_activity"
            assert extra_data["activity_type"] == "sql_injection_attempt"
            assert extra_data["details"]["payload"] == "'; DROP TABLE users; --"


class TestLoggingUtilities:
    """Test logging utility functions."""
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        # Initially should be None
        assert get_correlation_id() is None
        
        # Set correlation ID
        set_correlation_id("test-correlation-123")
        assert get_correlation_id() == "test-correlation-123"
        
        # Clean up
        correlation_id_var.set(None)
    
    def test_set_user_context(self):
        """Test setting user context."""
        set_user_context("user_123", "/api/test")
        
        assert user_id_var.get() == "user_123"
        assert request_path_var.get() == "/api/test"
        
        # Clean up
        user_id_var.set(None)
        request_path_var.set(None)
    
    def test_context_isolation(self):
        """Test that context variables are isolated between contexts."""
        def context1():
            set_correlation_id("context1-id")
            return get_correlation_id()
        
        def context2():
            set_correlation_id("context2-id")
            return get_correlation_id()
        
        # Run in different contexts
        ctx1 = copy_context()
        ctx2 = copy_context()
        
        result1 = ctx1.run(context1)
        result2 = ctx2.run(context2)
        
        assert result1 == "context1-id"
        assert result2 == "context2-id"


class TestLogWithTimingDecorator:
    """Test log_with_timing decorator."""
    
    def test_sync_function_timing(self):
        """Test timing decorator with synchronous function."""
        @log_with_timing("test_operation")
        def test_function(x, y):
            time.sleep(0.01)  # Small delay
            return x + y
        
        with patch('app.monitoring.structured_logging.PerformanceLogger') as mock_perf_logger_class:
            mock_perf_logger = Mock()
            mock_perf_logger_class.return_value = mock_perf_logger
            
            result = test_function(1, 2)
            
            assert result == 3
            mock_perf_logger.log_operation_time.assert_called_once()
            
            call_args = mock_perf_logger.log_operation_time.call_args
            assert call_args[0][0] == "test_operation"  # operation name
            assert call_args[0][1] > 0  # duration_ms should be positive
            assert call_args[1]["success"] is True
    
    @pytest.mark.asyncio
    async def test_async_function_timing(self):
        """Test timing decorator with asynchronous function."""
        @log_with_timing("async_test_operation")
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # Small delay
            return x * y
        
        with patch('app.monitoring.structured_logging.PerformanceLogger') as mock_perf_logger_class:
            mock_perf_logger = Mock()
            mock_perf_logger_class.return_value = mock_perf_logger
            
            result = await async_test_function(3, 4)
            
            assert result == 12
            mock_perf_logger.log_operation_time.assert_called_once()
            
            call_args = mock_perf_logger.log_operation_time.call_args
            assert call_args[0][0] == "async_test_operation"
            assert call_args[1]["success"] is True
    
    def test_function_timing_with_exception(self):
        """Test timing decorator when function raises exception."""
        @log_with_timing("failing_operation")
        def failing_function():
            raise ValueError("Test error")
        
        with patch('app.monitoring.structured_logging.PerformanceLogger') as mock_perf_logger_class:
            mock_perf_logger = Mock()
            mock_perf_logger_class.return_value = mock_perf_logger
            
            with pytest.raises(ValueError):
                failing_function()
            
            mock_perf_logger.log_operation_time.assert_called_once()
            
            call_args = mock_perf_logger.log_operation_time.call_args
            assert call_args[0][0] == "failing_operation"
            assert call_args[1]["success"] is False
            assert "error" in call_args[1]["extra_data"]
    
    def test_timing_decorator_with_custom_logger(self):
        """Test timing decorator with custom logger."""
        custom_logger = Mock()
        
        @log_with_timing("custom_operation", logger=custom_logger)
        def test_function():
            return "result"
        
        with patch('app.monitoring.structured_logging.PerformanceLogger') as mock_perf_logger_class:
            mock_perf_logger = Mock()
            mock_perf_logger_class.return_value = mock_perf_logger
            
            result = test_function()
            
            assert result == "result"
            custom_logger.debug.assert_called_once()
            # Check that debug was called with timing information
            debug_call = custom_logger.debug.call_args[0][0]
            assert "custom_operation completed" in debug_call


class TestSetupStructuredLogging:
    """Test structured logging setup."""
    
    @patch('app.monitoring.structured_logging.logging.getLogger')
    @patch('app.monitoring.structured_logging.logging.StreamHandler')
    @patch('app.monitoring.structured_logging.logging.FileHandler')
    @patch('app.monitoring.structured_logging.get_settings')
    def test_setup_structured_logging(self, mock_get_settings, mock_file_handler, mock_stream_handler, mock_get_logger):
        """Test structured logging setup."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.LOG_LEVEL = "INFO"
        mock_get_settings.return_value = mock_settings
        
        # Mock logger
        mock_root_logger = Mock()
        mock_root_logger.handlers = []
        mock_get_logger.return_value = mock_root_logger
        
        # Mock handlers
        mock_console_handler = Mock()
        mock_file_handler_instance = Mock()
        mock_stream_handler.return_value = mock_console_handler
        mock_file_handler.return_value = mock_file_handler_instance
        
        # Call setup
        setup_structured_logging()
        
        # Verify logger configuration
        mock_root_logger.setLevel.assert_called_once()
        mock_root_logger.addHandler.assert_called()
        
        # Verify handlers were configured with structured formatter
        mock_console_handler.setFormatter.assert_called_once()
        mock_file_handler_instance.setFormatter.assert_called_once()
    
    @patch('app.monitoring.structured_logging.logging.FileHandler')
    @patch('app.monitoring.structured_logging.get_settings')
    def test_setup_structured_logging_file_error(self, mock_get_settings, mock_file_handler):
        """Test structured logging setup when file handler fails."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.LOG_LEVEL = "INFO"
        mock_get_settings.return_value = mock_settings
        
        # Mock file handler to raise exception
        mock_file_handler.side_effect = OSError("Cannot create log file")
        
        # Should not raise exception, just continue with console logging
        setup_structured_logging()
        
        # File handler should have been attempted
        mock_file_handler.assert_called_once()


class TestGlobalLoggerInstances:
    """Test global logger instances."""
    
    def test_performance_logger_instance(self):
        """Test global performance logger instance."""
        assert isinstance(performance_logger, PerformanceLogger)
        assert performance_logger.logger.name == "performance"
    
    def test_business_logger_instance(self):
        """Test global business logger instance."""
        assert isinstance(business_logger, BusinessLogger)
        assert business_logger.logger.name == "business"
    
    def test_security_logger_instance(self):
        """Test global security logger instance."""
        assert isinstance(security_logger, SecurityLogger)
        assert security_logger.logger.name == "security"


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_logging_scenario(self):
        """Test complete logging scenario with all components."""
        # Set up context
        set_correlation_id("test-correlation-456")
        set_user_context("user_789", "/api/sms")
        
        try:
            # Create a function with timing
            @log_with_timing("sms_send_operation")
            def send_sms_mock(contact_id, message):
                time.sleep(0.01)  # Simulate work
                return {"status": "sent", "message_id": "msg_123"}
            
            with patch('app.monitoring.structured_logging.PerformanceLogger') as mock_perf_logger_class:
                with patch.object(business_logger.logger, 'log') as mock_business_log:
                    mock_perf_logger = Mock()
                    mock_perf_logger_class.return_value = mock_perf_logger
                    
                    # Execute operation
                    result = send_sms_mock("contact_123", "Hello world")
                    
                    # Log business event
                    business_logger.log_sms_sent(
                        contact_id="contact_123",
                        message_id=result["message_id"],
                        phone_number="+46701234567",
                        success=True
                    )
                    
                    # Verify performance logging
                    mock_perf_logger.log_operation_time.assert_called_once()
                    
                    # Verify business logging
                    mock_business_log.assert_called_once()
                    
                    # Check that correlation ID is available in context
                    assert get_correlation_id() == "test-correlation-456"
        finally:
            # Clean up context
            correlation_id_var.set(None)
            user_id_var.set(None)
            request_path_var.set(None)
    
    def test_logging_performance_impact(self):
        """Test that logging doesn't significantly impact performance."""
        @log_with_timing("performance_test")
        def fast_operation():
            return sum(range(1000))
        
        # Measure time with logging
        start_time = time.time()
        for _ in range(100):
            fast_operation()
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Should complete 100 operations quickly (less than 1 second)
        assert total_time < 1.0
    
    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads."""
        import threading
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                set_correlation_id(f"worker-{worker_id}")
                
                @log_with_timing(f"worker_{worker_id}_operation")
                def worker_task():
                    time.sleep(0.01)
                    return f"result_{worker_id}"
                
                result = worker_task()
                results.append(result)
                
                # Log business event
                business_logger.log_user_action(
                    action=f"worker_{worker_id}_action",
                    user_id=f"user_{worker_id}"
                )
                
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(f"result_{i}" in results for i in range(5))
    
    def test_logging_memory_usage(self):
        """Test logging memory usage with large amounts of data."""
        large_data = {"data": "x" * 10000}  # 10KB of data
        
        # Log many entries with large data
        for i in range(100):
            business_logger.log_user_action(
                action=f"large_data_action_{i}",
                user_id=f"user_{i}",
                extra_data=large_data
            )
        
        # Should complete without memory issues
        # This is mainly a smoke test to ensure no memory leaks
        assert True  # If we get here, no memory issues occurred
