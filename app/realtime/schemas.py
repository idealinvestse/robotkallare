"""
Schemas for realtime AI call integration.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CallMode(str, Enum):
    """Call mode options for outreach campaigns."""
    TTS = "tts"
    AUDIO_FILE = "audio_file"
    REALTIME_AI = "realtime_ai"


class RealtimeCallStatus(str, Enum):
    """Status of a realtime call."""
    INITIATED = "initiated"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RealtimeCallLog(BaseModel):
    """Log entry for realtime call tracking."""
    call_sid: str
    campaign_id: Optional[str] = None
    contact_id: Optional[str] = None
    status: RealtimeCallStatus
    metadata: Optional[Dict[str, Any]] = None
