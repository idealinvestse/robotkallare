from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime

class CallJob(BaseModel):
    """Schema for a call job message"""
    contact_id: UUID
    phone_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    custom_message_id: Optional[UUID] = None
    custom_message_content: Optional[str] = None
    dtmf_responses: Optional[Dict[str, Dict[str, str]]] = None
    call_run_id: Optional[UUID] = None
    priority: int = 1
    job_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    
class CallBatchJob(BaseModel):
    """Schema for a batch of calls"""
    contacts: List[UUID]
    group_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    call_run_id: Optional[UUID] = None
    call_run_name: Optional[str] = None
    call_run_description: Optional[str] = None
    job_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)