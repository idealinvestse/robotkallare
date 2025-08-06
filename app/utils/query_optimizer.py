"""
Query Optimization Utilities for GDial
Provides query profiling and optimization helpers for database operations.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from sqlmodel import Session, text
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class QueryProfiler:
    """Profile and analyze database queries for performance optimization."""
    
    def __init__(self):
        self.query_stats: List[Dict[str, Any]] = []
        self.slow_query_threshold = 0.1  # 100ms
        
    def profile_query(self, func: Callable) -> Callable:
        """Decorator to profile database query execution time."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            query_info = {
                'function': func.__name__,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'args': str(args)[:100],  # Truncate for logging
                'is_slow': execution_time > self.slow_query_threshold
            }
            
            self.query_stats.append(query_info)
            
            if query_info['is_slow']:
                logger.warning(
                    f"Slow query detected in {func.__name__}: "
                    f"{execution_time:.3f}s (threshold: {self.slow_query_threshold}s)"
                )
            
            return result
        return wrapper
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries."""
        return [q for q in self.query_stats if q['is_slow']]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        if not self.query_stats:
            return {}
        
        execution_times = [q['execution_time'] for q in self.query_stats]
        return {
            'total_queries': len(self.query_stats),
            'slow_queries': len(self.get_slow_queries()),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'total_execution_time': sum(execution_times)
        }
    
    def reset_stats(self):
        """Reset collected statistics."""
        self.query_stats = []


# Global profiler instance
query_profiler = QueryProfiler()


class QueryOptimizer:
    """Provides query optimization suggestions and utilities."""
    
    @staticmethod
    def explain_query(session: Session, query: str) -> List[Dict[str, Any]]:
        """Get query execution plan using EXPLAIN QUERY PLAN."""
        try:
            result = session.exec(text(f"EXPLAIN QUERY PLAN {query}"))
            plan = []
            for row in result:
                plan.append({
                    'id': row[0],
                    'parent': row[1],
                    'notused': row[2],
                    'detail': row[3]
                })
            return plan
        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return []
    
    @staticmethod
    def analyze_table_scan(plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query plan for table scans and suggest optimizations."""
        suggestions = []
        has_table_scan = False
        tables_scanned = []
        
        for step in plan:
            detail = step.get('detail', '')
            
            # Check for table scans
            if 'SCAN' in detail and 'USING INDEX' not in detail:
                has_table_scan = True
                # Extract table name
                if 'SCAN' in detail:
                    parts = detail.split()
                    for i, part in enumerate(parts):
                        if part == 'SCAN' and i + 1 < len(parts):
                            tables_scanned.append(parts[i + 1])
            
            # Check for missing indexes
            if 'USING INDEX' not in detail and 'SEARCH' in detail:
                suggestions.append(f"Consider adding index for: {detail}")
        
        return {
            'has_table_scan': has_table_scan,
            'tables_scanned': tables_scanned,
            'suggestions': suggestions,
            'is_optimized': not has_table_scan and len(suggestions) == 0
        }
    
    @staticmethod
    def suggest_indexes(session: Session, table_name: str) -> List[str]:
        """Suggest indexes based on table structure and common query patterns."""
        suggestions = []
        
        try:
            # Get table columns
            result = session.exec(text(f"PRAGMA table_info({table_name})"))
            columns = []
            for row in result:
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'notnull': row[3],
                    'pk': row[5]
                })
            
            # Suggest indexes for common patterns
            for col in columns:
                col_name = col['name']
                
                # Foreign keys should have indexes
                if col_name.endswith('_id') and not col['pk']:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col_name} "
                        f"ON {table_name}({col_name})"
                    )
                
                # Boolean/status columns often used in WHERE clauses
                if col_name in ['active', 'status', 'is_deleted', 'is_burned']:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col_name} "
                        f"ON {table_name}({col_name})"
                    )
                
                # Timestamp columns for date range queries
                if col_name in ['created_at', 'updated_at', 'scheduled_time']:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col_name} "
                        f"ON {table_name}({col_name})"
                    )
            
        except Exception as e:
            logger.error(f"Error suggesting indexes for {table_name}: {e}")
        
        return suggestions


class BatchQueryOptimizer:
    """Optimize batch database operations."""
    
    @staticmethod
    def batch_insert(session: Session, objects: List[Any], batch_size: int = 100):
        """Insert objects in batches for better performance."""
        total = len(objects)
        inserted = 0
        
        for i in range(0, total, batch_size):
            batch = objects[i:i + batch_size]
            session.add_all(batch)
            session.commit()
            inserted += len(batch)
            
            if inserted % 1000 == 0:
                logger.info(f"Inserted {inserted}/{total} objects")
        
        return inserted
    
    @staticmethod
    def batch_update(session: Session, model_class: Any, 
                     updates: List[Dict[str, Any]], batch_size: int = 100):
        """Update objects in batches."""
        total = len(updates)
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = updates[i:i + batch_size]
            
            for update in batch:
                obj_id = update.pop('id')
                obj = session.get(model_class, obj_id)
                if obj:
                    for key, value in update.items():
                        setattr(obj, key, value)
                    updated += 1
            
            session.commit()
            
            if updated % 1000 == 0:
                logger.info(f"Updated {updated}/{total} objects")
        
        return updated


@contextmanager
def query_performance_monitor(operation_name: str):
    """Context manager to monitor query performance."""
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}")
    
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        logger.info(
            f"Operation '{operation_name}' completed in {execution_time:.3f}s"
        )
        
        if execution_time > 1.0:
            logger.warning(
                f"Slow operation detected: '{operation_name}' "
                f"took {execution_time:.3f}s"
            )


def optimize_pagination(query, page: int = 1, page_size: int = 50):
    """Optimize pagination for large result sets."""
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def preload_relationships(query, *relationships):
    """Preload relationships to avoid N+1 queries."""
    from sqlalchemy.orm import selectinload
    
    for relationship in relationships:
        query = query.options(selectinload(relationship))
    
    return query


# Query optimization tips as constants
OPTIMIZATION_TIPS = {
    'use_indexes': 'Always use indexes for columns in WHERE, JOIN, and ORDER BY clauses',
    'avoid_select_all': 'Select only the columns you need instead of SELECT *',
    'use_joins_wisely': 'Use appropriate JOIN types and avoid unnecessary joins',
    'batch_operations': 'Use batch inserts/updates for multiple records',
    'connection_pooling': 'Use connection pooling for better resource management',
    'cache_results': 'Cache frequently accessed, rarely changing data',
    'use_explain': 'Use EXPLAIN to understand query execution plans',
    'avoid_n_plus_one': 'Use eager loading to avoid N+1 query problems',
    'limit_results': 'Always use LIMIT for queries that could return many rows',
    'index_foreign_keys': 'Index all foreign key columns for faster joins'
}
