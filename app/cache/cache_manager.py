"""Caching layer for improved performance."""
import json
import time
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class CacheManager:
    """In-memory cache manager with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        self._cleanup_expired()
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            del self._cache[key]
            return None
        
        entry['last_accessed'] = time.time()
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'ttl': ttl
        }
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired()
        
        total_entries = len(self._cache)
        total_size = sum(len(str(entry['value'])) for entry in self._cache.values())
        
        return {
            'total_entries': total_entries,
            'estimated_size_bytes': total_size,
            'default_ttl': self.default_ttl,
            'oldest_entry': min(
                (entry['created_at'] for entry in self._cache.values()),
                default=None
            ),
            'most_recent_access': max(
                (entry['last_accessed'] for entry in self._cache.values()),
                default=None
            )
        }
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        
        # Only cleanup every 60 seconds to avoid overhead
        if current_time - self._last_cleanup < 60:
            return
        
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        self._last_cleanup = current_time


class ContactCache:
    """Specialized cache for contact data."""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize with cache manager."""
        self.cache = cache_manager
        self.prefix = "contact:"
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact from cache."""
        return self.cache.get(f"{self.prefix}{contact_id}")
    
    def set_contact(self, contact_id: str, contact_data: Dict[str, Any], ttl: int = 300) -> None:
        """Cache contact data."""
        self.cache.set(f"{self.prefix}{contact_id}", contact_data, ttl)
    
    def get_contacts_by_group(self, group_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get contacts by group from cache."""
        return self.cache.get(f"{self.prefix}group:{group_id}")
    
    def set_contacts_by_group(self, group_id: str, contacts: List[Dict[str, Any]], ttl: int = 300) -> None:
        """Cache contacts by group."""
        self.cache.set(f"{self.prefix}group:{group_id}", contacts, ttl)
    
    def invalidate_contact(self, contact_id: str) -> None:
        """Remove contact from cache."""
        self.cache.delete(f"{self.prefix}{contact_id}")
    
    def invalidate_group(self, group_id: str) -> None:
        """Remove group contacts from cache."""
        self.cache.delete(f"{self.prefix}group:{group_id}")


class MessageCache:
    """Specialized cache for message data."""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize with cache manager."""
        self.cache = cache_manager
        self.prefix = "message:"
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message from cache."""
        return self.cache.get(f"{self.prefix}{message_id}")
    
    def set_message(self, message_id: str, message_data: Dict[str, Any], ttl: int = 600) -> None:
        """Cache message data (longer TTL since messages change less frequently)."""
        self.cache.set(f"{self.prefix}{message_id}", message_data, ttl)
    
    def get_message_templates(self) -> Optional[List[Dict[str, Any]]]:
        """Get message templates from cache."""
        return self.cache.get(f"{self.prefix}templates")
    
    def set_message_templates(self, templates: List[Dict[str, Any]], ttl: int = 900) -> None:
        """Cache message templates."""
        self.cache.set(f"{self.prefix}templates", templates, ttl)
    
    def invalidate_message(self, message_id: str) -> None:
        """Remove message from cache."""
        self.cache.delete(f"{self.prefix}{message_id}")
    
    def invalidate_templates(self) -> None:
        """Remove templates from cache."""
        self.cache.delete(f"{self.prefix}templates")


class TTSCache:
    """Specialized cache for TTS audio files."""
    
    def __init__(self, cache_manager: CacheManager):
        """Initialize with cache manager."""
        self.cache = cache_manager
        self.prefix = "tts:"
    
    def get_audio_path(self, text_hash: str) -> Optional[str]:
        """Get cached audio file path."""
        return self.cache.get(f"{self.prefix}{text_hash}")
    
    def set_audio_path(self, text_hash: str, file_path: str, ttl: int = 3600) -> None:
        """Cache audio file path (1 hour TTL)."""
        self.cache.set(f"{self.prefix}{text_hash}", file_path, ttl)
    
    def invalidate_audio(self, text_hash: str) -> None:
        """Remove audio from cache."""
        self.cache.delete(f"{self.prefix}{text_hash}")


def cache_result(ttl: int = 300, key_func: Optional[callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Function to generate cache key from args/kwargs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = global_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        
        return wrapper
    return decorator


def cache_async_result(ttl: int = 300, key_func: Optional[callable] = None):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Function to generate cache key from args/kwargs
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = global_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        
        return wrapper
    return decorator


# Global cache instances
global_cache = CacheManager(default_ttl=300)  # 5 minutes default
contact_cache = ContactCache(global_cache)
message_cache = MessageCache(global_cache)
tts_cache = TTSCache(global_cache)


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return global_cache


def get_contact_cache() -> ContactCache:
    """Get the contact cache instance."""
    return contact_cache


def get_message_cache() -> MessageCache:
    """Get the message cache instance."""
    return message_cache


def get_tts_cache() -> TTSCache:
    """Get the TTS cache instance."""
    return tts_cache
