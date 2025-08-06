"""
Service för krishantering och beredskap
Hanterar automatisk aktivering, kommunikationssekvenser och eskalering
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import (
    CrisisActivation, PersonnelActivation, ManualEscalation, CrisisTemplate,
    Contact, ContactGroup, User, InteractiveMessage,
    CrisisLevel, PersonnelRole
)
from app.schemas.crisis_management import (
    CrisisActivationCreate, CrisisActivationUpdate, PersonnelActivationUpdate,
    ManualEscalationUpdate, CrisisDashboardData, CommunicationEvent,
    RoleStatusSummary, CriticalGap, OperatorDashboardData
)
from app.schemas.interactive_messages import InteractiveMessageCreate
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.services.call_service import CallService
from app.services.sms_service import SmsService
from app.services.interactive_message_service import InteractiveMessageService

import logging
logger = logging.getLogger(__name__)


class CrisisManagementService:
    """Service för hantering av kritiska beredskapslägen"""
    
    def __init__(
        self,
        session: Session,
        contact_repo: ContactRepository,
        group_repo: GroupRepository,
        call_service: CallService,
        sms_service: SmsService,
        interactive_service: InteractiveMessageService
    ):
        self.session = session
        self.contact_repo = contact_repo
        self.group_repo = group_repo
        self.call_service = call_service
        self.sms_service = sms_service
        self.interactive_service = interactive_service
    
    async def activate_crisis_response(
        self,
        crisis_data: CrisisActivationCreate,
        user_id: uuid.UUID
    ) -> CrisisActivation:
        """Aktivera krishantering med automatisk personalinkallning"""
        
        # 1. Skapa krisaktivering
        crisis = CrisisActivation(
            crisis_name=crisis_data.crisis_name,
            crisis_type=crisis_data.crisis_type,
            crisis_level=crisis_data.crisis_level,
            geographic_area=crisis_data.geographic_area,
            primary_message=crisis_data.primary_message,
            urgency_level=crisis_data.urgency_level,
            activated_by_user_id=user_id,
            expected_duration=crisis_data.expected_duration,
            meeting_location=crisis_data.meeting_location,
            required_arrival_time=crisis_data.required_arrival_time
        )
        
        self.session.add(crisis)
        self.session.commit()
        self.session.refresh(crisis)
        
        # 2. Identifiera och aktivera personal
        await self._activate_personnel_by_crisis_level(crisis, crisis_data)
        
        # 3. Starta kommunikationssekvens
        await self._initiate_communication_sequence(crisis, crisis_data)
        
        # 4. Sätt upp eskalering
        asyncio.create_task(self._schedule_escalation_monitoring(crisis, crisis_data.max_escalation_time_minutes))
        
        logger.critical(f"Crisis activated: {crisis.crisis_name} (Level: {crisis.crisis_level})")
        return crisis
    
    async def _activate_personnel_by_crisis_level(
        self, 
        crisis: CrisisActivation, 
        crisis_data: CrisisActivationCreate
    ):
        """Aktivera personal baserat på krisens allvarlighetsgrad"""
        
        role_priorities = self._get_role_priorities_for_crisis_level(crisis.crisis_level)
        
        # Hämta målkontakter
        target_contacts = []
        if crisis_data.target_contact_ids:
            target_contacts = self.contact_repo.get_contacts_by_ids(crisis_data.target_contact_ids)
        elif crisis_data.target_group_ids:
            for group_id in crisis_data.target_group_ids:
                group_contacts = self.group_repo.get_contacts_by_group_id(group_id)
                target_contacts.extend(group_contacts)
        else:
            target_contacts = await self._get_all_emergency_personnel()
        
        # Aktivera personal enligt prioritet och roll
        for role, priority in role_priorities:
            role_contacts = await self._get_contacts_by_role(role, target_contacts)
            
            for contact in role_contacts:
                activation = PersonnelActivation(
                    crisis_id=crisis.id,
                    contact_id=contact.id,
                    assigned_role=role,
                    priority_level=priority,
                    meeting_location=crisis_data.meeting_location,
                    required_arrival_time=crisis_data.required_arrival_time
                )
                self.session.add(activation)
        
        self.session.commit()
        logger.info(f"Activated {len(target_contacts)} personnel for crisis {crisis.crisis_name}")
    
    def _get_role_priorities_for_crisis_level(self, crisis_level: CrisisLevel) -> List[tuple]:
        """Returnera roller och prioriteter baserat på krisnivå"""
        
        role_priorities = {
            CrisisLevel.STANDBY: [
                (PersonnelRole.CRISIS_LEADER, 1),
                (PersonnelRole.DEPUTY_LEADER, 2),
                (PersonnelRole.OPERATIONS_CHIEF, 2)
            ],
            CrisisLevel.ELEVATED: [
                (PersonnelRole.CRISIS_LEADER, 1),
                (PersonnelRole.DEPUTY_LEADER, 1),
                (PersonnelRole.OPERATIONS_CHIEF, 2),
                (PersonnelRole.INFORMATION_OFFICER, 2),
                (PersonnelRole.LOGISTICS_CHIEF, 3)
            ],
            CrisisLevel.EMERGENCY: [
                (PersonnelRole.CRISIS_LEADER, 1),
                (PersonnelRole.DEPUTY_LEADER, 1),
                (PersonnelRole.OPERATIONS_CHIEF, 1),
                (PersonnelRole.INFORMATION_OFFICER, 2),
                (PersonnelRole.LOGISTICS_CHIEF, 2),
                (PersonnelRole.MEDICAL_OFFICER, 2),
                (PersonnelRole.TECHNICAL_EXPERT, 3)
            ],
            CrisisLevel.DISASTER: [
                (PersonnelRole.CRISIS_LEADER, 1),
                (PersonnelRole.DEPUTY_LEADER, 1),
                (PersonnelRole.OPERATIONS_CHIEF, 1),
                (PersonnelRole.INFORMATION_OFFICER, 1),
                (PersonnelRole.LOGISTICS_CHIEF, 1),
                (PersonnelRole.MEDICAL_OFFICER, 1),
                (PersonnelRole.TECHNICAL_EXPERT, 2),
                (PersonnelRole.SUPPORT_STAFF, 3),
                (PersonnelRole.VOLUNTEER, 4)
            ]
        }
        
        return role_priorities.get(crisis_level, [])
    
    async def _initiate_communication_sequence(
        self, 
        crisis: CrisisActivation, 
        crisis_data: CrisisActivationCreate
    ):
        """Starta automatisk kommunikationssekvens enligt prioritet"""
        
        activations = self.session.exec(
            select(PersonnelActivation)
            .where(PersonnelActivation.crisis_id == crisis.id)
            .order_by(PersonnelActivation.priority_level, PersonnelActivation.assigned_role)
        ).all()
        
        # Gruppera efter prioritet
        priority_groups = {}
        for activation in activations:
            priority = activation.priority_level
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(activation)
        
        # Bearbeta varje prioritetsgrupp
        for priority in sorted(priority_groups.keys()):
            logger.info(f"Starting communication for priority {priority} personnel")
            
            tasks = []
            for activation in priority_groups[priority]:
                task = self._communicate_with_personnel(crisis, activation, crisis_data)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(2)  # Paus mellan prioritetsgrupper
    
    async def _communicate_with_personnel(
        self, 
        crisis: CrisisActivation, 
        activation: PersonnelActivation,
        crisis_data: CrisisActivationCreate
    ):
        """Kommunicera med en specifik person enligt definierad sekvens"""
        
        contact = self.session.get(Contact, activation.contact_id)
        if not contact or not contact.phone_numbers:
            await self._escalate_to_manual(crisis, activation, "no_phone_number")
            return
        
        primary_phone = contact.phone_numbers[0].number
        
        # Sekvens: Röstsamtal → SMS → Interaktiv länk → Eskalering
        
        if crisis_data.use_voice_calls:
            call_success = await self._attempt_voice_call(crisis, activation, primary_phone)
            if call_success:
                return
        
        if crisis_data.use_sms:
            sms_success = await self._attempt_sms_confirmation(crisis, activation, primary_phone)
            if sms_success:
                return
        
        if crisis_data.use_interactive_links:
            interactive_success = await self._send_interactive_confirmation(crisis, activation)
            if interactive_success:
                await asyncio.sleep(30)  # Vänta på svar
                self.session.refresh(activation)
                if activation.interactive_response_received:
                    return
        
        logger.warning(f"All communication methods attempted for {contact.name}, will escalate")
    
    async def _attempt_voice_call(
        self, 
        crisis: CrisisActivation, 
        activation: PersonnelActivation, 
        phone_number: str
    ) -> bool:
        """Försök röstsamtal med DTMF-kvittens"""
        
        call_message = self._generate_call_message(crisis, activation)
        
        try:
            activation.call_attempted_at = datetime.now()
            self.session.commit()
            
            call_result = await self.call_service.make_call_with_dtmf(
                phone_number=phone_number,
                message=call_message,
                dtmf_responses={
                    "1": "Tack för bekräftelsen! Du är registrerad som tillgänglig.",
                    "2": "Tack för att du meddelade. Vi noterar att du inte kan komma."
                }
            )
            
            activation.call_answered = call_result.get("answered", False)
            
            dtmf_digit = call_result.get("dtmf_digit")
            if dtmf_digit == "1":
                activation.call_confirmed = True
                activation.response_status = "confirmed"
                activation.response_received_at = datetime.now()
                self.session.commit()
                logger.info(f"Voice confirmation received for {phone_number}")
                return True
            elif dtmf_digit == "2":
                activation.response_status = "declined"
                activation.response_received_at = datetime.now()
                self.session.commit()
                logger.info(f"Voice decline received for {phone_number}")
                return True
            
        except Exception as e:
            logger.error(f"Voice call failed for {phone_number}: {e}")
        
        self.session.commit()
        return False
    
    async def _attempt_sms_confirmation(
        self, 
        crisis: CrisisActivation, 
        activation: PersonnelActivation, 
        phone_number: str
    ) -> bool:
        """Försök SMS med kvittens-svar"""
        
        sms_message = self._generate_sms_message(crisis, activation)
        
        try:
            activation.sms_sent_at = datetime.now()
            self.session.commit()
            
            sms_result = await self.sms_service.send_sms(
                phone_number=phone_number,
                message=sms_message
            )
            
            if sms_result.get("delivered", False):
                confirmation = await self._wait_for_sms_confirmation(activation, timeout_minutes=5)
                
                if confirmation:
                    activation.sms_confirmed = True
                    activation.response_status = "confirmed" if confirmation == "JA" else "declined"
                    activation.response_received_at = datetime.now()
                    self.session.commit()
                    logger.info(f"SMS confirmation received for {phone_number}: {confirmation}")
                    return True
            
        except Exception as e:
            logger.error(f"SMS failed for {phone_number}: {e}")
        
        self.session.commit()
        return False
    
    async def _send_interactive_confirmation(
        self, 
        crisis: CrisisActivation, 
        activation: PersonnelActivation
    ) -> bool:
        """Skicka interaktiv bekräftelselänk"""
        
        try:
            interactive_data = InteractiveMessageCreate(
                title=f"🚨 KRISINKALLNING: {crisis.crisis_name}",
                content=self._generate_interactive_message(crisis, activation),
                sender_name="Krisledning",
                theme_color="#DC2626",
                require_contact_info=True,
                expires_at=datetime.now() + timedelta(hours=2),
                contact_ids=[activation.contact_id],
                response_options=[
                    {
                        "option_key": "confirm_available",
                        "display_text": "✅ Bekräftar - Kan komma omgående",
                        "button_color": "#10B981",
                        "sort_order": 1,
                        "requires_comment": False,
                        "auto_reply_message": "Tack! Du är bekräftad."
                    },
                    {
                        "option_key": "unavailable",
                        "display_text": "❌ Kan inte komma",
                        "button_color": "#EF4444",
                        "sort_order": 2,
                        "requires_comment": True,
                        "auto_reply_message": "Tack för att du meddelade."
                    }
                ]
            )
            
            interactive_message = await self.interactive_service.create_interactive_message(interactive_data)
            await self.interactive_service.send_interactive_message(interactive_message.id)
            
            activation.interactive_link_sent = True
            activation.interactive_message_id = interactive_message.id
            self.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send interactive message for activation {activation.id}: {e}")
            return False
    
    async def _schedule_escalation_monitoring(
        self, 
        crisis: CrisisActivation, 
        max_escalation_time_minutes: int
    ):
        """Övervaka och eskalera obekräftade kontakter"""
        
        await asyncio.sleep(max_escalation_time_minutes * 60)
        
        unconfirmed_activations = self.session.exec(
            select(PersonnelActivation)
            .where(
                PersonnelActivation.crisis_id == crisis.id,
                PersonnelActivation.response_status == "pending",
                PersonnelActivation.escalated_to_manual == False
            )
        ).all()
        
        for activation in unconfirmed_activations:
            await self._escalate_to_manual(crisis, activation, "timeout_reached")
    
    async def _escalate_to_manual(
        self, 
        crisis: CrisisActivation, 
        activation: PersonnelActivation, 
        reason: str
    ):
        """Eskalera till manuell telefonisthantering"""
        
        escalation = ManualEscalation(
            crisis_id=crisis.id,
            personnel_activation_id=activation.id,
            escalation_reason=reason,
            attempts_made=self._count_communication_attempts(activation)
        )
        
        self.session.add(escalation)
        activation.escalated_to_manual = True
        activation.escalated_at = datetime.now()
        self.session.commit()
        
        await self._notify_operators_of_escalation(escalation)
        logger.warning(f"Escalated to manual handling: {activation.contact_id} (Reason: {reason})")
    
    def _count_communication_attempts(self, activation: PersonnelActivation) -> int:
        """Räkna antal kommunikationsförsök"""
        attempts = 0
        if activation.call_attempted_at:
            attempts += 1
        if activation.sms_sent_at:
            attempts += 1
        if activation.interactive_link_sent:
            attempts += 1
        return attempts
    
    async def _notify_operators_of_escalation(self, escalation: ManualEscalation):
        """Notifiera telefonister om ny eskalering"""
        available_operators = await self._get_available_operators()
        
        if not available_operators:
            logger.critical("No operators available for manual escalation!")
            return
        
        assigned_operator = self._assign_to_least_loaded_operator(available_operators)
        escalation.assigned_to_operator = assigned_operator
        escalation.operator_assigned_at = datetime.now()
        self.session.commit()
        
        logger.info(f"Escalation assigned to operator: {assigned_operator}")
    
    def get_crisis_dashboard_data(self, crisis_id: uuid.UUID) -> CrisisDashboardData:
        """Hämta realtidsdata för krisdashboard"""
        
        crisis = self.session.get(CrisisActivation, crisis_id)
        if not crisis:
            raise ValueError("Crisis not found")
        
        activations = self.session.exec(
            select(PersonnelActivation)
            .options(selectinload(PersonnelActivation.contact))
            .where(PersonnelActivation.crisis_id == crisis_id)
        ).all()
        
        # Beräkna statistik
        total_personnel = len(activations)
        confirmed_count = len([a for a in activations if a.response_status == "confirmed"])
        declined_count = len([a for a in activations if a.response_status == "declined"])
        pending_count = len([a for a in activations if a.response_status == "pending"])
        escalated_count = len([a for a in activations if a.escalated_to_manual])
        
        return CrisisDashboardData(
            crisis=crisis,
            statistics={
                "total_personnel": total_personnel,
                "confirmed": confirmed_count,
                "declined": declined_count,
                "pending": pending_count,
                "escalated": escalated_count,
                "confirmation_rate": confirmed_count / total_personnel if total_personnel > 0 else 0,
                "escalation_rate": escalated_count / total_personnel if total_personnel > 0 else 0
            },
            role_breakdown=self._calculate_role_breakdown(activations),
            communication_timeline=self._create_communication_timeline(activations)[-20:],
            critical_gaps=self._identify_critical_gaps(activations),
            pending_escalations=self._get_pending_escalations(crisis_id)
        )
    
    # Hjälpfunktioner
    def _generate_call_message(self, crisis: CrisisActivation, activation: PersonnelActivation) -> str:
        contact = self.session.get(Contact, activation.contact_id)
        return f"Hej {contact.name if contact else 'kollega'}. Krisaktivering: {crisis.crisis_name}. {crisis.primary_message}. Tryck 1 för att bekräfta, 2 för att avböja."
    
    def _generate_sms_message(self, crisis: CrisisActivation, activation: PersonnelActivation) -> str:
        return f"🚨 KRIS: {crisis.crisis_name}. {activation.assigned_role.value} behövs. Svara JA för att bekräfta, NEJ för att avböja."
    
    def _generate_interactive_message(self, crisis: CrisisActivation, activation: PersonnelActivation) -> str:
        contact = self.session.get(Contact, activation.contact_id)
        return f"**Krisaktivering: {crisis.crisis_name}**\n\nHej {contact.name if contact else 'kollega'},\n\n{crisis.primary_message}\n\n**Din roll:** {activation.assigned_role.value}"
    
    async def _get_all_emergency_personnel(self) -> List[Contact]:
        return self.contact_repo.get_all_contacts()
    
    async def _get_contacts_by_role(self, role: PersonnelRole, contacts: List[Contact]) -> List[Contact]:
        return contacts[:2]  # Placeholder
    
    async def _wait_for_sms_confirmation(self, activation: PersonnelActivation, timeout_minutes: int) -> Optional[str]:
        return None  # Placeholder
    
    async def _get_available_operators(self) -> List[str]:
        return ["Operator1", "Operator2", "Operator3"]
    
    def _assign_to_least_loaded_operator(self, operators: List[str]) -> str:
        return operators[0] if operators else "DefaultOperator"
    
    def _calculate_role_breakdown(self, activations: List[PersonnelActivation]) -> List[RoleStatusSummary]:
        role_stats = {}
        for activation in activations:
            role = activation.assigned_role
            if role not in role_stats:
                role_stats[role] = RoleStatusSummary(role=role)
            
            stats = role_stats[role]
            stats.total += 1
            if activation.response_status == "confirmed":
                stats.confirmed += 1
            elif activation.response_status == "declined":
                stats.declined += 1
            else:
                stats.pending += 1
            
            if activation.escalated_to_manual:
                stats.escalated += 1
            
            stats.confirmation_rate = stats.confirmed / stats.total if stats.total > 0 else 0
        
        return list(role_stats.values())
    
    def _create_communication_timeline(self, activations: List[PersonnelActivation]) -> List[CommunicationEvent]:
        events = []
        for activation in activations:
            contact = activation.contact
            contact_name = contact.name if contact else "Okänd"
            
            if activation.call_attempted_at:
                events.append(CommunicationEvent(
                    time=activation.call_attempted_at,
                    event_type="call_attempted",
                    contact_id=activation.contact_id,
                    contact_name=contact_name,
                    success=activation.call_confirmed
                ))
            
            if activation.sms_sent_at:
                events.append(CommunicationEvent(
                    time=activation.sms_sent_at,
                    event_type="sms_sent",
                    contact_id=activation.contact_id,
                    contact_name=contact_name,
                    success=activation.sms_confirmed
                ))
        
        return sorted(events, key=lambda x: x.time, reverse=True)
    
    def _identify_critical_gaps(self, activations: List[PersonnelActivation]) -> List[CriticalGap]:
        critical_roles = [PersonnelRole.CRISIS_LEADER, PersonnelRole.DEPUTY_LEADER, PersonnelRole.OPERATIONS_CHIEF]
        gaps = []
        
        for role in critical_roles:
            role_activations = [a for a in activations if a.assigned_role == role]
            confirmed = [a for a in role_activations if a.response_status == "confirmed"]
            
            if not confirmed:
                gaps.append(CriticalGap(
                    role=role,
                    severity="critical",
                    message=f"Ingen bekräftad {role.value}",
                    missing_count=1,
                    required_count=1
                ))
        
        return gaps
    
    def _get_pending_escalations(self, crisis_id: uuid.UUID) -> List:
        return []  # Placeholder
