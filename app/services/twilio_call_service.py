"""Twilio call service for direct API interactions.

This service handles all direct interactions with the Twilio API,
following the single responsibility principle.
"""
import uuid
import logging
from typing import Optional, Dict, Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import get_settings

logger = logging.getLogger(__name__)


class TwilioCallService:
    """Service for direct Twilio API call operations.
    
    This service is focused solely on Twilio API interactions and
    does not handle business logic or database operations.
    """
    
    def __init__(self, twilio_client: Optional[Client] = None, settings_override: Optional[Any] = None):
        """Initialize with Twilio client.
        
        Args:
            twilio_client: Optional Twilio client (for testing)
            settings_override: Optional settings override (for testing)
        """
        self.settings = settings_override or get_settings()
        self.twilio_client = twilio_client or Client(
            self.settings.TWILIO_ACCOUNT_SID, 
            self.settings.TWILIO_AUTH_TOKEN
        )
    
    def create_call(
        self, 
        to_number: str, 
        callback_url: str,
        status_callback_url: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Create a Twilio call and return the call SID.
        
        Args:
            to_number: Phone number to call
            callback_url: URL for call handling
            status_callback_url: Optional URL for status callbacks
            timeout: Optional timeout override
            
        Returns:
            Twilio call SID
            
        Raises:
            TwilioRestException: If call creation fails
        """
        try:
            call_timeout = timeout or self.settings.CALL_TIMEOUT_SEC
            
            call_params = {
                "to": to_number,
                "from_": self.settings.TWILIO_FROM_NUMBER,
                "url": callback_url,
                "timeout": call_timeout,
                "status_callback_event": ["completed"],
                "status_callback_method": "POST"
            }
            
            if status_callback_url:
                call_params["status_callback"] = status_callback_url
            
            call = self.twilio_client.calls.create(**call_params)
            
            logger.info(f"Created Twilio call {call.sid} to {to_number}")
            return call.sid
            
        except TwilioRestException as e:
            logger.error(f"Failed to create Twilio call to {to_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating call to {to_number}: {e}")
            raise TwilioRestException(status=500, uri="", msg=str(e))
    
    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get call status from Twilio.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dictionary with call status information
            
        Raises:
            TwilioRestException: If status retrieval fails
        """
        try:
            call = self.twilio_client.calls(call_sid).fetch()
            
            return {
                "sid": call.sid,
                "status": call.status,
                "direction": call.direction,
                "answered_by": call.answered_by,
                "duration": call.duration,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "price_unit": call.price_unit
            }
            
        except TwilioRestException as e:
            logger.error(f"Failed to get status for call {call_sid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting call status for {call_sid}: {e}")
            raise TwilioRestException(status=500, uri="", msg=str(e))
    
    def update_call(self, call_sid: str, **kwargs) -> Dict[str, Any]:
        """Update a Twilio call.
        
        Args:
            call_sid: Twilio call SID
            **kwargs: Call update parameters
            
        Returns:
            Updated call information
            
        Raises:
            TwilioRestException: If call update fails
        """
        try:
            call = self.twilio_client.calls(call_sid).update(**kwargs)
            
            return {
                "sid": call.sid,
                "status": call.status,
                "updated": True
            }
            
        except TwilioRestException as e:
            logger.error(f"Failed to update call {call_sid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating call {call_sid}: {e}")
            raise TwilioRestException(status=500, uri="", msg=str(e))
    
    def hangup_call(self, call_sid: str) -> bool:
        """Hangup a Twilio call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if successful
            
        Raises:
            TwilioRestException: If hangup fails
        """
        try:
            self.twilio_client.calls(call_sid).update(status="completed")
            logger.info(f"Hung up call {call_sid}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Failed to hangup call {call_sid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error hanging up call {call_sid}: {e}")
            raise TwilioRestException(status=500, uri="", msg=str(e))
    
    def build_callback_url(
        self, 
        base_url: str, 
        message_id: Optional[uuid.UUID] = None,
        custom_message_id: Optional[uuid.UUID] = None
    ) -> str:
        """Build callback URL for Twilio call.
        
        Args:
            base_url: Base URL for the application
            message_id: Optional message ID for template calls
            custom_message_id: Optional custom message ID
            
        Returns:
            Complete callback URL
        """
        if custom_message_id:
            return f"{base_url}/custom-voice?custom_message_id={custom_message_id}"
        elif message_id:
            return f"{base_url}/voice?message_id={message_id}"
        else:
            return f"{base_url}/voice"
    
    def build_status_callback_url(self, base_url: str) -> str:
        """Build status callback URL for Twilio call.
        
        Args:
            base_url: Base URL for the application
            
        Returns:
            Complete status callback URL
        """
        return f"{base_url}/call-status"
