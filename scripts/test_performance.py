#!/usr/bin/env python3
"""
Performance Testing Script for GDial
Tests and compares query performance before and after optimization.
"""

import sys
import time
import random
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.database import get_engine
from app.models import Contact, PhoneNumber, ContactGroup, Message, CallLog, SmsLog
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.utils.performance_monitor import benchmark_query, DatabasePerformanceAnalyzer
from app.utils.query_optimizer import QueryOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTester:
    """Test database query performance."""
    
    def __init__(self):
        """Initialize performance tester."""
        self.engine = get_engine()
        self.results = {}
        
    def test_contact_queries(self, session: Session) -> Dict[str, Any]:
        """Test contact-related query performance."""
        logger.info("\n=== Testing Contact Queries ===")
        results = {}
        
        # Test 1: Get all active contacts
        query1 = "SELECT * FROM contact WHERE active = 1"
        results['all_active_contacts'] = benchmark_query(session, query1, iterations=5)
        logger.info(f"All active contacts: {results['all_active_contacts']['avg_time']:.4f}s avg")
        
        # Test 2: Search contacts by name
        query2 = "SELECT * FROM contact WHERE name LIKE '%John%'"
        results['search_by_name'] = benchmark_query(session, query2, iterations=5)
        logger.info(f"Search by name: {results['search_by_name']['avg_time']:.4f}s avg")
        
        # Test 3: Get contacts with phone numbers (JOIN)
        query3 = """
            SELECT DISTINCT c.* 
            FROM contact c 
            JOIN phonenumber p ON c.id = p.contact_id 
            WHERE c.active = 1
        """
        results['contacts_with_phones'] = benchmark_query(session, query3, iterations=5)
        logger.info(f"Contacts with phones: {results['contacts_with_phones']['avg_time']:.4f}s avg")
        
        # Test 4: Get contact by ID
        query4 = "SELECT * FROM contact WHERE id = '00000000-0000-0000-0000-000000000001'"
        results['contact_by_id'] = benchmark_query(session, query4, iterations=10)
        logger.info(f"Contact by ID: {results['contact_by_id']['avg_time']:.4f}s avg")
        
        return results
    
    def test_group_queries(self, session: Session) -> Dict[str, Any]:
        """Test group-related query performance."""
        logger.info("\n=== Testing Group Queries ===")
        results = {}
        
        # Test 1: Get all groups
        query1 = "SELECT * FROM contactgroup WHERE active = 1"
        results['all_groups'] = benchmark_query(session, query1, iterations=5)
        logger.info(f"All groups: {results['all_groups']['avg_time']:.4f}s avg")
        
        # Test 2: Get contacts in a group
        query2 = """
            SELECT c.* 
            FROM contact c 
            JOIN contactgroupmembership m ON c.id = m.contact_id 
            WHERE m.group_id = '00000000-0000-0000-0000-000000000001'
        """
        results['contacts_in_group'] = benchmark_query(session, query2, iterations=5)
        logger.info(f"Contacts in group: {results['contacts_in_group']['avg_time']:.4f}s avg")
        
        # Test 3: Check membership
        query3 = """
            SELECT * FROM contactgroupmembership 
            WHERE group_id = '00000000-0000-0000-0000-000000000001' 
            AND contact_id = '00000000-0000-0000-0000-000000000002'
        """
        results['check_membership'] = benchmark_query(session, query3, iterations=10)
        logger.info(f"Check membership: {results['check_membership']['avg_time']:.4f}s avg")
        
        return results
    
    def test_message_queries(self, session: Session) -> Dict[str, Any]:
        """Test message-related query performance."""
        logger.info("\n=== Testing Message Queries ===")
        results = {}
        
        # Test 1: Get active templates
        query1 = "SELECT * FROM message WHERE active = 1 AND is_template = 1"
        results['active_templates'] = benchmark_query(session, query1, iterations=5)
        logger.info(f"Active templates: {results['active_templates']['avg_time']:.4f}s avg")
        
        # Test 2: Get messages by type
        query2 = "SELECT * FROM message WHERE message_type = 'sms' AND active = 1"
        results['messages_by_type'] = benchmark_query(session, query2, iterations=5)
        logger.info(f"Messages by type: {results['messages_by_type']['avg_time']:.4f}s avg")
        
        return results
    
    def test_log_queries(self, session: Session) -> Dict[str, Any]:
        """Test log-related query performance."""
        logger.info("\n=== Testing Log Queries ===")
        results = {}
        
        # Test 1: Get recent call logs
        query1 = """
            SELECT * FROM calllog 
            WHERE created_at > datetime('now', '-7 days') 
            ORDER BY created_at DESC 
            LIMIT 100
        """
        results['recent_calls'] = benchmark_query(session, query1, iterations=5)
        logger.info(f"Recent calls: {results['recent_calls']['avg_time']:.4f}s avg")
        
        # Test 2: Get SMS logs by status
        query2 = "SELECT * FROM smslog WHERE status = 'sent' LIMIT 100"
        results['sms_by_status'] = benchmark_query(session, query2, iterations=5)
        logger.info(f"SMS by status: {results['sms_by_status']['avg_time']:.4f}s avg")
        
        # Test 3: Get logs for a contact
        query3 = """
            SELECT * FROM smslog 
            WHERE contact_id = '00000000-0000-0000-0000-000000000001' 
            ORDER BY created_at DESC
        """
        results['logs_for_contact'] = benchmark_query(session, query3, iterations=5)
        logger.info(f"Logs for contact: {results['logs_for_contact']['avg_time']:.4f}s avg")
        
        # Test 4: Get retry candidates
        query4 = """
            SELECT * FROM smslog 
            WHERE is_retry = 0 
            AND retry_at < datetime('now') 
            AND retry_count < 3
        """
        results['retry_candidates'] = benchmark_query(session, query4, iterations=5)
        logger.info(f"Retry candidates: {results['retry_candidates']['avg_time']:.4f}s avg")
        
        return results
    
    def test_complex_queries(self, session: Session) -> Dict[str, Any]:
        """Test complex multi-table queries."""
        logger.info("\n=== Testing Complex Queries ===")
        results = {}
        
        # Test 1: Campaign statistics
        query1 = """
            SELECT 
                c.id, c.name, c.status,
                COUNT(DISTINCT cl.contact_id) as contacts_reached,
                COUNT(DISTINCT CASE WHEN s.status = 'sent' THEN s.id END) as sms_sent
            FROM outreachcampaign c
            LEFT JOIN outreachcampaigncontactlink cl ON c.id = cl.campaign_id
            LEFT JOIN smslog s ON c.id = s.outreach_campaign_id
            WHERE c.status = 'completed'
            GROUP BY c.id, c.name, c.status
        """
        results['campaign_stats'] = benchmark_query(session, query1, iterations=3)
        logger.info(f"Campaign stats: {results['campaign_stats']['avg_time']:.4f}s avg")
        
        # Test 2: Contact activity summary
        query2 = """
            SELECT 
                c.id, c.name,
                COUNT(DISTINCT s.id) as sms_count,
                COUNT(DISTINCT cl.id) as call_count,
                MAX(s.created_at) as last_sms,
                MAX(cl.created_at) as last_call
            FROM contact c
            LEFT JOIN smslog s ON c.id = s.contact_id
            LEFT JOIN calllog cl ON c.id = cl.contact_id
            WHERE c.active = 1
            GROUP BY c.id, c.name
            LIMIT 50
        """
        results['contact_activity'] = benchmark_query(session, query2, iterations=3)
        logger.info(f"Contact activity: {results['contact_activity']['avg_time']:.4f}s avg")
        
        return results
    
    def analyze_query_plans(self, session: Session):
        """Analyze query execution plans."""
        logger.info("\n=== Analyzing Query Plans ===")
        
        optimizer = QueryOptimizer()
        
        # Analyze a complex query
        query = """
            SELECT c.*, p.number 
            FROM contact c 
            JOIN phonenumber p ON c.id = p.contact_id 
            WHERE c.active = 1 AND p.priority = 1
        """
        
        plan = optimizer.explain_query(session, query)
        analysis = optimizer.analyze_table_scan(plan)
        
        logger.info(f"Query plan analysis:")
        logger.info(f"  Has table scan: {analysis['has_table_scan']}")
        logger.info(f"  Tables scanned: {analysis['tables_scanned']}")
        logger.info(f"  Is optimized: {analysis['is_optimized']}")
        
        if analysis['suggestions']:
            logger.info("  Suggestions:")
            for suggestion in analysis['suggestions']:
                logger.info(f"    - {suggestion}")
    
    def run_all_tests(self):
        """Run all performance tests."""
        logger.info("=" * 60)
        logger.info("GDIAL PERFORMANCE TEST SUITE")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        with Session(self.engine) as session:
            # Get database statistics
            analyzer = DatabasePerformanceAnalyzer()
            
            logger.info("\n=== Database Statistics ===")
            table_stats = analyzer.analyze_table_statistics(session)
            for table, stats in table_stats.items():
                logger.info(f"  {table}: {stats['row_count']} rows, {stats['size_mb']:.2f} MB")
            
            logger.info("\n=== Index Information ===")
            indexes = analyzer.analyze_index_usage(session)
            logger.info(f"  Total indexes: {len(indexes)}")
            
            # Run performance tests
            self.results['contacts'] = self.test_contact_queries(session)
            self.results['groups'] = self.test_group_queries(session)
            self.results['messages'] = self.test_message_queries(session)
            self.results['logs'] = self.test_log_queries(session)
            self.results['complex'] = self.test_complex_queries(session)
            
            # Analyze query plans
            self.analyze_query_plans(session)
            
            # Print summary
            self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE TEST SUMMARY")
        logger.info("=" * 60)
        
        total_time = 0
        query_count = 0
        
        for category, tests in self.results.items():
            category_time = sum(t['total_time'] for t in tests.values())
            category_queries = sum(t['iterations'] for t in tests.values())
            
            logger.info(f"\n{category.upper()}:")
            logger.info(f"  Total queries: {category_queries}")
            logger.info(f"  Total time: {category_time:.3f}s")
            
            # Find slowest query in category
            slowest = max(tests.items(), key=lambda x: x[1]['avg_time'])
            logger.info(f"  Slowest: {slowest[0]} ({slowest[1]['avg_time']:.4f}s avg)")
            
            # Find fastest query in category
            fastest = min(tests.items(), key=lambda x: x[1]['avg_time'])
            logger.info(f"  Fastest: {fastest[0]} ({fastest[1]['avg_time']:.4f}s avg)")
            
            total_time += category_time
            query_count += category_queries
        
        logger.info(f"\nOVERALL:")
        logger.info(f"  Total queries executed: {query_count}")
        logger.info(f"  Total execution time: {total_time:.3f}s")
        logger.info(f"  Average query time: {total_time/query_count:.4f}s")
        
        # Performance recommendations
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE RECOMMENDATIONS")
        logger.info("=" * 60)
        
        slow_queries = []
        for category, tests in self.results.items():
            for test_name, result in tests.items():
                if result['avg_time'] > 0.1:  # Queries slower than 100ms
                    slow_queries.append((f"{category}/{test_name}", result['avg_time']))
        
        if slow_queries:
            logger.info("\nQueries that need optimization (>100ms):")
            for query_name, avg_time in sorted(slow_queries, key=lambda x: x[1], reverse=True):
                logger.info(f"  - {query_name}: {avg_time:.4f}s")
        else:
            logger.info("\nAll queries are performing well (<100ms average)")
        
        logger.info("\n" + "=" * 60)
        logger.info("Performance testing complete!")
        logger.info("=" * 60)


def main():
    """Main entry point for performance testing."""
    try:
        tester = PerformanceTester()
        tester.run_all_tests()
        return 0
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
