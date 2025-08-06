"""
Health Check Module for GDial
Provides health monitoring and status endpoints for the application.
"""

import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, text
from redis import Redis
import aiohttp

from app.database import get_session
from app.settings import settings

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status of a single component."""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "OK",
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ):
        """
        Initialize component health.
        
        Args:
            name: Component name
            status: Health status
            message: Status message
            details: Additional details
            response_time_ms: Response time in milliseconds
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.response_time_ms = response_time_ms
        self.checked_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "checked_at": self.checked_at.isoformat()
        }
        
        if self.response_time_ms is not None:
            result["response_time_ms"] = round(self.response_time_ms, 2)
        
        if self.details:
            result["details"] = self.details
        
        return result


class HealthChecker:
    """Main health checker class."""
    
    def __init__(self):
        """Initialize health checker."""
        self.start_time = datetime.utcnow()
        self.checks_performed = 0
        self.last_check_time = None
        self.component_status = {}
    
    async def check_database(self, session: Session) -> ComponentHealth:
        """
        Check database health.
        
        Args:
            session: Database session
            
        Returns:
            ComponentHealth for database
        """
        start_time = time.time()
        
        try:
            # Execute a simple query
            result = session.exec(text("SELECT 1"))
            result.scalar()
            
            # Get database statistics
            stats = {}
            try:
                # Get table counts
                tables = ['contact', 'message', 'contactgroup']
                for table in tables:
                    count_result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[f"{table}_count"] = count_result.scalar()
            except:
                pass  # Stats are optional
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on response time
            if response_time < 100:
                status = HealthStatus.HEALTHY
                message = "Database responding normally"
            elif response_time < 500:
                status = HealthStatus.DEGRADED
                message = "Database responding slowly"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Database response time critical"
            
            return ComponentHealth(
                name="database",
                status=status,
                message=message,
                details=stats,
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def check_redis(self, redis_url: Optional[str] = None) -> ComponentHealth:
        """
        Check Redis health if configured.
        
        Args:
            redis_url: Redis connection URL
            
        Returns:
            ComponentHealth for Redis
        """
        if not redis_url:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis not configured (using in-memory cache)"
            )
        
        start_time = time.time()
        
        try:
            redis_client = Redis.from_url(redis_url)
            
            # Ping Redis
            redis_client.ping()
            
            # Get Redis info
            info = redis_client.info()
            details = {
                "version": info.get("redis_version"),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients"),
                "uptime_days": info.get("uptime_in_days")
            }
            
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis responding normally",
                details=details,
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def check_twilio(self) -> ComponentHealth:
        """
        Check Twilio API health.
        
        Returns:
            ComponentHealth for Twilio
        """
        start_time = time.time()
        
        try:
            # Check if Twilio credentials are configured
            if not hasattr(settings, 'twilio_account_sid') or not settings.twilio_account_sid:
                return ComponentHealth(
                    name="twilio",
                    status=HealthStatus.DEGRADED,
                    message="Twilio credentials not configured"
                )
            
            # Make a simple API call to Twilio status endpoint
            async with aiohttp.ClientSession() as session:
                url = "https://status.twilio.com/api/v2/status.json"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check Twilio's reported status
                        twilio_status = data.get("status", {}).get("indicator", "none")
                        
                        if twilio_status == "none":
                            status = HealthStatus.HEALTHY
                            message = "Twilio services operational"
                        elif twilio_status in ["minor", "major"]:
                            status = HealthStatus.DEGRADED
                            message = f"Twilio experiencing {twilio_status} issues"
                        else:
                            status = HealthStatus.UNHEALTHY
                            message = "Twilio services disrupted"
                        
                        response_time = (time.time() - start_time) * 1000
                        
                        return ComponentHealth(
                            name="twilio",
                            status=status,
                            message=message,
                            details={"twilio_status": twilio_status},
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            name="twilio",
                            status=HealthStatus.DEGRADED,
                            message="Could not check Twilio status"
                        )
                        
        except Exception as e:
            logger.error(f"Twilio health check failed: {e}")
            return ComponentHealth(
                name="twilio",
                status=HealthStatus.DEGRADED,
                message="Twilio health check failed",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_system_resources(self) -> ComponentHealth:
        """
        Check system resource usage.
        
        Returns:
            ComponentHealth for system resources
        """
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            details = {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            }
            
            # Determine health based on resource usage
            issues = []
            
            if cpu_percent > 90:
                issues.append("CPU usage critical")
            elif cpu_percent > 70:
                issues.append("CPU usage high")
            
            if memory.percent > 90:
                issues.append("Memory usage critical")
            elif memory.percent > 80:
                issues.append("Memory usage high")
            
            if disk.percent > 95:
                issues.append("Disk space critical")
            elif disk.percent > 90:
                issues.append("Disk space low")
            
            if not issues:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            elif any("critical" in issue for issue in issues):
                status = HealthStatus.UNHEALTHY
                message = "; ".join(issues)
            else:
                status = HealthStatus.DEGRADED
                message = "; ".join(issues)
            
            return ComponentHealth(
                name="system",
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return ComponentHealth(
                name="system",
                status=HealthStatus.UNHEALTHY,
                message=f"System check failed: {str(e)}"
            )
    
    async def check_all(self, session: Session) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Args:
            session: Database session
            
        Returns:
            Complete health status
        """
        self.checks_performed += 1
        self.last_check_time = datetime.utcnow()
        
        # Run all checks
        components = []
        
        # Database check
        db_health = await self.check_database(session)
        components.append(db_health)
        self.component_status["database"] = db_health.status
        
        # Redis check (if configured)
        redis_url = getattr(settings, 'redis_url', None)
        redis_health = await self.check_redis(redis_url)
        components.append(redis_health)
        self.component_status["redis"] = redis_health.status
        
        # Twilio check
        twilio_health = await self.check_twilio()
        components.append(twilio_health)
        self.component_status["twilio"] = twilio_health.status
        
        # System resources check
        system_health = self.check_system_resources()
        components.append(system_health)
        self.component_status["system"] = system_health.status
        
        # Determine overall status
        unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
            overall_message = f"{unhealthy_count} component(s) unhealthy"
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
            overall_message = f"{degraded_count} component(s) degraded"
        else:
            overall_status = HealthStatus.HEALTHY
            overall_message = "All systems operational"
        
        # Calculate uptime
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "status": overall_status,
            "message": overall_message,
            "timestamp": self.last_check_time.isoformat(),
            "uptime": {
                "days": uptime.days,
                "hours": uptime.seconds // 3600,
                "minutes": (uptime.seconds % 3600) // 60
            },
            "checks_performed": self.checks_performed,
            "components": [c.to_dict() for c in components],
            "version": getattr(settings, 'app_version', '1.0.0'),
            "environment": getattr(settings, 'environment', 'development')
        }
    
    async def check_liveness(self) -> Dict[str, Any]:
        """
        Simple liveness check.
        
        Returns:
            Liveness status
        """
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_readiness(self, session: Session) -> Dict[str, Any]:
        """
        Readiness check for load balancers.
        
        Args:
            session: Database session
            
        Returns:
            Readiness status
        """
        # Check critical components only
        db_health = await self.check_database(session)
        
        is_ready = db_health.status != HealthStatus.UNHEALTHY
        
        return {
            "ready": is_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_health.status
            }
        }


# Global health checker instance
health_checker = HealthChecker()


# Create health check router
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=Dict[str, Any])
async def health_check(session: Session = Depends(get_session)):
    """
    Comprehensive health check endpoint.
    
    Returns detailed health status of all components.
    """
    result = await health_checker.check_all(session)
    
    # Set appropriate status code
    if result["status"] == HealthStatus.UNHEALTHY:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif result["status"] == HealthStatus.DEGRADED:
        status_code = status.HTTP_200_OK  # Still return 200 for degraded
    else:
        status_code = status.HTTP_200_OK
    
    return JSONResponse(content=result, status_code=status_code)


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """
    Simple liveness check endpoint.
    
    Used by Kubernetes/Docker to check if the container is alive.
    """
    result = await health_checker.check_liveness()
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(session: Session = Depends(get_session)):
    """
    Readiness check endpoint.
    
    Used by load balancers to check if the service is ready to accept traffic.
    """
    result = await health_checker.check_readiness(session)
    
    status_code = (
        status.HTTP_200_OK if result["ready"]
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(content=result, status_code=status_code)


@router.get("/metrics", response_model=Dict[str, Any])
async def metrics_endpoint():
    """
    Metrics endpoint for monitoring systems.
    
    Returns metrics in a format suitable for Prometheus/Grafana.
    """
    metrics = {
        "gdial_uptime_seconds": (
            datetime.utcnow() - health_checker.start_time
        ).total_seconds(),
        "gdial_health_checks_total": health_checker.checks_performed,
        "gdial_component_status": health_checker.component_status,
        "gdial_system_cpu_percent": psutil.cpu_percent(),
        "gdial_system_memory_percent": psutil.virtual_memory().percent,
        "gdial_system_disk_percent": psutil.disk_usage('/').percent
    }
    
    return JSONResponse(content=metrics, status_code=status.HTTP_200_OK)
