"""
Pydantic schemas för krishantering och beredskap
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models import CrisisLevel, PersonnelRole


# ============================================================================
# REQUEST SCHEMAS - För API-anrop
# ============================================================================

class CrisisActivationCreate(BaseModel):
    """Schema för att skapa ny krisaktivering"""
    crisis_name: str = Field(..., max_length=200, description="Namn på krisen")
    crisis_type: str = Field(..., max_length=100, description="Typ av kris (översvämning, brand, etc.)")
    crisis_level: CrisisLevel = Field(..., description="Allvarlighetsgrad")
    geographic_area: str = Field(..., max_length=200, description="Geografiskt område")
    primary_message: str = Field(..., max_length=1000, description="Huvudmeddelande till personal")
    urgency_level: int = Field(default=3, ge=1, le=5, description="Brådskande nivå (1-5)")
    expected_duration: Optional[str] = Field(None, description="Förväntad varaktighet")
    meeting_location: Optional[str] = Field(None, max_length=200, description="Mötesplats")
    required_arrival_time: Optional[datetime] = Field(None, description="Krävd ankomsttid")
    
    # Målgrupper för aktivering
    target_group_ids: Optional[List[uuid.UUID]] = Field(None, description="Specifika grupper att aktivera")
    target_contact_ids: Optional[List[uuid.UUID]] = Field(None, description="Specifika kontakter att aktivera")
    target_roles: Optional[List[PersonnelRole]] = Field(None, description="Specifika roller att aktivera")
    
    # Kommunikationsinställningar
    use_voice_calls: bool = Field(True, description="Använd röstsamtal")
    use_sms: bool = Field(True, description="Använd SMS")
    use_interactive_links: bool = Field(True, description="Använd interaktiva länkar")
    max_escalation_time_minutes: int = Field(15, ge=1, le=60, description="Max tid innan eskalering")

class CrisisActivationUpdate(BaseModel):
    """Schema för att uppdatera befintlig krisaktivering"""
    crisis_name: Optional[str] = Field(None, max_length=200)
    primary_message: Optional[str] = Field(None, max_length=1000)
    urgency_level: Optional[int] = Field(None, ge=1, le=5)
    expected_duration: Optional[str] = None
    meeting_location: Optional[str] = Field(None, max_length=200)
    required_arrival_time: Optional[datetime] = None
    is_active: Optional[bool] = None

class PersonnelActivationUpdate(BaseModel):
    """Schema för att uppdatera personalaktivering"""
    response_status: Optional[str] = Field(None, description="pending, confirmed, declined, unavailable")
    estimated_arrival: Optional[datetime] = None
    current_location: Optional[str] = None
    availability_comment: Optional[str] = None

class ManualEscalationUpdate(BaseModel):
    """Schema för att uppdatera manuell eskalering"""
    assigned_to_operator: Optional[str] = Field(None, max_length=100)
    contact_result: Optional[str] = Field(None, description="confirmed, declined, unreachable")
    contact_notes: Optional[str] = Field(None, max_length=500)
    contact_successful: Optional[bool] = None

class CrisisTemplateCreate(BaseModel):
    """Schema för att skapa krismall"""
    template_name: str = Field(..., max_length=100)
    crisis_type: str = Field(..., max_length=100)
    default_crisis_level: CrisisLevel
    call_message_template: str = Field(..., max_length=500)
    sms_message_template: str = Field(..., max_length=160)
    interactive_message_template: str = Field(..., max_length=1000)
    required_roles: List[PersonnelRole] = Field(..., description="Roller som ska aktiveras")
    priority_matrix: Dict[str, int] = Field(..., description="Prioriteringsmatris för roller")
    max_call_attempts: int = Field(3, ge=1, le=10)
    call_timeout_seconds: int = Field(30, ge=10, le=120)
    confirmation_deadline_minutes: int = Field(15, ge=1, le=60)
    escalation_delay_minutes: int = Field(5, ge=1, le=30)


# ============================================================================
# RESPONSE SCHEMAS - För API-svar
# ============================================================================

class PersonnelActivationResponse(BaseModel):
    """Schema för personalaktivering i API-svar"""
    id: uuid.UUID
    contact_id: uuid.UUID
    assigned_role: PersonnelRole
    priority_level: int
    response_status: str
    call_attempted_at: Optional[datetime] = None
    call_confirmed: bool = False
    sms_sent_at: Optional[datetime] = None
    sms_confirmed: bool = False
    interactive_link_sent: bool = False
    interactive_response_received: bool = False
    response_received_at: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    escalated_to_manual: bool = False
    escalated_at: Optional[datetime] = None
    
    # Kontaktinformation (joined data)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

    class Config:
        from_attributes = True

class ManualEscalationResponse(BaseModel):
    """Schema för manuell eskalering i API-svar"""
    id: uuid.UUID
    personnel_activation_id: uuid.UUID
    escalated_at: datetime
    escalation_reason: str
    attempts_made: int
    assigned_to_operator: Optional[str] = None
    operator_assigned_at: Optional[datetime] = None
    contact_successful: bool = False
    contact_result: Optional[str] = None
    contact_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Personalinformation (joined data)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    assigned_role: Optional[PersonnelRole] = None

    class Config:
        from_attributes = True

class CrisisActivationResponse(BaseModel):
    """Schema för krisaktivering i API-svar"""
    id: uuid.UUID
    crisis_name: str
    crisis_type: str
    crisis_level: CrisisLevel
    geographic_area: str
    activated_at: datetime
    activated_by_user_id: uuid.UUID
    expected_duration: Optional[str] = None
    meeting_location: Optional[str] = None
    required_arrival_time: Optional[datetime] = None
    is_active: bool
    resolved_at: Optional[datetime] = None
    primary_message: str
    urgency_level: int
    
    # Statistik
    total_personnel: int = 0
    confirmed_personnel: int = 0
    pending_personnel: int = 0
    escalated_personnel: int = 0
    
    # Aktiverad av (joined data)
    activated_by_username: Optional[str] = None

    class Config:
        from_attributes = True

class CrisisTemplateResponse(BaseModel):
    """Schema för krismall i API-svar"""
    id: uuid.UUID
    template_name: str
    crisis_type: str
    default_crisis_level: CrisisLevel
    call_message_template: str
    sms_message_template: str
    interactive_message_template: str
    required_roles: List[PersonnelRole]
    priority_matrix: Dict[str, int]
    max_call_attempts: int
    call_timeout_seconds: int
    confirmation_deadline_minutes: int
    escalation_delay_minutes: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD SCHEMAS - För realtids-dashboard
# ============================================================================

class RoleStatusSummary(BaseModel):
    """Sammanfattning av status per roll"""
    role: PersonnelRole
    total: int = 0
    confirmed: int = 0
    declined: int = 0
    pending: int = 0
    escalated: int = 0
    confirmation_rate: float = 0.0

class CommunicationEvent(BaseModel):
    """Kommunikationshändelse för tidslinje"""
    time: datetime
    event_type: str  # "call_attempted", "sms_sent", "interactive_sent", "response_received"
    contact_id: uuid.UUID
    contact_name: str
    success: bool
    details: Optional[str] = None

class CriticalGap(BaseModel):
    """Kritisk lucka i personalstyrkan"""
    role: PersonnelRole
    severity: str  # "critical", "warning", "info"
    message: str
    missing_count: int
    required_count: int

class CrisisDashboardData(BaseModel):
    """Komplett dashboard-data för kris"""
    crisis: CrisisActivationResponse
    
    # Övergripande statistik
    statistics: Dict[str, Any] = {
        "total_personnel": 0,
        "confirmed": 0,
        "declined": 0,
        "pending": 0,
        "escalated": 0,
        "confirmation_rate": 0.0,
        "escalation_rate": 0.0,
        "average_response_time_minutes": 0.0
    }
    
    # Rollfördelning
    role_breakdown: List[RoleStatusSummary] = []
    
    # Kommunikationstidslinje (senaste händelser)
    communication_timeline: List[CommunicationEvent] = []
    
    # Kritiska luckor
    critical_gaps: List[CriticalGap] = []
    
    # Eskaleringar som väntar på telefonister
    pending_escalations: List[ManualEscalationResponse] = []
    
    # Estimerad tid till full aktivering
    estimated_full_activation_minutes: Optional[int] = None
    
    # Senast uppdaterad
    last_updated: datetime = Field(default_factory=datetime.now)

class OperatorWorkload(BaseModel):
    """Arbetsbelastning för telefonist"""
    operator_name: str
    active_escalations: int = 0
    completed_today: int = 0
    success_rate: float = 0.0
    average_resolution_minutes: float = 0.0

class OperatorDashboardData(BaseModel):
    """Dashboard-data för telefonister"""
    # Väntande eskaleringar
    pending_escalations: List[ManualEscalationResponse] = []
    
    # Operatörsbelastning
    operator_workloads: List[OperatorWorkload] = []
    
    # Statistik för dagen
    daily_stats: Dict[str, Any] = {
        "total_escalations": 0,
        "resolved_escalations": 0,
        "success_rate": 0.0,
        "average_resolution_time_minutes": 0.0
    }
    
    # Aktiva kriser
    active_crises: List[CrisisActivationResponse] = []


# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class CrisisActivationListResponse(BaseModel):
    """Lista av krisaktivering för översikt"""
    crises: List[CrisisActivationResponse]
    total_count: int
    active_count: int
    resolved_count: int

class PersonnelActivationListResponse(BaseModel):
    """Lista av personalaktiveringar"""
    personnel_activations: List[PersonnelActivationResponse]
    total_count: int
    confirmed_count: int
    pending_count: int
    escalated_count: int

class BulkPersonnelUpdate(BaseModel):
    """Bulk-uppdatering av flera personalaktiveringar"""
    updates: List[Dict[str, Any]]  # Lista av {"personnel_activation_id": uuid, "update_data": PersonnelActivationUpdate}

class CrisisStatistics(BaseModel):
    """Statistik för krishantering"""
    period_start: datetime
    period_end: datetime
    total_crises: int
    crises_by_level: Dict[str, int]
    crises_by_type: Dict[str, int]
    average_activation_time_minutes: float
    average_confirmation_rate: float
    total_personnel_activated: int
    total_escalations: int
    escalation_rate: float
