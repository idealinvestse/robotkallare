"""Health check endpoints and monitoring utilities."""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from sqlmodel import Session, text
from fastapi import HTTPException

from app.config import get_settings
from app.database import get_session
from app.database.async_session import get_async_session, async_db_manager
from app.dependencies.container import get_container
from app.cache.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthCheckResult:
    """Result of a health check."""
    
    def __init__(self, name: str, status: str, message: str = "", details: Dict[str, Any] = None):
        self.name = name
        self.status = status  # "healthy", "unhealthy", "degraded"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class HealthChecker:
    """Comprehensive health checking system."""
    
    def __init__(self):
        """Initialize health checker."""
        self.container = get_container()
        self.cache_manager = get_cache_manager()
    
    async def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test sync database connection
            with next(get_session()) as session:
                result = session.exec(text("SELECT 1")).first()
                if result != 1:
                    return HealthCheckResult(
                        "database",
                        "unhealthy",
                        "Database query returned unexpected result"
                    )
            
            # Test async database connection
            async with get_async_session() as async_session:
                result = await async_session.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    return HealthCheckResult(
                        "database",
                        "unhealthy",
                        "Async database query returned unexpected result"
                    )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Get connection info
            conn_info = await async_db_manager.get_connection_info()
            
            status = "healthy"
            message = "Database is accessible"
            
            # Check response time
            if response_time > 1000:  # 1 second
                status = "degraded"
                message = f"Database response time is high: {response_time:.2f}ms"
            
            return HealthCheckResult(
                "database",
                status,
                message,
                {
                    "response_time_ms": round(response_time, 2),
                    "connection_info": conn_info
                }
            )
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "database",
                "unhealthy",
                f"Database connection failed: {str(e)}"
            )
    
    async def check_twilio_health(self) -> HealthCheckResult:
        """Check Twilio API connectivity."""
        try:
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                return HealthCheckResult(
                    "twilio",
                    "unhealthy",
                    "Twilio credentials not configured"
                )
            
            start_time = time.time()
            twilio_client = self.container.twilio_client
            
            # Test Twilio API by fetching account info
            account = twilio_client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            
            response_time = (time.time() - start_time) * 1000
            
            status = "healthy"
            message = "Twilio API is accessible"
            
            if response_time > 2000:  # 2 seconds
                status = "degraded"
                message = f"Twilio API response time is high: {response_time:.2f}ms"
            
            return HealthCheckResult(
                "twilio",
                status,
                message,
                {
                    "response_time_ms": round(response_time, 2),
                    "account_status": account.status,
                    "account_type": account.type
                }
            )
            
        except Exception as e:
            logger.error(f"Twilio health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "twilio",
                "unhealthy",
                f"Twilio API connection failed: {str(e)}"
            )
    
    async def check_cache_health(self) -> HealthCheckResult:
        """Check cache system health."""
        try:
            start_time = time.time()
            
            # Test cache operations
            test_key = "health_check_test"
            test_value = {"timestamp": time.time(), "test": True}
            
            # Set test value
            self.cache_manager.set(test_key, test_value, ttl=60)
            
            # Get test value
            retrieved_value = self.cache_manager.get(test_key)
            
            # Clean up
            self.cache_manager.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved_value != test_value:
                return HealthCheckResult(
                    "cache",
                    "unhealthy",
                    "Cache set/get operation failed"
                )
            
            # Get cache statistics
            cache_stats = self.cache_manager.get_stats()
            
            status = "healthy"
            message = "Cache system is working"
            
            if cache_stats["total_entries"] > 10000:
                status = "degraded"
                message = f"Cache has many entries: {cache_stats['total_entries']}"
            
            return HealthCheckResult(
                "cache",
                status,
                message,
                {
                    "response_time_ms": round(response_time, 2),
                    "stats": cache_stats
                }
            )
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "cache",
                "unhealthy",
                f"Cache system error: {str(e)}"
            )
    
    async def check_rabbitmq_health(self) -> HealthCheckResult:
        """Check RabbitMQ connectivity."""
        try:
            # This would check RabbitMQ connection
            # Implementation depends on your RabbitMQ setup
            from app.queue.rabbitmq import get_rabbitmq_connection
            
            start_time = time.time()
            connection = get_rabbitmq_connection()
            
            if connection and not connection.is_closed:
                response_time = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    "rabbitmq",
                    "healthy",
                    "RabbitMQ connection is active",
                    {
                        "response_time_ms": round(response_time, 2),
                        "connection_state": "open"
                    }
                )
            else:
                return HealthCheckResult(
                    "rabbitmq",
                    "unhealthy",
                    "RabbitMQ connection is closed or unavailable"
                )
                
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "rabbitmq",
                "degraded",
                f"RabbitMQ check failed: {str(e)}"
            )
    
    async def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            import shutil
            
            # Check disk space for the application directory
            total, used, free = shutil.disk_usage(".")
            
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            used_percent = (used / total) * 100
            
            status = "healthy"
            message = f"Disk space: {free_gb:.2f}GB free ({100-used_percent:.1f}% available)"
            
            if free_gb < 1:  # Less than 1GB free
                status = "unhealthy"
                message = f"Critical: Only {free_gb:.2f}GB disk space remaining"
            elif used_percent > 90:  # More than 90% used
                status = "degraded"
                message = f"Warning: Disk {used_percent:.1f}% full"
            
            return HealthCheckResult(
                "disk_space",
                status,
                message,
                {
                    "total_gb": round(total_gb, 2),
                    "used_gb": round((total - free) / (1024**3), 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 1)
                }
            )
            
        except Exception as e:
            logger.error(f"Disk space check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "disk_space",
                "unhealthy",
                f"Disk space check failed: {str(e)}"
            )
    
    async def check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage."""
        try:
            import psutil
            
            # Get memory information
            memory = psutil.virtual_memory()
            
            used_percent = memory.percent
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)
            
            status = "healthy"
            message = f"Memory usage: {used_percent:.1f}% ({available_gb:.2f}GB available)"
            
            if used_percent > 95:
                status = "unhealthy"
                message = f"Critical: Memory usage at {used_percent:.1f}%"
            elif used_percent > 85:
                status = "degraded"
                message = f"Warning: High memory usage at {used_percent:.1f}%"
            
            return HealthCheckResult(
                "memory",
                status,
                message,
                {
                    "total_gb": round(total_gb, 2),
                    "used_gb": round((memory.total - memory.available) / (1024**3), 2),
                    "available_gb": round(available_gb, 2),
                    "used_percent": round(used_percent, 1)
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                "memory",
                "degraded",
                "psutil not available for memory monitoring"
            )
        except Exception as e:
            logger.error(f"Memory check failed: {str(e)}", exc_info=True)
            return HealthCheckResult(
                "memory",
                "unhealthy",
                f"Memory check failed: {str(e)}"
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status."""
        checks = [
            self.check_database_health(),
            self.check_twilio_health(),
            self.check_cache_health(),
            self.check_rabbitmq_health(),
            self.check_disk_space(),
            self.check_memory_usage()
        ]
        
        # Run all checks concurrently
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Process results
        health_results = []
        overall_status = "healthy"
        
        for result in results:
            if isinstance(result, Exception):
                health_results.append(HealthCheckResult(
                    "unknown",
                    "unhealthy",
                    f"Health check failed: {str(result)}"
                ).to_dict())
                overall_status = "unhealthy"
            else:
                health_results.append(result.to_dict())
                
                # Determine overall status
                if result.status == "unhealthy":
                    overall_status = "unhealthy"
                elif result.status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": health_results,
            "summary": {
                "total_checks": len(health_results),
                "healthy": len([r for r in health_results if r["status"] == "healthy"]),
                "degraded": len([r for r in health_results if r["status"] == "degraded"]),
                "unhealthy": len([r for r in health_results if r["status"] == "unhealthy"])
            }
        }
    
    async def get_readiness_check(self) -> Dict[str, Any]:
        """Quick readiness check for load balancers."""
        try:
            # Quick database check
            with next(get_session()) as session:
                session.exec(text("SELECT 1")).first()
            
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_liveness_check(self) -> Dict[str, Any]:
        """Basic liveness check."""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
        }


# Global health checker instance
health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return health_checker
