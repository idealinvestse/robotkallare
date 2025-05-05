"""Core database models for GDial

This module defines the primary database models like Contact, Message, etc.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, Relationship, select
from sqlalchemy import Column, JSON

# Convenience classmethods to support model.select() and model.where() in tests
SQLModel.select = classmethod(lambda cls: select(cls))
SQLModel.where = classmethod(lambda cls, condition: select(cls).where(condition))

class GroupContactLink(SQLModel, table=True):
    """Association table for many-to-many relationship between groups and contacts"""
    group_id: uuid.UUID = Field(foreign_key="contactgroup.id", primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id", primary_key=True)

class ScheduledMessageContactLink(SQLModel, table=True):
    """Association table for many-to-many relationship between scheduled messages and contacts"""
    scheduled_message_id: uuid.UUID = Field(foreign_key="scheduledmessage.id", primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id", primary_key=True)

class CallRun(SQLModel, table=True):
    """A batch of calls made together as part of a single operation"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="message.id")
    group_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contactgroup.id")
    scheduled_message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="scheduledmessage.id")
    status: str = "in_progress"  # in_progress, completed, cancelled
    total_calls: int = 0
    completed_calls: int = 0
    answered_calls: int = 0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    custom_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    calls: List["CallLog"] = Relationship(back_populates="call_run")

class PhoneNumber(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    number: str
    priority: int
    contact: "Contact" = Relationship(back_populates="phone_numbers")

class ContactGroup(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    contacts: List["Contact"] = Relationship(
        back_populates="groups",
        link_model=GroupContactLink,
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    
class Contact(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    phone_numbers: List[PhoneNumber] = Relationship(back_populates="contact")
    groups: List[ContactGroup] = Relationship(
        back_populates="contacts",
        link_model=GroupContactLink,
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    scheduled_messages: List["ScheduledMessage"] = Relationship(
        back_populates="recipients",
        link_model=ScheduledMessageContactLink,
        sa_relationship_kwargs={"lazy": "selectin"}
    )

class Message(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    content: str
    is_template: bool = True
    message_type: str = "voice"  # voice, sms, or both
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DtmfResponse(SQLModel, table=True):
    """Configurable DTMF response messages for the system"""
    digit: str = Field(primary_key=True, max_length=1)  # 1, 2, 3, etc.
    description: str  # Description of what this button means
    response_message: str  # Message to say when this button is pressed
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def get_response(cls, session, digit: str) -> Optional[str]:
        """Get response message for a specific digit"""
        response = session.exec(select(cls).where(cls.digit == digit)).first()
        if response:
            return response.response_message
        return None

class SmsLog(SQLModel, table=True):
    """Log of SMS messages sent through the system"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    phone_number_id: uuid.UUID = Field(foreign_key="phonenumber.id")
    message_sid: str
    sent_at: datetime = Field(default_factory=datetime.now)
    status: str  # sent | failed
    message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="message.id")
    retry_count: int = 0
    retry_at: Optional[datetime] = None
    is_retry: bool = False
    custom_message_log_id: Optional[uuid.UUID] = Field(default=None, foreign_key="custommessagelog.id")
    scheduled_message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="scheduledmessage.id")

class ScheduledMessage(SQLModel, table=True):
    """Scheduled messages for future delivery"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    message_id: uuid.UUID = Field(foreign_key="message.id")
    group_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contactgroup.id")
    message_type: str  # "call" or "sms"
    schedule_time: datetime
    recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "daily", "weekly", "monthly"
    dtmf_responses: Optional[Dict] = Field(default=None, sa_column=Column(JSON))  # For custom DTMF responses
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    recipients: List[Contact] = Relationship(
        back_populates="scheduled_messages",
        link_model=ScheduledMessageContactLink,
        sa_relationship_kwargs={"lazy": "selectin"}
    )

class CustomMessageLog(SQLModel, table=True):
    """Log of custom messages (not using templates)"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    message_content: str
    message_type: str  # "call" or "sms"
    dtmf_responses: Optional[Dict] = Field(default=None, sa_column=Column(JSON))  # For custom DTMF responses
    created_at: datetime = Field(default_factory=datetime.now)

class CallLog(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    phone_number_id: uuid.UUID = Field(foreign_key="phonenumber.id")
    call_sid: str
    started_at: datetime
    answered: bool = False
    digits: Optional[str] = Field(default=None, max_length=1)
    status: str  # initiated | completed | no-answer | manual | error | custom
    message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="message.id")
    custom_message_log_id: Optional[uuid.UUID] = Field(default=None, foreign_key="custommessagelog.id")
    scheduled_message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="scheduledmessage.id")
    call_run_id: Optional[uuid.UUID] = Field(default=None, foreign_key="callrun.id")
    custom_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    call_run: Optional["CallRun"] = Relationship(back_populates="calls")

class BurnMessage(SQLModel, table=True):
    """Temporary messages that can be viewed once and then deleted"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(index=True)  # Unique token for the message URL
    content: str  # Content of the message
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime  # When the message should expire
    viewed: bool = False  # Whether the message has been viewed
    viewed_at: Optional[datetime] = None  # When the message was viewed
    created_by_contact_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contact.id")
    sms_log_id: Optional[uuid.UUID] = Field(default=None, foreign_key="smslog.id")