"""Dependency injection container for external services and dependencies."""
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from twilio.rest import Client
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session

logger = logging.getLogger(__name__)


class DIContainer:
    """Dependency injection container for managing external service dependencies."""
    
    def __init__(self):
        """Initialize the container with settings."""
        self.settings = get_settings()
        self._twilio_client: Optional[Client] = None
        self._cache: Dict[str, Any] = {}
    
    @property
    def twilio_client(self) -> Client:
        """
        Get Twilio client instance (singleton pattern).
        
        Returns:
            Configured Twilio client
        """
        if self._twilio_client is None:
            if not self.settings.TWILIO_ACCOUNT_SID or not self.settings.TWILIO_AUTH_TOKEN:
                raise ValueError("Twilio credentials not configured in settings")
            
            self._twilio_client = Client(
                self.settings.TWILIO_ACCOUNT_SID,
                self.settings.TWILIO_AUTH_TOKEN
            )
            logger.info("Twilio client initialized")
        
        return self._twilio_client
    
    def get_database_session(self) -> Session:
        """
        Get database session.
        
        Returns:
            Database session
        """
        return next(get_session())
    
    def get_settings(self):
        """
        Get application settings.
        
        Returns:
            Application settings
        """
        return self.settings
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        return self._cache.get(key)
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (not implemented in this simple cache)
        """
        self._cache[key] = value
    
    def cache_clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def reset_twilio_client(self) -> None:
        """Reset Twilio client (useful for testing or credential changes)."""
        self._twilio_client = None
        logger.info("Twilio client reset")


# Global container instance
_container: Optional[DIContainer] = None


@lru_cache(maxsize=1)
def get_container() -> DIContainer:
    """
    Get the global dependency injection container.
    
    Returns:
        DIContainer instance
    """
    global _container
    if _container is None:
        _container = DIContainer()
        logger.info("Dependency injection container initialized")
    return _container


def get_twilio_client() -> Client:
    """
    FastAPI dependency for getting Twilio client.
    
    Returns:
        Twilio client instance
    """
    return get_container().twilio_client


def get_cached_value(key: str) -> Optional[Any]:
    """
    FastAPI dependency for getting cached values.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    return get_container().cache_get(key)


# FastAPI dependencies
def get_di_container() -> DIContainer:
    """FastAPI dependency for the DI container."""
    return get_container()
