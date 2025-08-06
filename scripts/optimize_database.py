#!/usr/bin/env python3
"""
Database Performance Optimization Script for GDial
This script adds necessary indexes and optimizes the database for better query performance.
"""

import logging
import sqlite3
import sys
import os
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_engine, init_database_engine
from sqlmodel import Session, text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization utility for GDial."""
    
    def __init__(self):
        """Initialize the optimizer with database connection."""
        self.engine = init_database_engine()
        self.indexes_created = []
        self.indexes_failed = []
        
    def get_existing_indexes(self, session: Session) -> List[str]:
        """Get list of existing indexes in the database."""
        try:
            result = session.exec(text("""
                SELECT name FROM sqlite_master 
                WHERE type = 'index' 
                AND sql IS NOT NULL
            """))
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error fetching existing indexes: {e}")
            return []
    
    def create_index(self, session: Session, index_name: str, table_name: str, 
                    columns: str, unique: bool = False) -> bool:
        """Create a database index if it doesn't exist."""
        try:
            existing_indexes = self.get_existing_indexes(session)
            
            if index_name in existing_indexes:
                logger.info(f"Index {index_name} already exists, skipping...")
                return True
            
            unique_clause = "UNIQUE" if unique else ""
            sql = f"CREATE {unique_clause} INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"
            
            session.exec(text(sql))
            session.commit()
            
            logger.info(f"✓ Created index: {index_name} on {table_name}({columns})")
            self.indexes_created.append(index_name)
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create index {index_name}: {e}")
            self.indexes_failed.append((index_name, str(e)))
            session.rollback()
            return False
    
    def optimize_contact_indexes(self, session: Session):
        """Create indexes for Contact table optimization."""
        logger.info("\n=== Optimizing Contact Table Indexes ===")
        
        # Index for active contacts (frequently used in queries)
        self.create_index(
            session, "idx_contact_active", "contact", "active"
        )
        
        # Index for name searches (used in search_contacts)
        self.create_index(
            session, "idx_contact_name", "contact", "name"
        )
        
        # Composite index for active + name (common query pattern)
        self.create_index(
            session, "idx_contact_active_name", "contact", "active, name"
        )
        
    def optimize_phone_number_indexes(self, session: Session):
        """Create indexes for PhoneNumber table optimization."""
        logger.info("\n=== Optimizing PhoneNumber Table Indexes ===")
        
        # Index for contact_id (foreign key, used in joins)
        self.create_index(
            session, "idx_phonenumber_contact_id", "phonenumber", "contact_id"
        )
        
        # Index for phone number lookups
        self.create_index(
            session, "idx_phonenumber_number", "phonenumber", "number"
        )
        
        # Composite index for contact_id + priority (for ordered phone number retrieval)
        self.create_index(
            session, "idx_phonenumber_contact_priority", "phonenumber", "contact_id, priority"
        )
    
    def optimize_group_indexes(self, session: Session):
        """Create indexes for ContactGroup table optimization."""
        logger.info("\n=== Optimizing ContactGroup Table Indexes ===")
        
        # Index for active groups
        self.create_index(
            session, "idx_contactgroup_active", "contactgroup", "active"
        )
        
        # Index for name searches
        self.create_index(
            session, "idx_contactgroup_name", "contactgroup", "name"
        )
    
    def optimize_membership_indexes(self, session: Session):
        """Create indexes for membership/link tables optimization."""
        logger.info("\n=== Optimizing Membership Table Indexes ===")
        
        # ContactGroupMembership indexes
        self.create_index(
            session, "idx_contactgroupmembership_group", 
            "contactgroupmembership", "group_id"
        )
        
        self.create_index(
            session, "idx_contactgroupmembership_contact", 
            "contactgroupmembership", "contact_id"
        )
        
        # Composite index for membership lookups
        self.create_index(
            session, "idx_contactgroupmembership_composite", 
            "contactgroupmembership", "group_id, contact_id",
            unique=True
        )
        
        # GroupContactLink indexes (if different from ContactGroupMembership)
        self.create_index(
            session, "idx_groupcontactlink_group", 
            "groupcontactlink", "group_id"
        )
        
        self.create_index(
            session, "idx_groupcontactlink_contact", 
            "groupcontactlink", "contact_id"
        )
    
    def optimize_message_indexes(self, session: Session):
        """Create indexes for Message table optimization."""
        logger.info("\n=== Optimizing Message Table Indexes ===")
        
        # Index for active messages
        self.create_index(
            session, "idx_message_active", "message", "active"
        )
        
        # Index for template messages
        self.create_index(
            session, "idx_message_is_template", "message", "is_template"
        )
        
        # Index for message type
        self.create_index(
            session, "idx_message_type", "message", "message_type"
        )
        
        # Composite index for common query pattern
        self.create_index(
            session, "idx_message_active_template_type", 
            "message", "active, is_template, message_type"
        )
    
    def optimize_log_indexes(self, session: Session):
        """Create indexes for log tables optimization."""
        logger.info("\n=== Optimizing Log Table Indexes ===")
        
        # CallLog indexes
        self.create_index(
            session, "idx_calllog_contact_id", "calllog", "contact_id"
        )
        
        self.create_index(
            session, "idx_calllog_status", "calllog", "status"
        )
        
        self.create_index(
            session, "idx_calllog_created_at", "calllog", "created_at"
        )
        
        self.create_index(
            session, "idx_calllog_campaign_id", "calllog", "outreach_campaign_id"
        )
        
        # SmsLog indexes
        self.create_index(
            session, "idx_smslog_contact_id", "smslog", "contact_id"
        )
        
        self.create_index(
            session, "idx_smslog_status", "smslog", "status"
        )
        
        self.create_index(
            session, "idx_smslog_created_at", "smslog", "created_at"
        )
        
        self.create_index(
            session, "idx_smslog_campaign_id", "smslog", "outreach_campaign_id"
        )
        
        # Index for retry queries
        self.create_index(
            session, "idx_smslog_retry", "smslog", "is_retry, retry_at"
        )
    
    def optimize_campaign_indexes(self, session: Session):
        """Create indexes for OutreachCampaign table optimization."""
        logger.info("\n=== Optimizing OutreachCampaign Table Indexes ===")
        
        # Index for status queries
        self.create_index(
            session, "idx_outreachcampaign_status", "outreachcampaign", "status"
        )
        
        # Index for date-based queries
        self.create_index(
            session, "idx_outreachcampaign_created", "outreachcampaign", "created_at"
        )
        
        # Index for group associations
        self.create_index(
            session, "idx_outreachcampaign_group", "outreachcampaign", "target_group_id"
        )
        
        # OutreachCampaignContactLink indexes
        self.create_index(
            session, "idx_campaigncontactlink_campaign", 
            "outreachcampaigncontactlink", "campaign_id"
        )
        
        self.create_index(
            session, "idx_campaigncontactlink_contact", 
            "outreachcampaigncontactlink", "contact_id"
        )
    
    def optimize_scheduled_message_indexes(self, session: Session):
        """Create indexes for ScheduledMessage table optimization."""
        logger.info("\n=== Optimizing ScheduledMessage Table Indexes ===")
        
        # Index for scheduled time queries
        self.create_index(
            session, "idx_scheduledmessage_scheduled", 
            "scheduledmessage", "scheduled_time"
        )
        
        # Index for status
        self.create_index(
            session, "idx_scheduledmessage_status", 
            "scheduledmessage", "status"
        )
        
        # Composite index for finding messages to send
        self.create_index(
            session, "idx_scheduledmessage_pending", 
            "scheduledmessage", "status, scheduled_time"
        )
    
    def optimize_burn_message_indexes(self, session: Session):
        """Create indexes for BurnMessage table optimization."""
        logger.info("\n=== Optimizing BurnMessage Table Indexes ===")
        
        # Index for burn time queries
        self.create_index(
            session, "idx_burnmessage_burn_time", 
            "burnmessage", "burn_time"
        )
        
        # Index for status
        self.create_index(
            session, "idx_burnmessage_is_burned", 
            "burnmessage", "is_burned"
        )
        
        # Composite index for finding messages to burn
        self.create_index(
            session, "idx_burnmessage_pending_burn", 
            "burnmessage", "is_burned, burn_time"
        )
    
    def analyze_database(self, session: Session):
        """Run ANALYZE to update SQLite statistics."""
        logger.info("\n=== Running Database Analysis ===")
        try:
            session.exec(text("ANALYZE"))
            session.commit()
            logger.info("✓ Database statistics updated")
        except Exception as e:
            logger.error(f"✗ Failed to analyze database: {e}")
    
    def vacuum_database(self, session: Session):
        """Run VACUUM to optimize database file."""
        logger.info("\n=== Running Database Vacuum ===")
        try:
            # Note: VACUUM cannot be run in a transaction
            session.exec(text("VACUUM"))
            logger.info("✓ Database file optimized")
        except Exception as e:
            logger.warning(f"Could not vacuum database (this is normal if in use): {e}")
    
    def get_table_statistics(self, session: Session):
        """Get statistics about database tables."""
        logger.info("\n=== Database Table Statistics ===")
        try:
            tables = [
                'contact', 'phonenumber', 'contactgroup', 'message',
                'calllog', 'smslog', 'outreachcampaign', 'scheduledmessage'
            ]
            
            for table in tables:
                try:
                    result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"  {table}: {count} rows")
                except:
                    pass  # Table might not exist
                    
        except Exception as e:
            logger.error(f"Error getting table statistics: {e}")
    
    def run_optimization(self):
        """Run the complete optimization process."""
        logger.info("=" * 60)
        logger.info("Starting GDial Database Optimization")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        with Session(self.engine) as session:
            # Get initial statistics
            self.get_table_statistics(session)
            
            # Create all indexes
            self.optimize_contact_indexes(session)
            self.optimize_phone_number_indexes(session)
            self.optimize_group_indexes(session)
            self.optimize_membership_indexes(session)
            self.optimize_message_indexes(session)
            self.optimize_log_indexes(session)
            self.optimize_campaign_indexes(session)
            self.optimize_scheduled_message_indexes(session)
            self.optimize_burn_message_indexes(session)
            
            # Update statistics
            self.analyze_database(session)
            
            # Vacuum if possible
            self.vacuum_database(session)
            
            # Print summary
            self.print_summary()
    
    def print_summary(self):
        """Print optimization summary."""
        logger.info("\n" + "=" * 60)
        logger.info("OPTIMIZATION SUMMARY")
        logger.info("=" * 60)
        
        if self.indexes_created:
            logger.info(f"\n✓ Successfully created {len(self.indexes_created)} indexes:")
            for idx in self.indexes_created:
                logger.info(f"  - {idx}")
        
        if self.indexes_failed:
            logger.info(f"\n✗ Failed to create {len(self.indexes_failed)} indexes:")
            for idx, error in self.indexes_failed:
                logger.info(f"  - {idx}: {error}")
        
        if not self.indexes_created and not self.indexes_failed:
            logger.info("\nAll indexes already exist. Database is optimized!")
        
        logger.info("\n" + "=" * 60)
        logger.info("Optimization complete!")
        logger.info("=" * 60)


def main():
    """Main entry point for the optimization script."""
    try:
        optimizer = DatabaseOptimizer()
        optimizer.run_optimization()
        return 0
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
