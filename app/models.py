import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, select
from sqlalchemy import JSON, Column


# Support Model.select() in tests: map to sqlmodel.select(Model)
SQLModel.select = classmethod(lambda cls: select(cls))

class OutboxJobStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class OutboxJob(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    service: str  # e.g. "rabbitmq" or "twilio"
    payload: Optional[str] = Field(default=None, sa_column=Column(JSON))  # JSON-serializable dict of args/kwargs
    attempts: int = 0
    last_error: Optional[str] = None
    status: OutboxJobStatus = Field(default=OutboxJobStatus.PENDING)

class ContactGroupMembership(SQLModel, table=True):
    """Association table for many-to-many relationship between contacts and groups"""
    contact_id: uuid.UUID = Field(foreign_key="contact.id", primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="contactgroup.id", primary_key=True)
    added_at: datetime = Field(default_factory=datetime.now)

class OutreachCampaignContactLink(SQLModel, table=True):
    """Association table for many-to-many relationship between outreach campaigns and contacts"""
    campaign_id: uuid.UUID = Field(foreign_key="outreachcampaign.id", primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id", primary_key=True)

class OutreachCampaign(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    message_id: uuid.UUID = Field(foreign_key="message.id")
    target_group_id: Optional[uuid.UUID] = Field(default=None, foreign_key="contactgroup.id")
    target_contact_count: int = Field(default=0)
    queued_contact_count: int = Field(default=0)
    status: str = Field(default="pending") # e.g., pending, queued, in_progress, completed, failed
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    initiated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    message: Optional["Message"] = Relationship(back_populates="outreach_campaigns")
    group: Optional["ContactGroup"] = Relationship(back_populates="outreach_campaigns")
    contacts: List["Contact"] = Relationship(back_populates="outreach_campaigns", link_model=OutreachCampaignContactLink, sa_relationship_kwargs={"lazy": "selectin"})

class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False, max_length=64)
    email: str = Field(index=True, unique=True, nullable=False, max_length=128)
    hashed_password: str = Field(nullable=False)
    disabled: bool = Field(default=False, nullable=False)

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
    # TODO: define contacts relationship properly later
    # contacts: List["Contact"] = Relationship(
    outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="group", sa_relationship_kwargs={"lazy": "selectin"})

class Contact(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    phone_numbers: List[PhoneNumber] = Relationship(back_populates="contact")
    # TODO: define groups relationship
    # groups: List[ContactGroup] = Relationship(
    # TODO: define scheduled_messages relationship
    # scheduled_messages: List["ScheduledMessage"] = Relationship(
    outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="contacts", link_model=OutreachCampaignContactLink, sa_relationship_kwargs={"lazy": "selectin"})

class Message(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    content: str
    is_template: bool = True
    message_type: str = "voice"  # voice, sms, or both
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message", sa_relationship_kwargs={"lazy": "selectin", "primaryjoin": "Message.id == OutreachCampaign.message_id"})
# NOTE: duplicated relationship kwargs line commented out
# sa_relationship_kwargs={"lazy": "selectin", "primaryjoin": "Message.id == OutreachCampaign.message_id"})

    def __init__(self, **data):
        # Handle string UUIDs by converting to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            try:
                data['id'] = uuid.UUID(data['id'])
            except ValueError:
                pass  # Keep original value if not a valid UUID string
        super().__init__(**data)

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
    dtmf_responses: Optional[str] = Field(default=None, sa_column=Column(JSON))  # For custom DTMF responses
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    # TODO: define recipients relationship
    # recipients: List[Contact] = Relationship(

class CustomMessageLog(SQLModel, table=True):
    """Log of custom messages (not using templates)"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    message_content: str
    message_type: str  # "call" or "sms"
    dtmf_responses: Optional[str] = Field(default=None, sa_column=Column(JSON))  # For custom DTMF responses
    created_at: datetime = Field(default_factory=datetime.now)

class SmsLog(SQLModel, table=True):
    """Log of SMS messages sent through the system"""
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    phone_number_id: uuid.UUID = Field(foreign_key="phonenumber.id")
    message_sid: str
    sent_at: datetime = Field(default_factory=datetime.now)
    status: str  # sent | failed
    error_code: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="message.id")
    retry_count: int = 0
    retry_at: Optional[datetime] = None
    is_retry: bool = False
    custom_message_log_id: Optional[uuid.UUID] = Field(default=None, foreign_key="custommessagelog.id")
    scheduled_message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="scheduledmessage.id")

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


# ============================================================================
# CRISIS MANAGEMENT MODELS - För kritisk beredskap och krishantering
# ============================================================================

class CrisisLevel(str, Enum):
    """Krisens allvarlighetsgrad för svensk regional beredskap"""
    STANDBY = "standby"           # Beredskap
    ELEVATED = "elevated"         # Förhöjd beredskap  
    EMERGENCY = "emergency"       # Nödläge
    DISASTER = "disaster"         # Katastrofläge

class PersonnelRole(str, Enum):
    """Personalroller i beredskapsorganisation"""
    CRISIS_LEADER = "crisis_leader"           # Krisledare
    DEPUTY_LEADER = "deputy_leader"           # Ställföreträdare
    OPERATIONS_CHIEF = "operations_chief"     # Operativ chef
    INFORMATION_OFFICER = "info_officer"      # Informationsansvarig
    LOGISTICS_CHIEF = "logistics_chief"       # Logistikchef
    MEDICAL_OFFICER = "medical_officer"       # Sjukvårdsansvarig
    TECHNICAL_EXPERT = "tech_expert"          # Teknisk expert
    SUPPORT_STAFF = "support_staff"           # Stödpersonal
    VOLUNTEER = "volunteer"                   # Frivillig

class CrisisActivation(SQLModel, table=True):
    """Krishantering och beredskapsaktivering"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Krisidentifikation
    crisis_name: str = Field(max_length=200)
    crisis_type: str = Field(max_length=100)  # "översvämning", "brand", "cyberattack"
    crisis_level: CrisisLevel
    geographic_area: str = Field(max_length=200)  # "Västra Götaland", "Göteborg"
    
    # Aktivering
    activated_at: datetime = Field(default_factory=datetime.now)
    activated_by_user_id: uuid.UUID = Field(foreign_key="user.id")
    expected_duration: Optional[str] = None  # "24 hours", "3 days"
    meeting_location: Optional[str] = Field(None, max_length=200)
    required_arrival_time: Optional[datetime] = None
    
    # Status
    is_active: bool = True
    resolved_at: Optional[datetime] = None
    
    # Kommunikation
    primary_message: str = Field(max_length=1000)
    urgency_level: int = Field(default=1, ge=1, le=5)  # 1=låg, 5=kritisk
    
    # Relationer
    personnel_activations: List["PersonnelActivation"] = Relationship(back_populates="crisis")
    escalations: List["ManualEscalation"] = Relationship(back_populates="crisis")
    activated_by: "User" = Relationship()

class PersonnelActivation(SQLModel, table=True):
    """Aktivering av specifik personal"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crisis_id: uuid.UUID = Field(foreign_key="crisisactivation.id")
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    
    # Rollspecifik information
    assigned_role: PersonnelRole
    priority_level: int = Field(default=3, ge=1, le=5)  # 1=kritisk, 5=låg
    required_arrival_time: Optional[datetime] = None
    meeting_location: Optional[str] = Field(None, max_length=200)
    
    # Kommunikationsstatus
    call_attempted_at: Optional[datetime] = None
    call_answered: bool = False
    call_confirmed: bool = False
    sms_sent_at: Optional[datetime] = None
    sms_confirmed: bool = False
    interactive_link_sent: bool = False
    interactive_response_received: bool = False
    interactive_message_id: Optional[uuid.UUID] = Field(None, foreign_key="interactive_messages.id")
    
    # Svar och status
    response_status: str = Field(default="pending")  # pending, confirmed, declined, unavailable
    response_received_at: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    current_location: Optional[str] = None
    availability_comment: Optional[str] = None
    
    # Eskalering
    escalated_to_manual: bool = False
    escalated_at: Optional[datetime] = None
    manual_contact_result: Optional[str] = None
    
    # Relationer
    crisis: "CrisisActivation" = Relationship(back_populates="personnel_activations")
    contact: "Contact" = Relationship()
    escalation: Optional["ManualEscalation"] = Relationship(back_populates="personnel_activation")
    interactive_message: Optional["InteractiveMessage"] = Relationship()

class ManualEscalation(SQLModel, table=True):
    """Eskalering till manuell telefonisthantering"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crisis_id: uuid.UUID = Field(foreign_key="crisisactivation.id")
    personnel_activation_id: uuid.UUID = Field(foreign_key="personnelactivation.id")
    
    # Eskaleringsinformation
    escalated_at: datetime = Field(default_factory=datetime.now)
    escalation_reason: str  # "no_answer", "no_confirmation", "technical_failure"
    attempts_made: int = Field(default=0)
    
    # Telefonisthantering
    assigned_to_operator: Optional[str] = Field(None, max_length=100)
    operator_assigned_at: Optional[datetime] = None
    contact_attempted_at: Optional[datetime] = None
    contact_successful: bool = False
    contact_result: Optional[str] = None  # "confirmed", "declined", "unreachable"
    contact_notes: Optional[str] = Field(None, max_length=500)
    resolved_at: Optional[datetime] = None
    
    # Relationer
    crisis: "CrisisActivation" = Relationship(back_populates="escalations")
    personnel_activation: "PersonnelActivation" = Relationship(back_populates="escalation")

class CrisisTemplate(SQLModel, table=True):
    """Fördefinierade mallar för olika kristyper"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Mallidentifikation
    template_name: str = Field(max_length=100)
    crisis_type: str = Field(max_length=100)
    default_crisis_level: CrisisLevel
    
    # Meddelandemallar
    call_message_template: str = Field(max_length=500)
    sms_message_template: str = Field(max_length=160)
    interactive_message_template: str = Field(max_length=1000)
    
    # Rollkonfiguration
    required_roles: str = Field(sa_column=Column(JSON))  # Lista av roller som ska aktiveras
    priority_matrix: str = Field(sa_column=Column(JSON))  # Prioriteringsmatris
    
    # Tidsgränser
    max_call_attempts: int = Field(default=3)
    call_timeout_seconds: int = Field(default=30)
    confirmation_deadline_minutes: int = Field(default=15)
    escalation_delay_minutes: int = Field(default=5)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by_user_id: uuid.UUID = Field(foreign_key="user.id")
    is_active: bool = True
    
    # Relationer
    created_by: "User" = Relationship()


class InteractiveMessage(SQLModel, table=True):
    """Interaktivt meddelande som skickas till kontakter"""
    __tablename__ = "interactive_messages"
    
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(index=True, unique=True)
    title: str
    content: str
    sender_name: Optional[str] = None
    theme_color: str = "#3B82F6"
    logo_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_responses: int = 1
    require_contact_info: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    
    # Relationer
    response_options: List["InteractiveMessageOption"] = Relationship(back_populates="message")
    responses: List["InteractiveMessageResponse"] = Relationship(back_populates="message")
    message_recipients: List["InteractiveMessageRecipient"] = Relationship(back_populates="message")


class InteractiveMessageOption(SQLModel, table=True):
    """Svarsalternativ för interaktivt meddelande"""
    __tablename__ = "interactive_message_options"
    
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="interactive_messages.id")
    option_key: str
    display_text: str
    button_color: str = "#3B82F6"
    sort_order: int = 1
    requires_comment: bool = False
    auto_reply_message: Optional[str] = None
    
    # Relationer
    message: InteractiveMessage = Relationship(back_populates="response_options")
    responses: List["InteractiveMessageResponse"] = Relationship(back_populates="selected_option")


class InteractiveMessageRecipient(SQLModel, table=True):
    """Mottagare av interaktivt meddelande"""
    __tablename__ = "interactive_message_recipients"
    
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="interactive_messages.id")
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_count: int = 0
    
    # Relationer
    message: InteractiveMessage = Relationship(back_populates="message_recipients")
    contact: Contact = Relationship()
    responses: List["InteractiveMessageResponse"] = Relationship(back_populates="recipient")


class InteractiveMessageResponse(SQLModel, table=True):
    """Svar på interaktivt meddelande"""
    __tablename__ = "interactive_message_responses"
    
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="interactive_messages.id")
    recipient_id: uuid.UUID = Field(foreign_key="interactive_message_recipients.id")
    option_id: uuid.UUID = Field(foreign_key="interactive_message_options.id")
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    user_comment: Optional[str] = None
    responded_at: datetime = Field(default_factory=datetime.now)
    
    # Relationer
    message: InteractiveMessage = Relationship(back_populates="responses")
    recipient: InteractiveMessageRecipient = Relationship(back_populates="responses")
    selected_option: InteractiveMessageOption = Relationship(back_populates="responses")
