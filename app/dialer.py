"""Refactored dialer module with clean wrapper functions.

This module provides backward compatibility while delegating to the new service architecture.
"""
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Sequence, Optional, Dict, Any, List
from sqlmodel import Session

from app.services.dialer_service import DialerService as NewDialerService
from app.services.call_service import CallService
from app.workers.call_worker import dial_contacts_worker
from app.models import Contact, Message, CallRun

logger = logging.getLogger(__name__)


class DialerService:
    """Legacy DialerService - DEPRECATED wrapper around new architecture."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        logger.warning("DialerService class is deprecated. Use app.services.dialer_service.DialerService instead.")
        self.session = session
        self._new_service = NewDialerService(session)
    
    async def start_call_run(
        self, 
        contacts: List[uuid.UUID] = None,
        message = None,
        group_id: Optional[uuid.UUID] = None,
        name: str = "Call Run",
        description: Optional[str] = None,
        dtmf_confirmations: bool = False,
        custom_data: Optional[Dict[str, Any]] = None,
        sms_after_dtmf: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Deprecated wrapper - delegates to new DialerService."""
        return await self._new_service.start_call_run(
            contacts=contacts,
            message=message,
            group_id=group_id,
            name=name,
            description=description,
            dtmf_confirmations=dtmf_confirmations,
            custom_data=custom_data,
            sms_after_dtmf=sms_after_dtmf
        )
    
    async def dial_contact(self, contact_id: uuid.UUID, message_id: uuid.UUID, burn_message_token: Optional[str] = None) -> bool:
        """Deprecated wrapper - delegates to new DialerService."""
        return await self._new_service.dial_contact(
            contact_id=contact_id,
            message_id=message_id,
            burn_message_token=burn_message_token
        )


# Legacy global functions - DEPRECATED
async def dial_contacts(
    contacts: Sequence[uuid.UUID] = None,
    group_id: Optional[uuid.UUID] = None,
    message_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None,
    call_run_name: Optional[str] = None,
    call_run_description: Optional[str] = None,
) -> None:
    """
    DEPRECATED: Background task entry point for dialing contacts.
    
    Use app.workers.call_worker.dial_contacts_worker instead.
    """
    logger.warning("dial_contacts function is deprecated. Use app.workers.call_worker.dial_contacts_worker instead.")
    
    await dial_contacts_worker(
        contacts=contacts,
        group_id=group_id,
        message_id=message_id,
        call_run_id=call_run_id,
        call_run_name=call_run_name,
        call_run_description=call_run_description
    )


async def make_manual_call(
    contact_id: uuid.UUID,
    message_id: uuid.UUID,
    phone_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    DEPRECATED: Make a manual call to a specific contact.
    
    Use app.services.call_service.CallService.make_manual_call instead.
    """
    logger.warning("make_manual_call function is deprecated. Use app.services.call_service.CallService.make_manual_call instead.")
    
    from app.database import get_session
    
    with next(get_session()) as session:
        call_service = CallService(session)
        return await call_service.make_manual_call(
            contact_id=contact_id,
            message_id=message_id,
            phone_id=phone_id,
            call_run_id=call_run_id
        )


async def make_custom_call(
    contact_id: uuid.UUID,
    message_content: str,
    phone_id: Optional[uuid.UUID] = None,
    dtmf_responses: Optional[List[dict]] = None,
    save_as_template: bool = False,
    template_name: Optional[str] = None,
    save_dtmf_responses: bool = False,
    call_run_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    DEPRECATED: Make a custom call with specific message content.
    
    Use app.services.call_service.CallService.make_custom_call instead.
    """
    logger.warning("make_custom_call function is deprecated. Use app.services.call_service.CallService.make_custom_call instead.")
    
    from app.database import get_session
    
    with next(get_session()) as session:
        call_service = CallService(session)
        return await call_service.make_custom_call(
            contact_id=contact_id,
            message_content=message_content,
            phone_id=phone_id,
            dtmf_responses=dtmf_responses,
            save_as_template=save_as_template,
            template_name=template_name,
            call_run_id=call_run_id
        )
