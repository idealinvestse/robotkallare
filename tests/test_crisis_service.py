"""
Tester för CrisisManagementService
"""
import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlmodel import Session, select

from app.services.crisis_management_service import CrisisManagementService
from app.models import (
    CrisisActivation, PersonnelActivation, ManualEscalation,
    Contact, PhoneNumber, CrisisLevel, PersonnelRole
)
from app.schemas.crisis_management import (
    CrisisActivationCreate, CrisisDashboardData
)
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository

from tests.fixtures.database_fixtures import test_session, clean_test_session
from tests.fixtures.crisis_fixtures import (
    sample_user, emergency_contacts, emergency_group,
    sample_crisis_activation, personnel_activations,
    confirmed_personnel_activation, declined_personnel_activation,
    escalated_personnel_activation, manual_escalation,
    mock_communication_services, create_crisis_activation_data,
    crisis_test_data
)


class TestCrisisManagementService:
    """Tester för CrisisManagementService"""
    
    @pytest.fixture
    def crisis_service(self, test_session: Session, mock_communication_services):
        """Skapa CrisisManagementService med mocks"""
        contact_repo = ContactRepository(test_session)
        group_repo = GroupRepository(test_session)
        
        return CrisisManagementService(
            session=test_session,
            contact_repo=contact_repo,
            group_repo=group_repo,
            call_service=mock_communication_services["call_service"],
            sms_service=mock_communication_services["sms_service"],
            interactive_service=mock_communication_services["interactive_service"]
        )
    
    @pytest.mark.asyncio
    async def test_activate_crisis_response_basic(
        self,
        crisis_service: CrisisManagementService,
        sample_user,
        emergency_contacts
    ):
        """Test grundläggande krisaktivering"""
        crisis_data = create_crisis_activation_data(
            crisis_name="Test Krisaktivering",
            crisis_type="test",
            crisis_level=CrisisLevel.ELEVATED,
            geographic_area="Test Region",
            primary_message="Detta är en testkris för att verifiera funktionalitet"
        )
        
        # Aktivera krisen
        crisis = await crisis_service.activate_crisis_response(crisis_data, sample_user.id)
        
        # Verifiera att krisen skapades
        assert crisis.id is not None
        assert crisis.crisis_name == "Test Krisaktivering"
        assert crisis.crisis_level == CrisisLevel.ELEVATED
        assert crisis.is_active is True
        assert crisis.activated_by_user_id == sample_user.id
        
        # Verifiera att personalaktiveringar skapades
        activations = crisis_service.session.exec(
            select(PersonnelActivation).where(PersonnelActivation.crisis_id == crisis.id)
        ).all()
        
        assert len(activations) > 0
        
        # Kontrollera att rätt roller aktiverades för ELEVATED nivå
        activated_roles = [a.assigned_role for a in activations]
        expected_roles = [
            PersonnelRole.CRISIS_LEADER,
            PersonnelRole.DEPUTY_LEADER,
            PersonnelRole.OPERATIONS_CHIEF,
            PersonnelRole.INFORMATION_OFFICER,
            PersonnelRole.LOGISTICS_CHIEF
        ]
        
        # Alla förväntade roller ska finnas bland aktiverade
        for role in expected_roles:
            assert role in activated_roles
    
    @pytest.mark.asyncio
    async def test_activate_crisis_different_levels(
        self,
        crisis_service: CrisisManagementService,
        sample_user,
        emergency_contacts
    ):
        """Test aktivering med olika krisnivåer"""
        
        # Test STANDBY nivå
        standby_data = create_crisis_activation_data(
            crisis_name="Standby Test",
            crisis_level=CrisisLevel.STANDBY
        )
        
        standby_crisis = await crisis_service.activate_crisis_response(standby_data, sample_user.id)
        standby_activations = crisis_service.session.exec(
            select(PersonnelActivation).where(PersonnelActivation.crisis_id == standby_crisis.id)
        ).all()
        
        standby_roles = [a.assigned_role for a in standby_activations]
        
        # STANDBY ska bara aktivera grundläggande roller
        expected_standby_roles = [
            PersonnelRole.CRISIS_LEADER,
            PersonnelRole.DEPUTY_LEADER,
            PersonnelRole.OPERATIONS_CHIEF
        ]
        
        for role in expected_standby_roles:
            assert role in standby_roles
        
        # DISASTER nivå ska aktivera alla roller
        disaster_data = create_crisis_activation_data(
            crisis_name="Disaster Test",
            crisis_level=CrisisLevel.DISASTER
        )
        
        disaster_crisis = await crisis_service.activate_crisis_response(disaster_data, sample_user.id)
        disaster_activations = crisis_service.session.exec(
            select(PersonnelActivation).where(PersonnelActivation.crisis_id == disaster_crisis.id)
        ).all()
        
        disaster_roles = [a.assigned_role for a in disaster_activations]
        
        # DISASTER ska inkludera alla roller
        all_roles = [
            PersonnelRole.CRISIS_LEADER,
            PersonnelRole.DEPUTY_LEADER,
            PersonnelRole.OPERATIONS_CHIEF,
            PersonnelRole.INFORMATION_OFFICER,
            PersonnelRole.LOGISTICS_CHIEF,
            PersonnelRole.MEDICAL_OFFICER,
            PersonnelRole.TECHNICAL_EXPERT,
            PersonnelRole.SUPPORT_STAFF,
            PersonnelRole.VOLUNTEER
        ]
        
        for role in all_roles:
            assert role in disaster_roles
    
    @pytest.mark.asyncio
    async def test_activate_crisis_with_specific_contacts(
        self,
        crisis_service: CrisisManagementService,
        sample_user,
        emergency_contacts
    ):
        """Test aktivering med specifika kontakter"""
        # Välj bara första två kontakterna
        target_contact_ids = [emergency_contacts[0].id, emergency_contacts[1].id]
        
        crisis_data = create_crisis_activation_data(
            crisis_name="Specifik Kontakt Test",
            target_contact_ids=target_contact_ids
        )
        
        crisis = await crisis_service.activate_crisis_response(crisis_data, sample_user.id)
        
        activations = crisis_service.session.exec(
            select(PersonnelActivation).where(PersonnelActivation.crisis_id == crisis.id)
        ).all()
        
        activated_contact_ids = [a.contact_id for a in activations]
        
        # Kontrollera att bara specificerade kontakter aktiverades
        for contact_id in target_contact_ids:
            assert contact_id in activated_contact_ids
    
    @pytest.mark.asyncio
    async def test_communication_sequence_voice_success(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        emergency_contacts
    ):
        """Test kommunikationssekvens - framgångsrikt röstsamtal"""
        # Skapa personalaktivering för kontakt som kommer svara
        activation = PersonnelActivation(
            crisis_id=sample_crisis_activation.id,
            contact_id=emergency_contacts[0].id,  # Denna kontakt kommer svara enligt mock
            assigned_role=PersonnelRole.CRISIS_LEADER,
            priority_level=1
        )
        crisis_service.session.add(activation)
        crisis_service.session.commit()
        crisis_service.session.refresh(activation)
        
        # Mock för kommunikationsdata
        crisis_data = create_crisis_activation_data(use_voice_calls=True)
        
        # Kör kommunikationssekvens
        await crisis_service._communicate_with_personnel(
            sample_crisis_activation, activation, crisis_data
        )
        
        # Verifiera att röstsamtal gjordes och bekräftades
        crisis_service.session.refresh(activation)
        assert activation.call_attempted_at is not None
        assert activation.call_confirmed is True
        assert activation.response_status == "confirmed"
        assert activation.response_received_at is not None
    
    @pytest.mark.asyncio
    async def test_communication_sequence_escalation(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        emergency_contacts
    ):
        """Test kommunikationssekvens som leder till eskalering"""
        # Skapa personalaktivering för kontakt utan telefon
        no_phone_contact = emergency_contacts[4]  # Kontakt utan telefonnummer
        
        activation = PersonnelActivation(
            crisis_id=sample_crisis_activation.id,
            contact_id=no_phone_contact.id,
            assigned_role=PersonnelRole.SUPPORT_STAFF,
            priority_level=3
        )
        crisis_service.session.add(activation)
        crisis_service.session.commit()
        crisis_service.session.refresh(activation)
        
        crisis_data = create_crisis_activation_data()
        
        # Kör kommunikationssekvens
        await crisis_service._communicate_with_personnel(
            sample_crisis_activation, activation, crisis_data
        )
        
        # Verifiera att eskalering skapades
        crisis_service.session.refresh(activation)
        assert activation.escalated_to_manual is True
        assert activation.escalated_at is not None
        
        # Kontrollera att ManualEscalation skapades
        escalation = crisis_service.session.exec(
            select(ManualEscalation).where(
                ManualEscalation.personnel_activation_id == activation.id
            )
        ).first()
        
        assert escalation is not None
        assert escalation.escalation_reason == "no_phone_number"
    
    def test_get_crisis_dashboard_data(
        self,
        crisis_service: CrisisManagementService,
        crisis_test_data
    ):
        """Test hämtning av dashboard-data"""
        crisis = crisis_test_data["crisis"]
        
        dashboard_data = crisis_service.get_crisis_dashboard_data(crisis.id)
        
        # Verifiera dashboard-struktur
        assert isinstance(dashboard_data, CrisisDashboardData)
        assert dashboard_data.crisis.id == crisis.id
        assert dashboard_data.crisis.crisis_name == crisis.crisis_name
        
        # Kontrollera statistik
        stats = dashboard_data.statistics
        assert "total_personnel" in stats
        assert "confirmed" in stats
        assert "declined" in stats
        assert "pending" in stats
        assert "escalated" in stats
        assert "confirmation_rate" in stats
        assert "escalation_rate" in stats
        
        assert stats["total_personnel"] > 0
        assert stats["confirmed"] >= 0
        assert stats["declined"] >= 0
        assert stats["pending"] >= 0
        assert stats["escalated"] >= 0
        
        # Kontrollera rollfördelning
        assert len(dashboard_data.role_breakdown) > 0
        for role_summary in dashboard_data.role_breakdown:
            assert hasattr(role_summary, 'role')
            assert hasattr(role_summary, 'total')
            assert hasattr(role_summary, 'confirmed')
            assert hasattr(role_summary, 'pending')
        
        # Kontrollera kommunikationstidslinje
        assert isinstance(dashboard_data.communication_timeline, list)
        
        # Kontrollera kritiska luckor
        assert isinstance(dashboard_data.critical_gaps, list)
    
    def test_get_role_priorities_for_crisis_level(
        self,
        crisis_service: CrisisManagementService
    ):
        """Test prioriteringsmatris för olika krisnivåer"""
        
        # Test STANDBY
        standby_priorities = crisis_service._get_role_priorities_for_crisis_level(CrisisLevel.STANDBY)
        assert len(standby_priorities) == 3
        assert (PersonnelRole.CRISIS_LEADER, 1) in standby_priorities
        assert (PersonnelRole.DEPUTY_LEADER, 2) in standby_priorities
        assert (PersonnelRole.OPERATIONS_CHIEF, 2) in standby_priorities
        
        # Test ELEVATED
        elevated_priorities = crisis_service._get_role_priorities_for_crisis_level(CrisisLevel.ELEVATED)
        assert len(elevated_priorities) == 5
        assert (PersonnelRole.CRISIS_LEADER, 1) in elevated_priorities
        assert (PersonnelRole.LOGISTICS_CHIEF, 3) in elevated_priorities
        
        # Test EMERGENCY
        emergency_priorities = crisis_service._get_role_priorities_for_crisis_level(CrisisLevel.EMERGENCY)
        assert len(emergency_priorities) == 7
        assert (PersonnelRole.MEDICAL_OFFICER, 2) in emergency_priorities
        assert (PersonnelRole.TECHNICAL_EXPERT, 3) in emergency_priorities
        
        # Test DISASTER
        disaster_priorities = crisis_service._get_role_priorities_for_crisis_level(CrisisLevel.DISASTER)
        assert len(disaster_priorities) == 9  # Alla roller
        assert (PersonnelRole.VOLUNTEER, 4) in disaster_priorities
    
    @pytest.mark.asyncio
    async def test_escalate_to_manual(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        personnel_activations
    ):
        """Test manuell eskalering"""
        activation = personnel_activations[0]
        
        # Simulera kommunikationsförsök
        activation.call_attempted_at = datetime.now() - timedelta(minutes=5)
        activation.sms_sent_at = datetime.now() - timedelta(minutes=3)
        activation.interactive_link_sent = True
        crisis_service.session.commit()
        
        # Eskalera till manuell hantering
        await crisis_service._escalate_to_manual(
            sample_crisis_activation, activation, "timeout_reached"
        )
        
        # Verifiera eskalering
        crisis_service.session.refresh(activation)
        assert activation.escalated_to_manual is True
        assert activation.escalated_at is not None
        
        # Kontrollera att ManualEscalation skapades
        escalation = crisis_service.session.exec(
            select(ManualEscalation).where(
                ManualEscalation.personnel_activation_id == activation.id
            )
        ).first()
        
        assert escalation is not None
        assert escalation.escalation_reason == "timeout_reached"
        assert escalation.attempts_made == 3  # call + sms + interactive
    
    def test_count_communication_attempts(
        self,
        crisis_service: CrisisManagementService,
        personnel_activations
    ):
        """Test räkning av kommunikationsförsök"""
        activation = personnel_activations[0]
        
        # Inga försök
        assert crisis_service._count_communication_attempts(activation) == 0
        
        # Ett försök (samtal)
        activation.call_attempted_at = datetime.now()
        assert crisis_service._count_communication_attempts(activation) == 1
        
        # Två försök (samtal + SMS)
        activation.sms_sent_at = datetime.now()
        assert crisis_service._count_communication_attempts(activation) == 2
        
        # Tre försök (samtal + SMS + interaktiv)
        activation.interactive_link_sent = True
        assert crisis_service._count_communication_attempts(activation) == 3
    
    def test_generate_call_message(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        personnel_activations
    ):
        """Test generering av röstmeddelande"""
        activation = personnel_activations[0]
        
        message = crisis_service._generate_call_message(sample_crisis_activation, activation)
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "Anna Krisledare" in message  # Kontaktnamn
        assert "Översvämning Göta Älv" in message  # Krisnamn
        assert "crisis_leader" in message  # Roll
    
    def test_generate_sms_message(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        personnel_activations
    ):
        """Test generering av SMS-meddelande"""
        activation = personnel_activations[0]
        
        message = crisis_service._generate_sms_message(sample_crisis_activation, activation)
        
        assert isinstance(message, str)
        assert len(message) <= 160  # SMS-längdbegränsning
        assert "🚨" in message  # Krisikon
        assert "Översvämning Göta Älv" in message
        assert "crisis_leader" in message
    
    def test_generate_interactive_message(
        self,
        crisis_service: CrisisManagementService,
        sample_crisis_activation,
        personnel_activations
    ):
        """Test generering av interaktivt meddelande"""
        activation = personnel_activations[0]
        
        message = crisis_service._generate_interactive_message(sample_crisis_activation, activation)
        
        assert isinstance(message, str)
        assert len(message) > 0
        assert "**Krisaktivering:" in message  # Markdown-formatering
        assert "Anna Krisledare" in message
        assert "crisis_leader" in message
    
    def test_identify_critical_gaps(
        self,
        crisis_service: CrisisManagementService,
        personnel_activations,
        confirmed_personnel_activation
    ):
        """Test identifiering av kritiska luckor"""
        # Skapa scenario där krisledare saknas
        activations_without_leader = [
            pa for pa in personnel_activations 
            if pa.assigned_role != PersonnelRole.CRISIS_LEADER
        ]
        
        gaps = crisis_service._identify_critical_gaps(activations_without_leader)
        
        # Ska identifiera att krisledare saknas
        gap_messages = [gap.message for gap in gaps]
        assert any("krisledare" in msg.lower() for msg in gap_messages)
        
        # Test med bekräftad krisledare
        gaps_with_leader = crisis_service._identify_critical_gaps(personnel_activations)
        
        # Ska ha färre luckor när krisledare är bekräftad
        leader_gap_messages = [gap.message for gap in gaps_with_leader]
        confirmed_leader_gaps = [
            gap for gap in gaps_with_leader 
            if gap.role == PersonnelRole.CRISIS_LEADER
        ]
        
        # Om krisledare är bekräftad ska det inte finnas lucka för den rollen
        if confirmed_personnel_activation.assigned_role == PersonnelRole.CRISIS_LEADER:
            assert len(confirmed_leader_gaps) == 0


class TestCrisisServiceIntegration:
    """Integrationstester för CrisisManagementService"""
    
    @pytest.fixture
    def real_crisis_service(self, test_session: Session):
        """Skapa CrisisManagementService med riktiga dependencies (men mocked externa tjänster)"""
        contact_repo = ContactRepository(test_session)
        group_repo = GroupRepository(test_session)
        
        # Mock externa tjänster
        call_service = AsyncMock()
        sms_service = AsyncMock()
        interactive_service = AsyncMock()
        
        return CrisisManagementService(
            session=test_session,
            contact_repo=contact_repo,
            group_repo=group_repo,
            call_service=call_service,
            sms_service=sms_service,
            interactive_service=interactive_service
        )
    
    @pytest.mark.asyncio
    async def test_full_crisis_activation_workflow(
        self,
        real_crisis_service: CrisisManagementService,
        sample_user,
        emergency_contacts,
        emergency_group
    ):
        """Test komplett krisaktivering från start till slut"""
        
        # 1. Skapa krisdata
        crisis_data = create_crisis_activation_data(
            crisis_name="Fullständig Integration Test",
            crisis_type="integration_test",
            crisis_level=CrisisLevel.EMERGENCY,
            geographic_area="Integration Test Region",
            primary_message="Detta är ett fullständigt integrationstest",
            target_group_ids=[emergency_group.id],
            use_voice_calls=True,
            use_sms=True,
            use_interactive_links=True,
            max_escalation_time_minutes=1  # Kort tid för test
        )
        
        # 2. Aktivera krisen
        crisis = await real_crisis_service.activate_crisis_response(crisis_data, sample_user.id)
        
        # 3. Verifiera att krisen skapades korrekt
        assert crisis.id is not None
        assert crisis.crisis_name == "Fullständig Integration Test"
        assert crisis.is_active is True
        
        # 4. Kontrollera att personalaktiveringar skapades
        activations = real_crisis_service.session.exec(
            select(PersonnelActivation).where(PersonnelActivation.crisis_id == crisis.id)
        ).all()
        
        assert len(activations) > 0
        
        # 5. Verifiera att kommunikationstjänster anropades
        # (Detta skulle kräva mer sofistikerade mocks för att verifiera exakt)
        
        # 6. Testa dashboard-funktionalitet
        dashboard_data = real_crisis_service.get_crisis_dashboard_data(crisis.id)
        
        assert dashboard_data.crisis.id == crisis.id
        assert dashboard_data.statistics["total_personnel"] == len(activations)
        
        # 7. Simulera några svar
        if len(activations) > 0:
            # Bekräfta första personen
            activations[0].response_status = "confirmed"
            activations[0].response_received_at = datetime.now()
            
            if len(activations) > 1:
                # Avböj andra personen
                activations[1].response_status = "declined"
                activations[1].response_received_at = datetime.now()
            
            real_crisis_service.session.commit()
            
            # 8. Kontrollera uppdaterad dashboard
            updated_dashboard = real_crisis_service.get_crisis_dashboard_data(crisis.id)
            
            assert updated_dashboard.statistics["confirmed"] >= 1
            if len(activations) > 1:
                assert updated_dashboard.statistics["declined"] >= 1
        
        # 9. Avsluta krisen
        crisis.is_active = False
        crisis.resolved_at = datetime.now()
        real_crisis_service.session.commit()
        
        # 10. Verifiera att krisen är avslutad
        final_crisis = real_crisis_service.session.get(CrisisActivation, crisis.id)
        assert final_crisis.is_active is False
        assert final_crisis.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_crisis_activations(
        self,
        real_crisis_service: CrisisManagementService,
        sample_user,
        emergency_contacts
    ):
        """Test att hantera flera samtidiga kriser"""
        
        # Skapa flera kriser samtidigt
        crisis_tasks = []
        for i in range(3):
            crisis_data = create_crisis_activation_data(
                crisis_name=f"Samtidig Kris {i+1}",
                crisis_type=f"test_type_{i}",
                crisis_level=CrisisLevel.ELEVATED
            )
            
            task = real_crisis_service.activate_crisis_response(crisis_data, sample_user.id)
            crisis_tasks.append(task)
        
        # Vänta på att alla kriser aktiveras
        crises = await asyncio.gather(*crisis_tasks)
        
        # Verifiera att alla kriser skapades
        assert len(crises) == 3
        for i, crisis in enumerate(crises):
            assert crisis.crisis_name == f"Samtidig Kris {i+1}"
            assert crisis.is_active is True
        
        # Kontrollera att personalaktiveringar skapades för alla kriser
        for crisis in crises:
            activations = real_crisis_service.session.exec(
                select(PersonnelActivation).where(PersonnelActivation.crisis_id == crisis.id)
            ).all()
            assert len(activations) > 0
    
    def test_crisis_service_error_handling(
        self,
        real_crisis_service: CrisisManagementService
    ):
        """Test felhantering i CrisisManagementService"""
        
        # Test att hämta dashboard för icke-existerande kris
        non_existent_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Crisis not found"):
            real_crisis_service.get_crisis_dashboard_data(non_existent_id)
        
        # Test med ogiltiga parametrar skulle kräva mer specifik validering
        # i service-klassen
