"""Call run service for managing call run lifecycle and statistics.

This service handles the creation, management, and statistics tracking
of call runs, following the single responsibility principle.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlmodel import Session

from app.models import CallRun
from app.repositories.call_repository import CallRepository

logger = logging.getLogger(__name__)


class CallRunService:
    """Service for managing call run lifecycle and statistics.
    
    This service is focused solely on call run management and
    does not handle individual call operations.
    """
    
    def __init__(self, session: Session):
        """Initialize with database session.
        
        Args:
            session: Database session
        """
        self.session = session
        self.call_repository = CallRepository(session)
    
    def create_call_run(
        self, 
        name: str, 
        description: Optional[str] = None,
        message_id: Optional[uuid.UUID] = None,
        group_id: Optional[uuid.UUID] = None,
        scheduled_message_id: Optional[uuid.UUID] = None
    ) -> CallRun:
        """Create a new call run.
        
        Args:
            name: Name for the call run
            description: Optional description
            message_id: Optional message ID
            group_id: Optional group ID
            scheduled_message_id: Optional scheduled message ID
            
        Returns:
            Created CallRun instance
        """
        try:
            call_run = CallRun(
                name=name,
                description=description,
                message_id=message_id,
                group_id=group_id,
                scheduled_message_id=scheduled_message_id,
                status="in_progress",
                started_at=datetime.now()
            )
            
            created_run = self.call_repository.create_call_run(call_run)
            logger.info(f"Created call run {created_run.id}: {name}")
            
            return created_run
            
        except Exception as e:
            logger.error(f"Failed to create call run '{name}': {e}")
            raise
    
    def get_call_run(self, call_run_id: uuid.UUID) -> Optional[CallRun]:
        """Get a call run by ID.
        
        Args:
            call_run_id: Call run ID
            
        Returns:
            CallRun instance or None if not found
        """
        try:
            return self.call_repository.get_call_run(call_run_id)
        except Exception as e:
            logger.error(f"Failed to get call run {call_run_id}: {e}")
            raise
    
    def update_call_run_stats(self, call_run_id: uuid.UUID) -> bool:
        """Update call run statistics.
        
        Args:
            call_run_id: Call run ID
            
        Returns:
            True if successful
        """
        try:
            self.call_repository.update_call_run_stats(call_run_id)
            logger.debug(f"Updated stats for call run {call_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update stats for call run {call_run_id}: {e}")
            raise
    
    def complete_call_run(self, call_run_id: uuid.UUID) -> bool:
        """Mark a call run as completed.
        
        Args:
            call_run_id: Call run ID
            
        Returns:
            True if successful
        """
        try:
            call_run = self.get_call_run(call_run_id)
            if not call_run:
                logger.warning(f"Call run {call_run_id} not found for completion")
                return False
            
            call_run.status = "completed"
            call_run.completed_at = datetime.now()
            
            self.session.add(call_run)
            self.session.commit()
            
            logger.info(f"Completed call run {call_run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete call run {call_run_id}: {e}")
            raise
    
    def cancel_call_run(self, call_run_id: uuid.UUID, reason: Optional[str] = None) -> bool:
        """Cancel a call run.
        
        Args:
            call_run_id: Call run ID
            reason: Optional cancellation reason
            
        Returns:
            True if successful
        """
        try:
            call_run = self.get_call_run(call_run_id)
            if not call_run:
                logger.warning(f"Call run {call_run_id} not found for cancellation")
                return False
            
            call_run.status = "cancelled"
            call_run.completed_at = datetime.now()
            
            if reason:
                call_run.description = f"{call_run.description or ''} [CANCELLED: {reason}]"
            
            self.session.add(call_run)
            self.session.commit()
            
            logger.info(f"Cancelled call run {call_run_id}: {reason or 'No reason provided'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel call run {call_run_id}: {e}")
            raise
    
    def get_call_run_statistics(self, call_run_id: uuid.UUID) -> Dict[str, Any]:
        """Get detailed statistics for a call run.
        
        Args:
            call_run_id: Call run ID
            
        Returns:
            Dictionary with call run statistics
        """
        try:
            call_run = self.get_call_run(call_run_id)
            if not call_run:
                return {}
            
            # Get call logs for this run
            call_logs = self.call_repository.get_call_logs_by_run_id(call_run_id)
            
            # Calculate statistics
            total_calls = len(call_logs)
            answered_calls = len([log for log in call_logs if log.answered])
            failed_calls = len([log for log in call_logs if log.status == "error"])
            no_answer_calls = len([log for log in call_logs if log.status == "no-answer"])
            
            # Calculate duration if completed
            duration_minutes = None
            if call_run.completed_at and call_run.started_at:
                duration = call_run.completed_at - call_run.started_at
                duration_minutes = duration.total_seconds() / 60
            
            return {
                "call_run_id": call_run_id,
                "name": call_run.name,
                "status": call_run.status,
                "started_at": call_run.started_at,
                "completed_at": call_run.completed_at,
                "duration_minutes": duration_minutes,
                "total_calls": total_calls,
                "answered_calls": answered_calls,
                "failed_calls": failed_calls,
                "no_answer_calls": no_answer_calls,
                "success_rate": (answered_calls / total_calls * 100) if total_calls > 0 else 0,
                "completion_rate": ((answered_calls + no_answer_calls) / total_calls * 100) if total_calls > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics for call run {call_run_id}: {e}")
            raise
    
    def list_active_call_runs(self) -> List[CallRun]:
        """Get all active (in-progress) call runs.
        
        Returns:
            List of active CallRun instances
        """
        try:
            return self.call_repository.get_active_call_runs()
        except Exception as e:
            logger.error(f"Failed to list active call runs: {e}")
            raise
    
    def cleanup_stale_call_runs(self, max_age_hours: int = 24) -> int:
        """Clean up stale call runs that have been running too long.
        
        Args:
            max_age_hours: Maximum age in hours before considering stale
            
        Returns:
            Number of call runs cleaned up
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            stale_runs = self.call_repository.get_stale_call_runs(cutoff_time)
            
            cleaned_count = 0
            for call_run in stale_runs:
                if self.cancel_call_run(call_run.id, f"Stale run (older than {max_age_hours}h)"):
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} stale call runs")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup stale call runs: {e}")
            raise
