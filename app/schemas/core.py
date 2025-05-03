"""Core schemas for GDial

This module defines the Pydantic schemas for the main API resources.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, UUID4, Field

class Stats(BaseModel):
    total_calls: int
    completed: int
    no_answer: int
    manual: int
    error: int
    total_sms: int = 0
    sms_sent: int = 0
    sms_failed: int = 0
    last_call: datetime | None = None

# Request schemas
class PhoneNumberCreate(BaseModel):
    number: str
    priority: int

class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    phone_numbers: List[PhoneNumberCreate]

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    contact_ids: Optional[List[UUID4]] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class MessageCreate(BaseModel):
    name: str
    content: str
    is_template: bool = True
    message_type: str = "voice"  # voice, sms, or both
    
class MessageUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    is_template: Optional[bool] = None
    message_type: Optional[str] = None
    
class DtmfResponseCreate(BaseModel):
    digit: str
    description: str
    response_message: str
    
class DtmfResponseUpdate(BaseModel):
    description: Optional[str] = None
    response_message: Optional[str] = None

# Response schemas
class PhoneNumberResponse(BaseModel):
    id: UUID4
    number: str
    priority: int

class GroupBrief(BaseModel):
    id: UUID4
    name: str

class ContactResponse(BaseModel):
    id: UUID4
    name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    phone_numbers: List[PhoneNumberResponse]
    groups: List[GroupBrief] = []

class GroupDetailResponse(BaseModel):
    id: UUID4
    name: str
    description: Optional[str] = None
    contacts: List[ContactResponse] = []

class MessageResponse(BaseModel):
    id: UUID4
    name: str
    content: str
    is_template: bool
    message_type: str
    created_at: datetime
    updated_at: datetime
    
class DtmfResponseResponse(BaseModel):
    digit: str
    description: str
    response_message: str
    created_at: datetime
    updated_at: datetime

class SmsLogResponse(BaseModel):
    id: UUID4
    contact_name: str
    phone_number: str
    message_sid: str
    sent_at: datetime
    status: str
    message: Optional[MessageResponse] = None

class CallLogResponse(BaseModel):
    id: UUID4
    contact_name: str
    phone_number: str
    call_sid: str
    started_at: datetime
    answered: bool
    digits: Optional[str] = None
    status: str
    message: Optional[MessageResponse] = None

# Custom call and SMS schemas
class CustomDtmfResponse(BaseModel):
    digit: str
    description: str
    response_message: str

class CustomCallRequest(BaseModel):
    contact_id: UUID4
    phone_id: Optional[UUID4] = None
    message_content: str
    save_as_template: bool = False
    template_name: Optional[str] = None
    dtmf_responses: List[CustomDtmfResponse] = []
    save_dtmf_responses: bool = False

class CustomSmsRequest(BaseModel):
    recipients: List[UUID4] = []
    group_id: Optional[UUID4] = None
    message_content: str
    save_as_template: bool = False
    template_name: Optional[str] = None
    schedule_time: Optional[datetime] = None
    retry_count: int = 0
    retry_delay_minutes: int = 30

class ScheduledMessageCreate(BaseModel):
    name: str
    message_id: UUID4
    recipients: List[UUID4] = []
    group_id: Optional[UUID4] = None
    message_type: str  # "call" or "sms"
    schedule_time: datetime
    recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "daily", "weekly", "monthly"
    active: bool = True

class ScheduledMessageUpdate(BaseModel):
    name: Optional[str] = None
    message_id: Optional[UUID4] = None
    recipients: Optional[List[UUID4]] = None
    group_id: Optional[UUID4] = None
    schedule_time: Optional[datetime] = None
    recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    active: Optional[bool] = None

class ScheduledMessageResponse(BaseModel):
    id: UUID4
    name: str
    message: MessageResponse
    recipients: List[ContactResponse] = []
    group: Optional[GroupBrief] = None
    message_type: str
    schedule_time: datetime
    recurring: bool
    recurrence_pattern: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime

# Burn message schemas
class BurnMessageCreate(BaseModel):
    """Schema for creating a burn message"""
    content: str
    expires_in_hours: int = 24  # Default expiration is 24 hours

class BurnMessageResponse(BaseModel):
    """Schema for returning a burn message"""
    id: UUID4
    token: str
    content: str
    created_at: datetime
    expires_at: datetime
    viewed: bool

class BurnSmsRequest(BaseModel):
    """Schema for sending an SMS with a burn message link"""
    recipients: List[UUID4] = []
    group_id: Optional[UUID4] = None
    message_content: str
    custom_link_text: Optional[str] = None
    expires_in_hours: int = 24
    base_url: Optional[str] = None
    
class BurnVoiceCallRequest(BaseModel):
    """Schema for initiating a voice call that directs to a burn message"""
    recipients: List[UUID4] = []
    group_id: Optional[UUID4] = None
    burn_content: str
    intro_message: str
    custom_link_text: Optional[str] = None
    dtmf_digit: str = "1"
    dtmf_message: Optional[str] = None
    expires_in_hours: int = 24
    base_url: Optional[str] = None