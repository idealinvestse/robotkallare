"""Unit tests for CacheManager and caching functionality."""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.cache.cache_manager import (
    CacheManager,
    ContactCache,
    MessageCache,
    TTSCache,
    cache_result,
    async_cache_result,
    get_cache_manager
)


class TestCacheManager:
    """Test cases for CacheManager."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a fresh CacheManager instance for testing."""
        return CacheManager()
    
    def test_cache_manager_init(self, cache_manager):
        """Test CacheManager initialization."""
        assert cache_manager.cache == {}
        assert cache_manager.ttl_data == {}
        assert cache_manager.default_ttl == 300
    
    def test_set_and_get_basic(self, cache_manager):
        """Test basic set and get operations."""
        # Set a value
        cache_manager.set("test_key", "test_value", ttl=60)
        
        # Get the value
        result = cache_manager.get("test_key")
        assert result == "test_value"
    
    def test_get_nonexistent_key(self, cache_manager):
        """Test getting a non-existent key."""
        result = cache_manager.get("nonexistent_key")
        assert result is None
    
    def test_get_with_default(self, cache_manager):
        """Test getting with default value."""
        result = cache_manager.get("nonexistent_key", default="default_value")
        assert result == "default_value"
    
    def test_ttl_expiration(self, cache_manager):
        """Test TTL expiration."""
        # Set a value with very short TTL
        cache_manager.set("short_ttl_key", "value", ttl=0.1)
        
        # Should be available immediately
        assert cache_manager.get("short_ttl_key") == "value"
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired now
        assert cache_manager.get("short_ttl_key") is None
    
    def test_delete_key(self, cache_manager):
        """Test deleting a key."""
        # Set a value
        cache_manager.set("delete_me", "value")
        assert cache_manager.get("delete_me") == "value"
        
        # Delete it
        result = cache_manager.delete("delete_me")
        assert result is True
        assert cache_manager.get("delete_me") is None
    
    def test_delete_nonexistent_key(self, cache_manager):
        """Test deleting a non-existent key."""
        result = cache_manager.delete("nonexistent_key")
        assert result is False
    
    def test_clear_cache(self, cache_manager):
        """Test clearing the entire cache."""
        # Set multiple values
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        
        # Clear cache
        cache_manager.clear()
        
        # All values should be gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert len(cache_manager.cache) == 0
    
    def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        # Set some values
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2", ttl=60)
        
        stats = cache_manager.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["entries_with_ttl"] == 1
        assert "memory_usage_bytes" in stats
    
    def test_cleanup_expired(self, cache_manager):
        """Test cleanup of expired entries."""
        # Set values with different TTLs
        cache_manager.set("persistent", "value")  # No TTL
        cache_manager.set("short_lived", "value", ttl=0.1)
        cache_manager.set("medium_lived", "value", ttl=10)
        
        # Wait for short-lived to expire
        time.sleep(0.2)
        
        # Cleanup expired entries
        removed_count = cache_manager.cleanup_expired()
        
        assert removed_count == 1
        assert cache_manager.get("persistent") == "value"
        assert cache_manager.get("short_lived") is None
        assert cache_manager.get("medium_lived") == "value"
    
    def test_has_key(self, cache_manager):
        """Test checking if key exists."""
        cache_manager.set("existing_key", "value")
        
        assert cache_manager.has("existing_key") is True
        assert cache_manager.has("nonexistent_key") is False
    
    def test_update_ttl(self, cache_manager):
        """Test updating TTL of existing key."""
        cache_manager.set("test_key", "value", ttl=1)
        
        # Update TTL
        result = cache_manager.update_ttl("test_key", 10)
        assert result is True
        
        # Key should still exist after original TTL would have expired
        time.sleep(1.1)
        assert cache_manager.get("test_key") == "value"
    
    def test_update_ttl_nonexistent_key(self, cache_manager):
        """Test updating TTL of non-existent key."""
        result = cache_manager.update_ttl("nonexistent_key", 10)
        assert result is False
    
    def test_get_keys_by_pattern(self, cache_manager):
        """Test getting keys by pattern."""
        # Set keys with different patterns
        cache_manager.set("user:123", "user_data")
        cache_manager.set("user:456", "user_data")
        cache_manager.set("session:abc", "session_data")
        
        # Get keys matching pattern
        user_keys = cache_manager.get_keys_by_pattern("user:*")
        assert len(user_keys) == 2
        assert "user:123" in user_keys
        assert "user:456" in user_keys
        assert "session:abc" not in user_keys


class TestContactCache:
    """Test cases for ContactCache."""
    
    @pytest.fixture
    def contact_cache(self):
        """Create ContactCache instance."""
        return ContactCache()
    
    def test_cache_contact(self, contact_cache):
        """Test caching a contact."""
        contact_data = {
            "id": "123",
            "name": "John Doe",
            "phone": "+46701234567"
        }
        
        contact_cache.cache_contact("123", contact_data)
        
        result = contact_cache.get_contact("123")
        assert result == contact_data
    
    def test_cache_contacts_by_group(self, contact_cache):
        """Test caching contacts by group."""
        contacts = [
            {"id": "1", "name": "John"},
            {"id": "2", "name": "Jane"}
        ]
        
        contact_cache.cache_contacts_by_group("group_123", contacts)
        
        result = contact_cache.get_contacts_by_group("group_123")
        assert result == contacts
    
    def test_invalidate_contact(self, contact_cache):
        """Test invalidating a contact."""
        contact_data = {"id": "123", "name": "John Doe"}
        contact_cache.cache_contact("123", contact_data)
        
        # Invalidate
        contact_cache.invalidate_contact("123")
        
        # Should be gone
        result = contact_cache.get_contact("123")
        assert result is None
    
    def test_invalidate_group_contacts(self, contact_cache):
        """Test invalidating group contacts."""
        contacts = [{"id": "1", "name": "John"}]
        contact_cache.cache_contacts_by_group("group_123", contacts)
        
        # Invalidate
        contact_cache.invalidate_group_contacts("group_123")
        
        # Should be gone
        result = contact_cache.get_contacts_by_group("group_123")
        assert result is None


class TestMessageCache:
    """Test cases for MessageCache."""
    
    @pytest.fixture
    def message_cache(self):
        """Create MessageCache instance."""
        return MessageCache()
    
    def test_cache_message(self, message_cache):
        """Test caching a message."""
        message_data = {
            "id": "msg_123",
            "content": "Hello world",
            "type": "sms"
        }
        
        message_cache.cache_message("msg_123", message_data)
        
        result = message_cache.get_message("msg_123")
        assert result == message_data
    
    def test_cache_message_history(self, message_cache):
        """Test caching message history."""
        history = [
            {"id": "1", "content": "Message 1"},
            {"id": "2", "content": "Message 2"}
        ]
        
        message_cache.cache_message_history("contact_123", history)
        
        result = message_cache.get_message_history("contact_123")
        assert result == history
    
    def test_invalidate_message(self, message_cache):
        """Test invalidating a message."""
        message_data = {"id": "msg_123", "content": "Hello"}
        message_cache.cache_message("msg_123", message_data)
        
        # Invalidate
        message_cache.invalidate_message("msg_123")
        
        # Should be gone
        result = message_cache.get_message("msg_123")
        assert result is None


class TestTTSCache:
    """Test cases for TTSCache."""
    
    @pytest.fixture
    def tts_cache(self):
        """Create TTSCache instance."""
        return TTSCache()
    
    def test_cache_audio_file(self, tts_cache):
        """Test caching audio file."""
        audio_data = b"fake_audio_data"
        
        tts_cache.cache_audio_file("hello_world", audio_data)
        
        result = tts_cache.get_audio_file("hello_world")
        assert result == audio_data
    
    def test_cache_tts_metadata(self, tts_cache):
        """Test caching TTS metadata."""
        metadata = {
            "text": "Hello world",
            "voice": "sv-SE-Standard-A",
            "duration": 2.5
        }
        
        tts_cache.cache_tts_metadata("hello_world", metadata)
        
        result = tts_cache.get_tts_metadata("hello_world")
        assert result == metadata
    
    def test_invalidate_tts_cache(self, tts_cache):
        """Test invalidating TTS cache."""
        audio_data = b"fake_audio_data"
        metadata = {"text": "Hello", "voice": "sv-SE"}
        
        tts_cache.cache_audio_file("hello", audio_data)
        tts_cache.cache_tts_metadata("hello", metadata)
        
        # Invalidate
        tts_cache.invalidate_tts_cache("hello")
        
        # Both should be gone
        assert tts_cache.get_audio_file("hello") is None
        assert tts_cache.get_tts_metadata("hello") is None


class TestCacheDecorators:
    """Test cache decorators."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager for decorator tests."""
        return CacheManager()
    
    def test_cache_result_decorator(self, cache_manager):
        """Test cache_result decorator."""
        call_count = 0
        
        @cache_result(cache_manager, ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
        
        # Different arguments should execute function again
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_cache_result_decorator(self, cache_manager):
        """Test async_cache_result decorator."""
        call_count = 0
        
        @async_cache_result(cache_manager, ttl=60)
        async def expensive_async_function(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate async work
            return x * y
        
        # First call should execute function
        result1 = await expensive_async_function(2, 3)
        assert result1 == 6
        assert call_count == 1
        
        # Second call should use cache
        result2 = await expensive_async_function(2, 3)
        assert result2 == 6
        assert call_count == 1  # Should not increment
    
    def test_cache_result_with_custom_key(self, cache_manager):
        """Test cache_result decorator with custom key function."""
        call_count = 0
        
        def custom_key_func(*args, **kwargs):
            return f"custom:{args[0]}"
        
        @cache_result(cache_manager, key_func=custom_key_func, ttl=60)
        def function_with_custom_key(user_id, data):
            nonlocal call_count
            call_count += 1
            return f"result_for_{user_id}"
        
        # First call
        result1 = function_with_custom_key("123", {"some": "data"})
        assert result1 == "result_for_123"
        assert call_count == 1
        
        # Second call with different data but same user_id should use cache
        result2 = function_with_custom_key("123", {"different": "data"})
        assert result2 == "result_for_123"
        assert call_count == 1  # Should not increment
    
    def test_cache_result_exception_handling(self, cache_manager):
        """Test cache_result decorator with exceptions."""
        call_count = 0
        
        @cache_result(cache_manager, ttl=60)
        def function_that_raises(should_raise):
            nonlocal call_count
            call_count += 1
            if should_raise:
                raise ValueError("Test exception")
            return "success"
        
        # Successful call should be cached
        result = function_that_raises(False)
        assert result == "success"
        assert call_count == 1
        
        # Second successful call should use cache
        result = function_that_raises(False)
        assert result == "success"
        assert call_count == 1
        
        # Exception should not be cached
        with pytest.raises(ValueError):
            function_that_raises(True)
        assert call_count == 2
        
        # Another exception call should execute again
        with pytest.raises(ValueError):
            function_that_raises(True)
        assert call_count == 3


class TestCacheIntegration:
    """Test cache integration scenarios."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create cache manager for integration tests."""
        return CacheManager()
    
    def test_multiple_cache_types(self, cache_manager):
        """Test using multiple cache types together."""
        contact_cache = ContactCache(cache_manager)
        message_cache = MessageCache(cache_manager)
        
        # Cache different types of data
        contact_cache.cache_contact("123", {"name": "John"})
        message_cache.cache_message("msg_1", {"content": "Hello"})
        
        # Both should be retrievable
        assert contact_cache.get_contact("123")["name"] == "John"
        assert message_cache.get_message("msg_1")["content"] == "Hello"
        
        # Stats should reflect both entries
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 2
    
    def test_cache_memory_management(self, cache_manager):
        """Test cache memory management."""
        # Fill cache with data
        for i in range(100):
            cache_manager.set(f"key_{i}", f"value_{i}" * 100)  # Larger values
        
        stats_before = cache_manager.get_stats()
        assert stats_before["total_entries"] == 100
        
        # Clear cache
        cache_manager.clear()
        
        stats_after = cache_manager.get_stats()
        assert stats_after["total_entries"] == 0
        assert stats_after["memory_usage_bytes"] < stats_before["memory_usage_bytes"]
    
    def test_concurrent_cache_access(self, cache_manager):
        """Test concurrent cache access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def cache_worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_item_{i}"
                    value = f"data_{worker_id}_{i}"
                    
                    # Set value
                    cache_manager.set(key, value)
                    
                    # Get value
                    retrieved = cache_manager.get(key)
                    results.append((key, retrieved == value))
                    
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 workers * 10 items each
        assert all(success for _, success in results)
    
    @pytest.mark.asyncio
    async def test_async_cache_integration(self, cache_manager):
        """Test async cache integration."""
        @async_cache_result(cache_manager, ttl=60)
        async def fetch_user_data(user_id):
            # Simulate async database call
            await asyncio.sleep(0.01)
            return {"id": user_id, "name": f"User {user_id}"}
        
        @async_cache_result(cache_manager, ttl=60)
        async def fetch_user_messages(user_id):
            # Simulate async API call
            await asyncio.sleep(0.01)
            return [f"Message {i} for user {user_id}" for i in range(3)]
        
        # Fetch data concurrently
        user_data_task = fetch_user_data("123")
        messages_task = fetch_user_messages("123")
        
        user_data, messages = await asyncio.gather(user_data_task, messages_task)
        
        assert user_data["id"] == "123"
        assert len(messages) == 3
        
        # Second call should use cache (faster)
        start_time = time.time()
        user_data2 = await fetch_user_data("123")
        end_time = time.time()
        
        assert user_data2 == user_data
        assert (end_time - start_time) < 0.005  # Should be much faster


class TestCacheManagerSingleton:
    """Test cache manager singleton behavior."""
    
    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns the same instance."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        assert manager1 is manager2
        
        # Set value in one, should be available in the other
        manager1.set("test_key", "test_value")
        assert manager2.get("test_key") == "test_value"
    
    def test_cache_manager_persistence(self):
        """Test cache manager persistence across calls."""
        manager = get_cache_manager()
        manager.set("persistent_key", "persistent_value")
        
        # Get manager again
        manager2 = get_cache_manager()
        assert manager2.get("persistent_key") == "persistent_value"
