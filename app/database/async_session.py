"""Async database session management for improved performance."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.config import get_settings

logger = logging.getLogger(__name__)

# Get settings with fallback for testing
try:
    settings = get_settings()
    database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./gdial.db')
except Exception as e:
    logging.warning(f"Settings loading failed: {e}. Using fallback database configuration.")
    database_url = 'sqlite:///./gdial.db'

# Create async engine
def create_async_database_engine():
    """Create async database engine with proper configuration."""
    global database_url
    
    # Convert SQLite URL to async format if needed
    if database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+aiomysql://")
    
    engine = create_async_engine(
        database_url,
        echo=settings.LOG_LEVEL == "DEBUG",
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_size=10,       # Connection pool size
        max_overflow=20     # Max overflow connections
    )
    
    logger.info(f"Async database engine created for: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    return engine


# Global async engine and session factory
async_engine = create_async_database_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_async_tables():
    """Create database tables asynchronously."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Async database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating async database tables: {str(e)}", exc_info=True)
        raise


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with proper cleanup.
    
    Usage:
        async with get_async_session() as session:
            # Use session here
            result = await session.exec(select(Model))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()


class AsyncDatabaseManager:
    """Manager for async database operations."""
    
    def __init__(self):
        """Initialize the async database manager."""
        self.engine = async_engine
        self.session_factory = AsyncSessionLocal
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            async with get_async_session() as session:
                # Simple query to test connectivity
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def get_connection_info(self) -> dict:
        """
        Get database connection information.
        
        Returns:
            Dictionary with connection details
        """
        try:
            async with get_async_session() as session:
                # Get database version and other info
                result = await session.execute("SELECT sqlite_version()")
                version = result.scalar()
                
                return {
                    "database_type": "SQLite",
                    "version": version,
                    "url": str(self.engine.url).split('@')[-1] if '@' in str(self.engine.url) else str(self.engine.url),
                    "pool_size": self.engine.pool.size(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "checked_in": self.engine.pool.checkedin()
                }
        except Exception as e:
            logger.error(f"Error getting connection info: {str(e)}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the async engine and all connections."""
        try:
            await self.engine.dispose()
            logger.info("Async database engine closed")
        except Exception as e:
            logger.error(f"Error closing async database engine: {str(e)}")


# Global async database manager instance
async_db_manager = AsyncDatabaseManager()


# FastAPI dependency for async sessions
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with get_async_session() as session:
        yield session
