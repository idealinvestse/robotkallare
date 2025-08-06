"""
Performance Monitoring Module for GDial
Tracks and reports on application performance metrics.
"""

import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from pathlib import Path
from sqlmodel import Session, text

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and track application performance metrics."""
    
    def __init__(self, log_dir: str = "logs/performance"):
        """Initialize performance monitor with log directory."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = {
            'queries': [],
            'api_calls': [],
            'system_resources': []
        }
        self.start_time = time.time()
        
    def track_query(self, query_name: str):
        """Decorator to track database query performance."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                try:
                    result = func(*args, **kwargs)
                    status = 'success'
                    error = None
                except Exception as e:
                    status = 'error'
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                    
                    metric = {
                        'timestamp': datetime.now().isoformat(),
                        'query_name': query_name,
                        'function': func.__name__,
                        'execution_time': end_time - start_time,
                        'memory_delta': end_memory - start_memory,
                        'status': status,
                        'error': error
                    }
                    
                    self.metrics['queries'].append(metric)
                    
                    if metric['execution_time'] > 0.1:  # Log slow queries
                        logger.warning(
                            f"Slow query '{query_name}': {metric['execution_time']:.3f}s"
                        )
                
                return result
            return wrapper
        return decorator
    
    def track_api_endpoint(self, endpoint: str):
        """Decorator to track API endpoint performance."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    status_code = getattr(result, 'status_code', 200)
                    status = 'success' if status_code < 400 else 'error'
                except Exception as e:
                    status = 'error'
                    status_code = 500
                    raise
                finally:
                    end_time = time.time()
                    
                    metric = {
                        'timestamp': datetime.now().isoformat(),
                        'endpoint': endpoint,
                        'method': func.__name__,
                        'execution_time': end_time - start_time,
                        'status': status,
                        'status_code': status_code
                    }
                    
                    self.metrics['api_calls'].append(metric)
                    
                    if metric['execution_time'] > 1.0:  # Log slow endpoints
                        logger.warning(
                            f"Slow API endpoint '{endpoint}': {metric['execution_time']:.3f}s"
                        )
                
                return result
            return wrapper
        return decorator
    
    def capture_system_metrics(self):
        """Capture current system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / 1024 / 1024,
            'memory_available_mb': memory.available / 1024 / 1024,
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / 1024 / 1024 / 1024,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024
        }
        
        self.metrics['system_resources'].append(metric)
        return metric
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get statistics about query performance."""
        if not self.metrics['queries']:
            return {}
        
        execution_times = [q['execution_time'] for q in self.metrics['queries']]
        slow_queries = [q for q in self.metrics['queries'] if q['execution_time'] > 0.1]
        
        return {
            'total_queries': len(self.metrics['queries']),
            'slow_queries': len(slow_queries),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'total_execution_time': sum(execution_times),
            'slowest_queries': sorted(
                self.metrics['queries'], 
                key=lambda x: x['execution_time'], 
                reverse=True
            )[:5]
        }
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get statistics about API performance."""
        if not self.metrics['api_calls']:
            return {}
        
        execution_times = [a['execution_time'] for a in self.metrics['api_calls']]
        error_calls = [a for a in self.metrics['api_calls'] if a['status'] == 'error']
        
        return {
            'total_calls': len(self.metrics['api_calls']),
            'error_calls': len(error_calls),
            'error_rate': len(error_calls) / len(self.metrics['api_calls']),
            'avg_response_time': sum(execution_times) / len(execution_times),
            'max_response_time': max(execution_times),
            'min_response_time': min(execution_times),
            'slowest_endpoints': sorted(
                self.metrics['api_calls'], 
                key=lambda x: x['execution_time'], 
                reverse=True
            )[:5]
        }
    
    def save_metrics(self):
        """Save current metrics to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.log_dir / f"performance_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Performance metrics saved to {filename}")
    
    def generate_report(self) -> str:
        """Generate a performance report."""
        uptime = time.time() - self.start_time
        query_stats = self.get_query_statistics()
        api_stats = self.get_api_statistics()
        
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"Uptime: {uptime:.2f} seconds")
        report.append("")
        
        if query_stats:
            report.append("DATABASE QUERIES")
            report.append("-" * 40)
            report.append(f"Total Queries: {query_stats['total_queries']}")
            report.append(f"Slow Queries: {query_stats['slow_queries']}")
            report.append(f"Avg Execution Time: {query_stats['avg_execution_time']:.3f}s")
            report.append(f"Max Execution Time: {query_stats['max_execution_time']:.3f}s")
            report.append("")
            
            if query_stats['slowest_queries']:
                report.append("Top 5 Slowest Queries:")
                for q in query_stats['slowest_queries'][:5]:
                    report.append(f"  - {q['query_name']}: {q['execution_time']:.3f}s")
            report.append("")
        
        if api_stats:
            report.append("API ENDPOINTS")
            report.append("-" * 40)
            report.append(f"Total Calls: {api_stats['total_calls']}")
            report.append(f"Error Rate: {api_stats['error_rate']:.2%}")
            report.append(f"Avg Response Time: {api_stats['avg_response_time']:.3f}s")
            report.append(f"Max Response Time: {api_stats['max_response_time']:.3f}s")
            report.append("")
            
            if api_stats['slowest_endpoints']:
                report.append("Top 5 Slowest Endpoints:")
                for e in api_stats['slowest_endpoints'][:5]:
                    report.append(f"  - {e['endpoint']}: {e['execution_time']:.3f}s")
            report.append("")
        
        if self.metrics['system_resources']:
            latest_system = self.metrics['system_resources'][-1]
            report.append("SYSTEM RESOURCES")
            report.append("-" * 40)
            report.append(f"CPU Usage: {latest_system['cpu_percent']:.1f}%")
            report.append(f"Memory Usage: {latest_system['memory_percent']:.1f}%")
            report.append(f"Memory Used: {latest_system['memory_used_mb']:.1f} MB")
            report.append(f"Disk Usage: {latest_system['disk_percent']:.1f}%")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


class DatabasePerformanceAnalyzer:
    """Analyze database performance and suggest optimizations."""
    
    @staticmethod
    def analyze_index_usage(session: Session) -> List[Dict[str, Any]]:
        """Analyze which indexes are being used."""
        try:
            # Get all indexes
            result = session.exec(text("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type = 'index' 
                AND sql IS NOT NULL
            """))
            
            indexes = []
            for row in result:
                indexes.append({
                    'name': row[0],
                    'table': row[1],
                    'definition': row[2]
                })
            
            return indexes
        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")
            return []
    
    @staticmethod
    def analyze_table_statistics(session: Session) -> Dict[str, Any]:
        """Get statistics about database tables."""
        stats = {}
        
        tables = [
            'contact', 'phonenumber', 'contactgroup', 'message',
            'calllog', 'smslog', 'outreachcampaign', 'scheduledmessage'
        ]
        
        for table in tables:
            try:
                # Get row count
                count_result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                
                # Get table size (approximate)
                size_result = session.exec(text(f"""
                    SELECT SUM(pgsize) FROM dbstat WHERE name='{table}'
                """))
                size = size_result.scalar() or 0
                
                stats[table] = {
                    'row_count': count,
                    'size_bytes': size,
                    'size_mb': size / 1024 / 1024
                }
            except:
                pass  # Table might not exist
        
        return stats
    
    @staticmethod
    def suggest_query_optimizations(query: str) -> List[str]:
        """Suggest optimizations for a given query."""
        suggestions = []
        
        query_lower = query.lower()
        
        # Check for SELECT *
        if 'select *' in query_lower:
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        # Check for missing WHERE clause
        if 'where' not in query_lower and ('update' in query_lower or 'delete' in query_lower):
            suggestions.append("Add WHERE clause to avoid full table scan")
        
        # Check for LIKE with leading wildcard
        if 'like' in query_lower and "'%" in query:
            suggestions.append("Leading wildcard in LIKE prevents index usage")
        
        # Check for OR conditions
        if ' or ' in query_lower:
            suggestions.append("Consider using UNION instead of OR for better index usage")
        
        # Check for NOT IN
        if 'not in' in query_lower:
            suggestions.append("Consider using NOT EXISTS instead of NOT IN")
        
        # Check for missing LIMIT
        if 'select' in query_lower and 'limit' not in query_lower:
            suggestions.append("Add LIMIT clause to prevent fetching too many rows")
        
        return suggestions


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def benchmark_query(session: Session, query: str, iterations: int = 10) -> Dict[str, float]:
    """Benchmark a query by running it multiple times."""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        session.exec(text(query))
        times.append(time.time() - start)
    
    return {
        'avg_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'total_time': sum(times),
        'iterations': iterations
    }
