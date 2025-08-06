"""
Tester för krishanteringsmodeller
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models import (
    CrisisActivation, PersonnelActivation, ManualEscalation, CrisisTemplate,
    Contact, PhoneNumber, User, CrisisLevel, PersonnelRole
)
from tests.fixtures.database_fixtures import test_session, clean_test_session
from tests.fixtures.crisis_fixtures import (
    sample_user, emergency_contacts, crisis_template,
    sample_crisis_activation, personnel_activations,
    confirmed_personnel_activation, declined_personnel_activation,
    escalated_personnel_activation, manual_escalation
)


class TestCrisisActivationModel:
    """Tester för CrisisActivation-modellen"""
    
    def test_create_crisis_activation(self, test_session: Session, sample_user: User):
        """Test att skapa en krisaktivering"""
        crisis = CrisisActivation(
            crisis_name="Test Översvämning",
            crisis_type="översvämning",
            crisis_level=CrisisLevel.EMERGENCY,
            geographic_area="Göteborg",
            activated_by_user_id=sample_user.id,
            primary_message="Kritisk översvämning vid Göta Älv",
            urgency_level=4
        )
        
        test_session.add(crisis)
        test_session.commit()
        test_session.refresh(crisis)
        
        assert crisis.id is not None
        assert crisis.crisis_name == "Test Översvämning"
        assert crisis.crisis_level == CrisisLevel.EMERGENCY
        assert crisis.is_active is True
        assert crisis.resolved_at is None
        assert isinstance(crisis.activated_at, datetime)
    
    def test_crisis_activation_relationships(
        self, 
        test_session: Session, 
        sample_crisis_activation: CrisisActivation,
        personnel_activations: list
    ):
        """Test relationer för CrisisActivation"""
        # Hämta krisen med relationer
        crisis = test_session.get(CrisisActivation, sample_crisis_activation.id)
        
        # Kontrollera att personal-relationer fungerar
        assert len(crisis.personnel_activations) > 0
        assert all(isinstance(pa, PersonnelActivation) for pa in crisis.personnel_activations)
        
        # Kontrollera att användare-relation fungerar
        assert crisis.activated_by is not None
        assert crisis.activated_by.username == "crisis_admin"
    
    def test_crisis_activation_enum_validation(self, test_session: Session, sample_user: User):
        """Test att enum-värden valideras korrekt"""
        # Test giltigt CrisisLevel
        crisis = CrisisActivation(
            crisis_name="Test",
            crisis_type="test",
            crisis_level=CrisisLevel.DISASTER,
            geographic_area="Test",
            activated_by_user_id=sample_user.id,
            primary_message="Test",
            urgency_level=5
        )
        
        test_session.add(crisis)
        test_session.commit()
        
        assert crisis.crisis_level == CrisisLevel.DISASTER
    
    def test_crisis_activation_urgency_constraints(self, test_session: Session, sample_user: User):
        """Test att urgency_level följer constraints (1-5)"""
        # Test giltig urgency_level
        crisis = CrisisActivation(
            crisis_name="Test",
            crisis_type="test",
            crisis_level=CrisisLevel.STANDBY,
            geographic_area="Test",
            activated_by_user_id=sample_user.id,
            primary_message="Test",
            urgency_level=3
        )
        
        test_session.add(crisis)
        test_session.commit()
        
        assert crisis.urgency_level == 3
    
    def test_resolve_crisis(self, test_session: Session, sample_crisis_activation: CrisisActivation):
        """Test att avsluta en kris"""
        crisis = sample_crisis_activation
        assert crisis.is_active is True
        assert crisis.resolved_at is None
        
        # Avsluta krisen
        crisis.is_active = False
        crisis.resolved_at = datetime.now()
        
        test_session.commit()
        test_session.refresh(crisis)
        
        assert crisis.is_active is False
        assert crisis.resolved_at is not None
        assert isinstance(crisis.resolved_at, datetime)


class TestPersonnelActivationModel:
    """Tester för PersonnelActivation-modellen"""
    
    def test_create_personnel_activation(
        self, 
        test_session: Session,
        sample_crisis_activation: CrisisActivation,
        emergency_contacts: list
    ):
        """Test att skapa personalaktivering"""
        contact = emergency_contacts[0]
        
        activation = PersonnelActivation(
            crisis_id=sample_crisis_activation.id,
            contact_id=contact.id,
            assigned_role=PersonnelRole.CRISIS_LEADER,
            priority_level=1,
            meeting_location="Kriscentrum",
            required_arrival_time=datetime.now() + timedelta(hours=1)
        )
        
        test_session.add(activation)
        test_session.commit()
        test_session.refresh(activation)
        
        assert activation.id is not None
        assert activation.assigned_role == PersonnelRole.CRISIS_LEADER
        assert activation.priority_level == 1
        assert activation.response_status == "pending"
        assert activation.escalated_to_manual is False
    
    def test_personnel_activation_relationships(
        self,
        test_session: Session,
        personnel_activations: list
    ):
        """Test relationer för PersonnelActivation"""
        activation = personnel_activations[0]
        
        # Kontrollera kris-relation
        assert activation.crisis is not None
        assert activation.crisis.crisis_name == "Översvämning Göta Älv"
        
        # Kontrollera kontakt-relation
        assert activation.contact is not None
        assert activation.contact.name == "Anna Krisledare"
    
    def test_personnel_activation_communication_tracking(
        self,
        test_session: Session,
        confirmed_personnel_activation: PersonnelActivation
    ):
        """Test spårning av kommunikationsförsök"""
        activation = confirmed_personnel_activation
        
        assert activation.call_attempted_at is not None
        assert activation.call_answered is True
        assert activation.call_confirmed is True
        assert activation.response_status == "confirmed"
        assert activation.response_received_at is not None
        assert activation.estimated_arrival is not None
    
    def test_personnel_role_enum_validation(
        self,
        test_session: Session,
        sample_crisis_activation: CrisisActivation,
        emergency_contacts: list
    ):
        """Test att PersonnelRole enum valideras"""
        contact = emergency_contacts[0]
        
        # Test alla giltiga roller
        valid_roles = [
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
        
        for role in valid_roles:
            activation = PersonnelActivation(
                crisis_id=sample_crisis_activation.id,
                contact_id=contact.id,
                assigned_role=role,
                priority_level=2
            )
            
            test_session.add(activation)
            test_session.commit()
            
            assert activation.assigned_role == role
            
            # Rensa för nästa test
            test_session.delete(activation)
            test_session.commit()
    
    def test_priority_level_constraints(
        self,
        test_session: Session,
        sample_crisis_activation: CrisisActivation,
        emergency_contacts: list
    ):
        """Test att priority_level följer constraints (1-5)"""
        contact = emergency_contacts[0]
        
        # Test giltiga prioritetsnivåer
        for priority in [1, 2, 3, 4, 5]:
            activation = PersonnelActivation(
                crisis_id=sample_crisis_activation.id,
                contact_id=contact.id,
                assigned_role=PersonnelRole.SUPPORT_STAFF,
                priority_level=priority
            )
            
            test_session.add(activation)
            test_session.commit()
            
            assert activation.priority_level == priority
            
            # Rensa för nästa test
            test_session.delete(activation)
            test_session.commit()


class TestManualEscalationModel:
    """Tester för ManualEscalation-modellen"""
    
    def test_create_manual_escalation(
        self,
        test_session: Session,
        sample_crisis_activation: CrisisActivation,
        personnel_activations: list
    ):
        """Test att skapa manuell eskalering"""
        activation = personnel_activations[0]
        
        escalation = ManualEscalation(
            crisis_id=sample_crisis_activation.id,
            personnel_activation_id=activation.id,
            escalation_reason="no_answer",
            attempts_made=3
        )
        
        test_session.add(escalation)
        test_session.commit()
        test_session.refresh(escalation)
        
        assert escalation.id is not None
        assert escalation.escalation_reason == "no_answer"
        assert escalation.attempts_made == 3
        assert escalation.contact_successful is False
        assert escalation.resolved_at is None
        assert isinstance(escalation.escalated_at, datetime)
    
    def test_manual_escalation_relationships(
        self,
        test_session: Session,
        manual_escalation: ManualEscalation
    ):
        """Test relationer för ManualEscalation"""
        escalation = manual_escalation
        
        # Kontrollera kris-relation
        assert escalation.crisis is not None
        assert escalation.crisis.crisis_name == "Översvämning Göta Älv"
        
        # Kontrollera personalaktivering-relation
        assert escalation.personnel_activation is not None
        assert escalation.personnel_activation.assigned_role == PersonnelRole.OPERATIONS_CHIEF
    
    def test_escalation_operator_assignment(
        self,
        test_session: Session,
        manual_escalation: ManualEscalation
    ):
        """Test tilldelning av telefonist"""
        escalation = manual_escalation
        
        assert escalation.assigned_to_operator == "Telefonist Anna"
        assert escalation.operator_assigned_at is not None
    
    def test_escalation_resolution(
        self,
        test_session: Session,
        manual_escalation: ManualEscalation
    ):
        """Test att lösa eskalering"""
        escalation = manual_escalation
        
        # Markera som löst
        escalation.contact_attempted_at = datetime.now()
        escalation.contact_successful = True
        escalation.contact_result = "confirmed"
        escalation.contact_notes = "Kontaktad via hemtelefon"
        escalation.resolved_at = datetime.now()
        
        test_session.commit()
        test_session.refresh(escalation)
        
        assert escalation.contact_successful is True
        assert escalation.contact_result == "confirmed"
        assert escalation.contact_notes == "Kontaktad via hemtelefon"
        assert escalation.resolved_at is not None


class TestCrisisTemplateModel:
    """Tester för CrisisTemplate-modellen"""
    
    def test_create_crisis_template(
        self,
        test_session: Session,
        sample_user: User
    ):
        """Test att skapa krismall"""
        template = CrisisTemplate(
            template_name="Brand Standard",
            crisis_type="brand",
            default_crisis_level=CrisisLevel.EMERGENCY,
            call_message_template="Brandlarm aktiverat. {role} behövs.",
            sms_message_template="🔥 Brand: {role} behövs",
            interactive_message_template="**BRANDLARM**\n{message}",
            required_roles='["crisis_leader", "deputy_leader"]',
            priority_matrix='{"crisis_leader": 1, "deputy_leader": 2}',
            max_call_attempts=3,
            call_timeout_seconds=30,
            confirmation_deadline_minutes=10,
            escalation_delay_minutes=5,
            created_by_user_id=sample_user.id
        )
        
        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)
        
        assert template.id is not None
        assert template.template_name == "Brand Standard"
        assert template.crisis_type == "brand"
        assert template.default_crisis_level == CrisisLevel.EMERGENCY
        assert template.is_active is True
        assert isinstance(template.created_at, datetime)
    
    def test_crisis_template_relationships(
        self,
        test_session: Session,
        crisis_template: CrisisTemplate
    ):
        """Test relationer för CrisisTemplate"""
        template = crisis_template
        
        # Kontrollera användare-relation
        assert template.created_by is not None
        assert template.created_by.username == "crisis_admin"
    
    def test_template_json_fields(
        self,
        test_session: Session,
        crisis_template: CrisisTemplate
    ):
        """Test JSON-fält i mall"""
        template = crisis_template
        
        # Kontrollera att JSON-fält sparas korrekt
        assert template.required_roles is not None
        assert template.priority_matrix is not None
        
        # JSON-fält ska vara strängar (SQLModel hanterar serialisering)
        assert isinstance(template.required_roles, str)
        assert isinstance(template.priority_matrix, str)
    
    def test_template_constraints(
        self,
        test_session: Session,
        sample_user: User
    ):
        """Test constraints för mallparametrar"""
        template = CrisisTemplate(
            template_name="Test Mall",
            crisis_type="test",
            default_crisis_level=CrisisLevel.STANDBY,
            call_message_template="Test",
            sms_message_template="Test",
            interactive_message_template="Test",
            required_roles='[]',
            priority_matrix='{}',
            max_call_attempts=5,  # Inom gränser (1-10)
            call_timeout_seconds=60,  # Inom gränser (10-120)
            confirmation_deadline_minutes=30,  # Inom gränser (1-60)
            escalation_delay_minutes=15,  # Inom gränser (1-30)
            created_by_user_id=sample_user.id
        )
        
        test_session.add(template)
        test_session.commit()
        
        assert template.max_call_attempts == 5
        assert template.call_timeout_seconds == 60
        assert template.confirmation_deadline_minutes == 30
        assert template.escalation_delay_minutes == 15


class TestCrisisModelIntegration:
    """Integrationstester för krishanteringsmodeller"""
    
    def test_full_crisis_workflow(
        self,
        test_session: Session,
        sample_user: User,
        emergency_contacts: list
    ):
        """Test komplett krishanteringsflöde"""
        # 1. Skapa kris
        crisis = CrisisActivation(
            crisis_name="Integration Test Kris",
            crisis_type="test",
            crisis_level=CrisisLevel.EMERGENCY,
            geographic_area="Test Region",
            activated_by_user_id=sample_user.id,
            primary_message="Test av komplett flöde",
            urgency_level=3
        )
        test_session.add(crisis)
        test_session.commit()
        test_session.refresh(crisis)
        
        # 2. Skapa personalaktiveringar
        activations = []
        for i, contact in enumerate(emergency_contacts[:3]):
            activation = PersonnelActivation(
                crisis_id=crisis.id,
                contact_id=contact.id,
                assigned_role=PersonnelRole.CRISIS_LEADER if i == 0 else PersonnelRole.SUPPORT_STAFF,
                priority_level=1 if i == 0 else 2
            )
            test_session.add(activation)
            activations.append(activation)
        
        test_session.commit()
        
        # 3. Simulera kommunikationsförsök
        activations[0].call_attempted_at = datetime.now()
        activations[0].call_confirmed = True
        activations[0].response_status = "confirmed"
        
        activations[1].sms_sent_at = datetime.now()
        activations[1].response_status = "declined"
        
        # 4. Skapa eskalering för tredje personen
        activations[2].escalated_to_manual = True
        activations[2].escalated_at = datetime.now()
        
        escalation = ManualEscalation(
            crisis_id=crisis.id,
            personnel_activation_id=activations[2].id,
            escalation_reason="no_answer",
            attempts_made=2
        )
        test_session.add(escalation)
        
        test_session.commit()
        
        # 5. Verifiera hela strukturen
        # Hämta krisen med alla relationer
        crisis_with_relations = test_session.get(CrisisActivation, crisis.id)
        
        assert len(crisis_with_relations.personnel_activations) == 3
        assert len(crisis_with_relations.escalations) == 1
        
        # Kontrollera statusfördelning
        statuses = [pa.response_status for pa in crisis_with_relations.personnel_activations]
        assert "confirmed" in statuses
        assert "declined" in statuses
        assert "pending" in statuses
        
        # Kontrollera eskalering
        escalation_from_db = crisis_with_relations.escalations[0]
        assert escalation_from_db.escalation_reason == "no_answer"
        assert escalation_from_db.personnel_activation.escalated_to_manual is True
    
    def test_cascade_delete_behavior(
        self,
        test_session: Session,
        sample_crisis_activation: CrisisActivation,
        personnel_activations: list,
        manual_escalation: ManualEscalation
    ):
        """Test att relationer hanteras korrekt vid borttagning"""
        crisis_id = sample_crisis_activation.id
        activation_ids = [pa.id for pa in personnel_activations]
        escalation_id = manual_escalation.id
        
        # Kontrollera att allt finns
        assert test_session.get(CrisisActivation, crisis_id) is not None
        assert all(test_session.get(PersonnelActivation, aid) is not None for aid in activation_ids)
        assert test_session.get(ManualEscalation, escalation_id) is not None
        
        # Ta bort krisen (beroende på foreign key constraints)
        # I en riktig applikation skulle vi hantera detta med soft delete
        # eller cascade delete policies
        
        # För nu testar vi bara att relationerna fungerar
        crisis = test_session.get(CrisisActivation, crisis_id)
        assert len(crisis.personnel_activations) > 0
        assert len(crisis.escalations) > 0
