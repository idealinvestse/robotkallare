"""
API endpoints för krishantering och beredskap
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session

from app.database import get_session
from app.models import User, CrisisActivation, PersonnelActivation, ManualEscalation
from app.schemas.crisis_management import (
    CrisisActivationCreate, CrisisActivationUpdate, CrisisActivationResponse,
    PersonnelActivationUpdate, PersonnelActivationResponse,
    ManualEscalationUpdate, ManualEscalationResponse,
    CrisisDashboardData, CrisisActivationListResponse,
    PersonnelActivationListResponse, CrisisTemplateCreate, CrisisTemplateResponse
)
from app.services.crisis_management_service import CrisisManagementService
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.services.call_service import CallService
from app.services.sms_service import SmsService
from app.services.interactive_message_service import InteractiveMessageService

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crisis", tags=["Crisis Management"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_crisis_management_service(session: Session = Depends(get_session)) -> CrisisManagementService:
    """Dependency injection för CrisisManagementService"""
    contact_repo = ContactRepository(session)
    group_repo = GroupRepository(session)
    call_service = CallService()
    sms_service = SmsService()
    interactive_service = InteractiveMessageService(session)
    
    return CrisisManagementService(
        session=session,
        contact_repo=contact_repo,
        group_repo=group_repo,
        call_service=call_service,
        sms_service=sms_service,
        interactive_service=interactive_service
    )

def get_current_user() -> User:
    """Placeholder för användarautentisering"""
    # TODO: Implementera riktig autentisering
    return User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@example.com",
        hashed_password="dummy",
        disabled=False
    )


# ============================================================================
# KRISAKTIVERING - Huvudendpoints
# ============================================================================

@router.post("/activate", response_model=CrisisActivationResponse, status_code=status.HTTP_201_CREATED)
async def activate_crisis(
    crisis_data: CrisisActivationCreate,
    background_tasks: BackgroundTasks,
    service: CrisisManagementService = Depends(get_crisis_management_service),
    current_user: User = Depends(get_current_user)
):
    """
    🚨 AKTIVERA KRISHANTERING
    
    Startar automatisk inkallning av beredskapsorganisation enligt
    fördefinierade mallar baserat på kristyp och allvarlighetsgrad.
    
    **Automatisk sekvens:**
    1. Identifiera personal baserat på krisnivå och roller
    2. Starta kommunikation enligt prioritet (röst → SMS → interaktiv länk)
    3. Automatisk eskalering till telefonister för obekräftade
    4. Realtidsövervakning via dashboard
    
    **Krisnivåer:**
    - `standby`: Beredskap (krisledare + ställföreträdare)
    - `elevated`: Förhöjd beredskap (+ operativ chef, information)
    - `emergency`: Nödläge (+ logistik, sjukvård, teknik)
    - `disaster`: Katastrofläge (alla roller aktiveras)
    """
    try:
        # Aktivera krisen i bakgrunden för snabb respons
        crisis = await service.activate_crisis_response(crisis_data, current_user.id)
        
        # Logga kritisk händelse
        logger.critical(
            f"CRISIS ACTIVATED by {current_user.username}: {crisis.crisis_name} "
            f"(Level: {crisis.crisis_level}, Area: {crisis.geographic_area})"
        )
        
        return CrisisActivationResponse(
            id=crisis.id,
            crisis_name=crisis.crisis_name,
            crisis_type=crisis.crisis_type,
            crisis_level=crisis.crisis_level,
            geographic_area=crisis.geographic_area,
            activated_at=crisis.activated_at,
            activated_by_user_id=crisis.activated_by_user_id,
            expected_duration=crisis.expected_duration,
            meeting_location=crisis.meeting_location,
            required_arrival_time=crisis.required_arrival_time,
            is_active=crisis.is_active,
            resolved_at=crisis.resolved_at,
            primary_message=crisis.primary_message,
            urgency_level=crisis.urgency_level,
            activated_by_username=current_user.username
        )
        
    except Exception as e:
        logger.error(f"Failed to activate crisis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crisis activation failed: {str(e)}"
        )

@router.get("/", response_model=CrisisActivationListResponse)
async def list_crises(
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    service: CrisisManagementService = Depends(get_crisis_management_service)
):
    """
    📋 LISTA KRISER
    
    Hämta lista över alla kriser med möjlighet att filtrera på aktiva.
    """
    try:
        session = service.session
        query = session.query(CrisisActivation)
        
        if active_only:
            query = query.filter(CrisisActivation.is_active == True)
        
        total_count = query.count()
        crises = query.offset(offset).limit(limit).all()
        
        active_count = session.query(CrisisActivation).filter(CrisisActivation.is_active == True).count()
        resolved_count = total_count - active_count
        
        crisis_responses = []
        for crisis in crises:
            # Lägg till statistik för varje kris
            personnel_count = session.query(PersonnelActivation).filter(
                PersonnelActivation.crisis_id == crisis.id
            ).count()
            
            confirmed_count = session.query(PersonnelActivation).filter(
                PersonnelActivation.crisis_id == crisis.id,
                PersonnelActivation.response_status == "confirmed"
            ).count()
            
            crisis_response = CrisisActivationResponse(
                id=crisis.id,
                crisis_name=crisis.crisis_name,
                crisis_type=crisis.crisis_type,
                crisis_level=crisis.crisis_level,
                geographic_area=crisis.geographic_area,
                activated_at=crisis.activated_at,
                activated_by_user_id=crisis.activated_by_user_id,
                expected_duration=crisis.expected_duration,
                meeting_location=crisis.meeting_location,
                required_arrival_time=crisis.required_arrival_time,
                is_active=crisis.is_active,
                resolved_at=crisis.resolved_at,
                primary_message=crisis.primary_message,
                urgency_level=crisis.urgency_level,
                total_personnel=personnel_count,
                confirmed_personnel=confirmed_count
            )
            crisis_responses.append(crisis_response)
        
        return CrisisActivationListResponse(
            crises=crisis_responses,
            total_count=total_count,
            active_count=active_count,
            resolved_count=resolved_count
        )
        
    except Exception as e:
        logger.error(f"Failed to list crises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crises: {str(e)}"
        )

@router.get("/{crisis_id}", response_model=CrisisActivationResponse)
async def get_crisis(
    crisis_id: uuid.UUID,
    service: CrisisManagementService = Depends(get_crisis_management_service)
):
    """
    🔍 HÄMTA SPECIFIK KRIS
    
    Hämta detaljerad information om en specifik kris.
    """
    try:
        session = service.session
        crisis = session.get(CrisisActivation, crisis_id)
        
        if not crisis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crisis not found"
            )
        
        # Lägg till statistik
        personnel_count = session.query(PersonnelActivation).filter(
            PersonnelActivation.crisis_id == crisis.id
        ).count()
        
        confirmed_count = session.query(PersonnelActivation).filter(
            PersonnelActivation.crisis_id == crisis.id,
            PersonnelActivation.response_status == "confirmed"
        ).count()
        
        pending_count = session.query(PersonnelActivation).filter(
            PersonnelActivation.crisis_id == crisis.id,
            PersonnelActivation.response_status == "pending"
        ).count()
        
        escalated_count = session.query(PersonnelActivation).filter(
            PersonnelActivation.crisis_id == crisis.id,
            PersonnelActivation.escalated_to_manual == True
        ).count()
        
        return CrisisActivationResponse(
            id=crisis.id,
            crisis_name=crisis.crisis_name,
            crisis_type=crisis.crisis_type,
            crisis_level=crisis.crisis_level,
            geographic_area=crisis.geographic_area,
            activated_at=crisis.activated_at,
            activated_by_user_id=crisis.activated_by_user_id,
            expected_duration=crisis.expected_duration,
            meeting_location=crisis.meeting_location,
            required_arrival_time=crisis.required_arrival_time,
            is_active=crisis.is_active,
            resolved_at=crisis.resolved_at,
            primary_message=crisis.primary_message,
            urgency_level=crisis.urgency_level,
            total_personnel=personnel_count,
            confirmed_personnel=confirmed_count,
            pending_personnel=pending_count,
            escalated_personnel=escalated_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crisis {crisis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crisis: {str(e)}"
        )


# ============================================================================
# DASHBOARD - Realtidsövervakning
# ============================================================================

@router.get("/{crisis_id}/dashboard", response_model=CrisisDashboardData)
async def get_crisis_dashboard(
    crisis_id: uuid.UUID,
    service: CrisisManagementService = Depends(get_crisis_management_service)
):
    """
    📊 KRISDASHBOARD
    
    Hämta komplett realtidsdata för krisdashboard:
    - Övergripande statistik (bekräftade, väntande, eskalerade)
    - Rollfördelning och status per personaltyp
    - Kommunikationstidslinje (senaste händelser)
    - Kritiska luckor i personalstyrkan
    - Väntande eskaleringar för telefonister
    - Estimerad tid till full aktivering
    """
    try:
        dashboard_data = service.get_crisis_dashboard_data(crisis_id)
        return dashboard_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard for crisis {crisis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )

@router.put("/{crisis_id}", response_model=CrisisActivationResponse)
async def update_crisis(
    crisis_id: uuid.UUID,
    update_data: CrisisActivationUpdate,
    service: CrisisManagementService = Depends(get_crisis_management_service),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ UPPDATERA KRIS
    
    Uppdatera information om pågående kris.
    """
    try:
        session = service.session
        crisis = session.get(CrisisActivation, crisis_id)
        
        if not crisis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crisis not found"
            )
        
        # Uppdatera fält
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(crisis, field, value)
        
        session.commit()
        session.refresh(crisis)
        
        logger.info(f"Crisis {crisis_id} updated by {current_user.username}")
        
        return CrisisActivationResponse(
            id=crisis.id,
            crisis_name=crisis.crisis_name,
            crisis_type=crisis.crisis_type,
            crisis_level=crisis.crisis_level,
            geographic_area=crisis.geographic_area,
            activated_at=crisis.activated_at,
            activated_by_user_id=crisis.activated_by_user_id,
            expected_duration=crisis.expected_duration,
            meeting_location=crisis.meeting_location,
            required_arrival_time=crisis.required_arrival_time,
            is_active=crisis.is_active,
            resolved_at=crisis.resolved_at,
            primary_message=crisis.primary_message,
            urgency_level=crisis.urgency_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update crisis {crisis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update crisis: {str(e)}"
        )

@router.post("/{crisis_id}/resolve")
async def resolve_crisis(
    crisis_id: uuid.UUID,
    service: CrisisManagementService = Depends(get_crisis_management_service),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ AVSLUTA KRIS
    
    Markera kris som avslutad och stoppa alla pågående aktiviteter.
    """
    try:
        session = service.session
        crisis = session.get(CrisisActivation, crisis_id)
        
        if not crisis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crisis not found"
            )
        
        if not crisis.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crisis is already resolved"
            )
        
        crisis.is_active = False
        crisis.resolved_at = datetime.now()
        
        session.commit()
        
        logger.critical(f"Crisis {crisis.crisis_name} resolved by {current_user.username}")
        
        return {"message": "Crisis resolved successfully", "resolved_at": crisis.resolved_at}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve crisis {crisis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve crisis: {str(e)}"
        )


# ============================================================================
# PERSONALHANTERING
# ============================================================================

@router.get("/{crisis_id}/personnel", response_model=PersonnelActivationListResponse)
async def get_crisis_personnel(
    crisis_id: uuid.UUID,
    role_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    service: CrisisManagementService = Depends(get_crisis_management_service)
):
    """
    👥 HÄMTA PERSONAL
    
    Hämta lista över all aktiverad personal för en kris.
    """
    try:
        session = service.session
        
        # Kontrollera att krisen finns
        crisis = session.get(CrisisActivation, crisis_id)
        if not crisis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crisis not found"
            )
        
        # Bygg query
        query = session.query(PersonnelActivation).filter(
            PersonnelActivation.crisis_id == crisis_id
        )
        
        if role_filter:
            query = query.filter(PersonnelActivation.assigned_role == role_filter)
        
        if status_filter:
            query = query.filter(PersonnelActivation.response_status == status_filter)
        
        activations = query.all()
        
        # Beräkna statistik
        total_count = len(activations)
        confirmed_count = len([a for a in activations if a.response_status == "confirmed"])
        pending_count = len([a for a in activations if a.response_status == "pending"])
        escalated_count = len([a for a in activations if a.escalated_to_manual])
        
        # Konvertera till response format
        personnel_responses = []
        for activation in activations:
            contact = session.get(Contact, activation.contact_id)
            phone = contact.phone_numbers[0].number if contact and contact.phone_numbers else None
            
            personnel_responses.append(PersonnelActivationResponse(
                id=activation.id,
                contact_id=activation.contact_id,
                assigned_role=activation.assigned_role,
                priority_level=activation.priority_level,
                response_status=activation.response_status,
                call_attempted_at=activation.call_attempted_at,
                call_confirmed=activation.call_confirmed,
                sms_sent_at=activation.sms_sent_at,
                sms_confirmed=activation.sms_confirmed,
                interactive_link_sent=activation.interactive_link_sent,
                interactive_response_received=activation.interactive_response_received,
                response_received_at=activation.response_received_at,
                estimated_arrival=activation.estimated_arrival,
                escalated_to_manual=activation.escalated_to_manual,
                escalated_at=activation.escalated_at,
                contact_name=contact.name if contact else None,
                contact_phone=phone
            ))
        
        return PersonnelActivationListResponse(
            personnel_activations=personnel_responses,
            total_count=total_count,
            confirmed_count=confirmed_count,
            pending_count=pending_count,
            escalated_count=escalated_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get personnel for crisis {crisis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve personnel: {str(e)}"
        )

@router.put("/personnel/{activation_id}", response_model=PersonnelActivationResponse)
async def update_personnel_activation(
    activation_id: uuid.UUID,
    update_data: PersonnelActivationUpdate,
    service: CrisisManagementService = Depends(get_crisis_management_service),
    current_user: User = Depends(get_current_user)
):
    """
    ✏️ UPPDATERA PERSONALSTATUS
    
    Uppdatera status för en specifik personalaktivering.
    """
    try:
        session = service.session
        activation = session.get(PersonnelActivation, activation_id)
        
        if not activation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Personnel activation not found"
            )
        
        # Uppdatera fält
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(activation, field, value)
        
        # Sätt response_received_at om status ändras
        if "response_status" in update_dict and activation.response_status != "pending":
            activation.response_received_at = datetime.now()
        
        session.commit()
        session.refresh(activation)
        
        logger.info(f"Personnel activation {activation_id} updated by {current_user.username}")
        
        # Returnera uppdaterad data
        contact = session.get(Contact, activation.contact_id)
        phone = contact.phone_numbers[0].number if contact and contact.phone_numbers else None
        
        return PersonnelActivationResponse(
            id=activation.id,
            contact_id=activation.contact_id,
            assigned_role=activation.assigned_role,
            priority_level=activation.priority_level,
            response_status=activation.response_status,
            call_attempted_at=activation.call_attempted_at,
            call_confirmed=activation.call_confirmed,
            sms_sent_at=activation.sms_sent_at,
            sms_confirmed=activation.sms_confirmed,
            interactive_link_sent=activation.interactive_link_sent,
            interactive_response_received=activation.interactive_response_received,
            response_received_at=activation.response_received_at,
            estimated_arrival=activation.estimated_arrival,
            escalated_to_manual=activation.escalated_to_manual,
            escalated_at=activation.escalated_at,
            contact_name=contact.name if contact else None,
            contact_phone=phone
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update personnel activation {activation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update personnel activation: {str(e)}"
        )


# ============================================================================
# ESKALERING OCH TELEFONISTHANTERING
# ============================================================================

@router.get("/escalations/pending", response_model=List[ManualEscalationResponse])
async def get_pending_escalations(
    operator_filter: Optional[str] = None,
    service: CrisisManagementService = Depends(get_crisis_management_service)
):
    """
    📞 VÄNTANDE ESKALERINGAR
    
    Hämta alla eskaleringar som väntar på manuell telefonisthantering.
    """
    try:
        session = service.session
        
        query = session.query(ManualEscalation).filter(
            ManualEscalation.resolved_at.is_(None)
        )
        
        if operator_filter:
            query = query.filter(ManualEscalation.assigned_to_operator == operator_filter)
        
        escalations = query.order_by(ManualEscalation.escalated_at.desc()).all()
        
        escalation_responses = []
        for escalation in escalations:
            # Hämta personalaktivering och kontakt
            activation = session.get(PersonnelActivation, escalation.personnel_activation_id)
            contact = session.get(Contact, activation.contact_id) if activation else None
            phone = contact.phone_numbers[0].number if contact and contact.phone_numbers else None
            
            escalation_responses.append(ManualEscalationResponse(
                id=escalation.id,
                personnel_activation_id=escalation.personnel_activation_id,
                escalated_at=escalation.escalated_at,
                escalation_reason=escalation.escalation_reason,
                attempts_made=escalation.attempts_made,
                assigned_to_operator=escalation.assigned_to_operator,
                operator_assigned_at=escalation.operator_assigned_at,
                contact_successful=escalation.contact_successful,
                contact_result=escalation.contact_result,
                contact_notes=escalation.contact_notes,
                resolved_at=escalation.resolved_at,
                contact_name=contact.name if contact else None,
                contact_phone=phone,
                assigned_role=activation.assigned_role if activation else None
            ))
        
        return escalation_responses
        
    except Exception as e:
        logger.error(f"Failed to get pending escalations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve escalations: {str(e)}"
        )

@router.put("/escalations/{escalation_id}", response_model=ManualEscalationResponse)
async def update_escalation(
    escalation_id: uuid.UUID,
    update_data: ManualEscalationUpdate,
    service: CrisisManagementService = Depends(get_crisis_management_service),
    current_user: User = Depends(get_current_user)
):
    """
    📞 UPPDATERA ESKALERING
    
    Uppdatera status för manuell eskalering (för telefonister).
    """
    try:
        session = service.session
        escalation = session.get(ManualEscalation, escalation_id)
        
        if not escalation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Escalation not found"
            )
        
        # Uppdatera fält
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(escalation, field, value)
        
        # Sätt resolved_at om kontakt är slutförd
        if update_data.contact_successful is not None:
            escalation.contact_attempted_at = datetime.now()
            if update_data.contact_successful:
                escalation.resolved_at = datetime.now()
                
                # Uppdatera även personalaktivering
                activation = session.get(PersonnelActivation, escalation.personnel_activation_id)
                if activation and update_data.contact_result:
                    activation.response_status = update_data.contact_result
                    activation.response_received_at = datetime.now()
                    activation.manual_contact_result = update_data.contact_result
        
        session.commit()
        session.refresh(escalation)
        
        logger.info(f"Escalation {escalation_id} updated by {current_user.username}")
        
        # Returnera uppdaterad data
        activation = session.get(PersonnelActivation, escalation.personnel_activation_id)
        contact = session.get(Contact, activation.contact_id) if activation else None
        phone = contact.phone_numbers[0].number if contact and contact.phone_numbers else None
        
        return ManualEscalationResponse(
            id=escalation.id,
            personnel_activation_id=escalation.personnel_activation_id,
            escalated_at=escalation.escalated_at,
            escalation_reason=escalation.escalation_reason,
            attempts_made=escalation.attempts_made,
            assigned_to_operator=escalation.assigned_to_operator,
            operator_assigned_at=escalation.operator_assigned_at,
            contact_successful=escalation.contact_successful,
            contact_result=escalation.contact_result,
            contact_notes=escalation.contact_notes,
            resolved_at=escalation.resolved_at,
            contact_name=contact.name if contact else None,
            contact_phone=phone,
            assigned_role=activation.assigned_role if activation else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update escalation {escalation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update escalation: {str(e)}"
        )
