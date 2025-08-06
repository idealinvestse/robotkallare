"""
Test fixtures för krishantering och beredskap
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlmodel import Session
from typing import List, Dict

from app.models import (
    CrisisActivation, PersonnelActivation, ManualEscalation, CrisisTemplate,
    Contact, PhoneNumber, ContactGroup, User, InteractiveMessage,
    CrisisLevel, PersonnelRole
)


@pytest.fixture
def sample_user(test_session: Session) -> User:
    """Skapa testanvändare för krishantering"""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440010"),
        username="crisis_admin",
        email="crisis@example.com",
        hashed_password="hashed_password",
        disabled=False
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def emergency_contacts(test_session: Session) -> List[Contact]:
    """Skapa testpersonal för beredskap"""
    contacts = []
    
    # Krisledare
    crisis_leader = Contact(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440020"),
        name="Anna Krisledare",
        email="anna.krisledare@region.se",
        notes="Krisledare för Region Väst"
    )
    test_session.add(crisis_leader)
    
    # Lägg till telefonnummer
    phone1 = PhoneNumber(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440021"),
        contact_id=crisis_leader.id,
        number="+46701234567",
        priority=1
    )
    test_session.add(phone1)
    contacts.append(crisis_leader)
    
    # Ställföreträdare
    deputy_leader = Contact(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440022"),
        name="Björn Ställföreträdare",
        email="bjorn.deputy@region.se",
        notes="Ställföreträdande krisledare"
    )
    test_session.add(deputy_leader)
    
    phone2 = PhoneNumber(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440023"),
        contact_id=deputy_leader.id,
        number="+46701234568",
        priority=1
    )
    test_session.add(phone2)
    contacts.append(deputy_leader)
    
    # Operativ chef
    operations_chief = Contact(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440024"),
        name="Cecilia Operativ",
        email="cecilia.ops@region.se",
        notes="Operativ chef"
    )
    test_session.add(operations_chief)
    
    phone3 = PhoneNumber(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440025"),
        contact_id=operations_chief.id,
        number="+46701234569",
        priority=1
    )
    test_session.add(phone3)
    contacts.append(operations_chief)
    
    # Informationsansvarig
    info_officer = Contact(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440026"),
        name="David Information",
        email="david.info@region.se",
        notes="Informationsansvarig"
    )
    test_session.add(info_officer)
    
    phone4 = PhoneNumber(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440027"),
        contact_id=info_officer.id,
        number="+46701234570",
        priority=1
    )
    test_session.add(phone4)
    contacts.append(info_officer)
    
    # Kontakt utan telefonnummer (för testning av eskalering)
    no_phone_contact = Contact(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440028"),
        name="Erik Inget Telefon",
        email="erik.nophone@region.se",
        notes="Kontakt utan telefonnummer"
    )
    test_session.add(no_phone_contact)
    contacts.append(no_phone_contact)
    
    test_session.commit()
    
    # Refresh alla kontakter för att få relationships
    for contact in contacts:
        test_session.refresh(contact)
    
    return contacts


@pytest.fixture
def emergency_group(test_session: Session, emergency_contacts: List[Contact]) -> ContactGroup:
    """Skapa beredskapsgrupp"""
    group = ContactGroup(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440030"),
        name="Krisledningsgrupp Väst",
        description="Huvudgrupp för krishantering i Västra Götaland"
    )
    test_session.add(group)
    test_session.commit()
    test_session.refresh(group)
    return group


@pytest.fixture
def crisis_template(test_session: Session, sample_user: User) -> CrisisTemplate:
    """Skapa krismall för översvämning"""
    template = CrisisTemplate(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440040"),
        template_name="Översvämning Standard",
        crisis_type="översvämning",
        default_crisis_level=CrisisLevel.EMERGENCY,
        call_message_template="Kritisk översvämningssituation. {role} behövs omgående. Tryck 1 för att bekräfta.",
        sms_message_template="🚨 Översvämning: {role} behövs. Svara JA för bekräftelse.",
        interactive_message_template="**ÖVERSVÄMNINGSKRIS**\n\n{message}\n\n**Din roll:** {role}",
        required_roles='["crisis_leader", "deputy_leader", "operations_chief", "logistics_chief"]',
        priority_matrix='{"crisis_leader": 1, "deputy_leader": 1, "operations_chief": 2, "logistics_chief": 3}',
        max_call_attempts=3,
        call_timeout_seconds=30,
        confirmation_deadline_minutes=15,
        escalation_delay_minutes=5,
        created_by_user_id=sample_user.id,
        is_active=True
    )
    test_session.add(template)
    test_session.commit()
    test_session.refresh(template)
    return template


@pytest.fixture
def sample_crisis_activation(test_session: Session, sample_user: User) -> CrisisActivation:
    """Skapa testkrisaktivering"""
    crisis = CrisisActivation(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440050"),
        crisis_name="Översvämning Göta Älv",
        crisis_type="översvämning",
        crisis_level=CrisisLevel.EMERGENCY,
        geographic_area="Västra Götaland",
        activated_at=datetime.now(),
        activated_by_user_id=sample_user.id,
        expected_duration="24 timmar",
        meeting_location="Regionens kriscentrum, Göteborg",
        required_arrival_time=datetime.now() + timedelta(hours=1),
        is_active=True,
        primary_message="Kritisk översvämningssituation vid Göta Älv. Vattennivåerna stiger snabbt och evakuering kan bli nödvändig.",
        urgency_level=4
    )
    test_session.add(crisis)
    test_session.commit()
    test_session.refresh(crisis)
    return crisis


@pytest.fixture
def personnel_activations(
    test_session: Session, 
    sample_crisis_activation: CrisisActivation,
    emergency_contacts: List[Contact]
) -> List[PersonnelActivation]:
    """Skapa personalaktiveringar för testkris"""
    activations = []
    
    roles = [
        PersonnelRole.CRISIS_LEADER,
        PersonnelRole.DEPUTY_LEADER,
        PersonnelRole.OPERATIONS_CHIEF,
        PersonnelRole.INFORMATION_OFFICER
    ]
    
    for i, (contact, role) in enumerate(zip(emergency_contacts[:4], roles)):
        activation = PersonnelActivation(
            id=uuid.UUID(f"550e8400-e29b-41d4-a716-44665544006{i}"),
            crisis_id=sample_crisis_activation.id,
            contact_id=contact.id,
            assigned_role=role,
            priority_level=1 if role in [PersonnelRole.CRISIS_LEADER, PersonnelRole.DEPUTY_LEADER] else 2,
            meeting_location="Regionens kriscentrum, Göteborg",
            required_arrival_time=datetime.now() + timedelta(hours=1),
            response_status="pending"
        )
        test_session.add(activation)
        activations.append(activation)
    
    # Skapa en aktivering för kontakt utan telefon (för eskaleringstest)
    no_phone_activation = PersonnelActivation(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440064"),
        crisis_id=sample_crisis_activation.id,
        contact_id=emergency_contacts[4].id,  # Kontakt utan telefon
        assigned_role=PersonnelRole.SUPPORT_STAFF,
        priority_level=3,
        response_status="pending"
    )
    test_session.add(no_phone_activation)
    activations.append(no_phone_activation)
    
    test_session.commit()
    
    for activation in activations:
        test_session.refresh(activation)
    
    return activations


@pytest.fixture
def confirmed_personnel_activation(
    test_session: Session,
    personnel_activations: List[PersonnelActivation]
) -> PersonnelActivation:
    """Skapa bekräftad personalaktivering"""
    activation = personnel_activations[0]  # Krisledare
    activation.call_attempted_at = datetime.now() - timedelta(minutes=5)
    activation.call_answered = True
    activation.call_confirmed = True
    activation.response_status = "confirmed"
    activation.response_received_at = datetime.now() - timedelta(minutes=4)
    activation.estimated_arrival = datetime.now() + timedelta(minutes=30)
    
    test_session.commit()
    test_session.refresh(activation)
    return activation


@pytest.fixture
def declined_personnel_activation(
    test_session: Session,
    personnel_activations: List[PersonnelActivation]
) -> PersonnelActivation:
    """Skapa avböjd personalaktivering"""
    activation = personnel_activations[1]  # Ställföreträdare
    activation.sms_sent_at = datetime.now() - timedelta(minutes=3)
    activation.sms_confirmed = True
    activation.response_status = "declined"
    activation.response_received_at = datetime.now() - timedelta(minutes=2)
    activation.availability_comment = "Är på semester utomlands"
    
    test_session.commit()
    test_session.refresh(activation)
    return activation


@pytest.fixture
def escalated_personnel_activation(
    test_session: Session,
    personnel_activations: List[PersonnelActivation]
) -> PersonnelActivation:
    """Skapa eskalerad personalaktivering"""
    activation = personnel_activations[2]  # Operativ chef
    activation.call_attempted_at = datetime.now() - timedelta(minutes=10)
    activation.call_answered = False
    activation.sms_sent_at = datetime.now() - timedelta(minutes=8)
    activation.sms_confirmed = False
    activation.interactive_link_sent = True
    activation.interactive_response_received = False
    activation.escalated_to_manual = True
    activation.escalated_at = datetime.now() - timedelta(minutes=2)
    
    test_session.commit()
    test_session.refresh(activation)
    return activation


@pytest.fixture
def manual_escalation(
    test_session: Session,
    sample_crisis_activation: CrisisActivation,
    escalated_personnel_activation: PersonnelActivation
) -> ManualEscalation:
    """Skapa manuell eskalering"""
    escalation = ManualEscalation(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440070"),
        crisis_id=sample_crisis_activation.id,
        personnel_activation_id=escalated_personnel_activation.id,
        escalated_at=datetime.now() - timedelta(minutes=2),
        escalation_reason="no_answer",
        attempts_made=3,
        assigned_to_operator="Telefonist Anna",
        operator_assigned_at=datetime.now() - timedelta(minutes=1),
        contact_successful=False
    )
    test_session.add(escalation)
    test_session.commit()
    test_session.refresh(escalation)
    return escalation


@pytest.fixture
def resolved_manual_escalation(
    test_session: Session,
    manual_escalation: ManualEscalation
) -> ManualEscalation:
    """Skapa löst manuell eskalering"""
    manual_escalation.contact_attempted_at = datetime.now() - timedelta(minutes=5)
    manual_escalation.contact_successful = True
    manual_escalation.contact_result = "confirmed"
    manual_escalation.contact_notes = "Kontaktad via hemtelefon. Bekräftar deltagande."
    manual_escalation.resolved_at = datetime.now() - timedelta(minutes=3)
    
    test_session.commit()
    test_session.refresh(manual_escalation)
    return manual_escalation


@pytest.fixture
def crisis_test_data(
    test_session: Session,
    sample_user: User,
    emergency_contacts: List[Contact],
    emergency_group: ContactGroup,
    crisis_template: CrisisTemplate,
    sample_crisis_activation: CrisisActivation,
    personnel_activations: List[PersonnelActivation],
    confirmed_personnel_activation: PersonnelActivation,
    declined_personnel_activation: PersonnelActivation,
    escalated_personnel_activation: PersonnelActivation,
    manual_escalation: ManualEscalation
) -> Dict:
    """Komplett testdataset för krishantering"""
    return {
        "user": sample_user,
        "contacts": emergency_contacts,
        "group": emergency_group,
        "template": crisis_template,
        "crisis": sample_crisis_activation,
        "activations": personnel_activations,
        "confirmed_activation": confirmed_personnel_activation,
        "declined_activation": declined_personnel_activation,
        "escalated_activation": escalated_personnel_activation,
        "escalation": manual_escalation,
        "session": test_session
    }


@pytest.fixture
def mock_communication_services():
    """Mock för kommunikationstjänster"""
    class MockCallService:
        async def make_call_with_dtmf(self, phone_number: str, message: str, dtmf_responses: dict):
            # Simulera framgångsrikt samtal för vissa nummer
            if phone_number == "+46701234567":  # Krisledare
                return {"answered": True, "dtmf_digit": "1", "confirmed": True}
            elif phone_number == "+46701234568":  # Ställföreträdare
                return {"answered": True, "dtmf_digit": "2", "confirmed": False}
            else:
                return {"answered": False, "dtmf_digit": None, "confirmed": False}
    
    class MockSmsService:
        async def send_sms(self, phone_number: str, message: str):
            # Simulera framgångsrik SMS för vissa nummer
            if phone_number in ["+46701234567", "+46701234568"]:
                return {"delivered": True, "message_sid": f"SM{phone_number[-4:]}"}
            else:
                return {"delivered": False, "error": "Invalid number"}
    
    class MockInteractiveService:
        async def create_interactive_message(self, data):
            return type('MockMessage', (), {'id': uuid.uuid4()})()
        
        async def send_interactive_message(self, message_id):
            return {"sent": True}
    
    return {
        "call_service": MockCallService(),
        "sms_service": MockSmsService(),
        "interactive_service": MockInteractiveService()
    }


# Hjälpfunktioner för testdata
def create_crisis_activation_data(**overrides):
    """Skapa CrisisActivationCreate data för tester"""
    from app.schemas.crisis_management import CrisisActivationCreate
    
    default_data = {
        "crisis_name": "Test Kris",
        "crisis_type": "test",
        "crisis_level": CrisisLevel.ELEVATED,
        "geographic_area": "Test Region",
        "primary_message": "Detta är en testkris",
        "urgency_level": 3,
        "expected_duration": "2 timmar",
        "meeting_location": "Testcenter",
        "use_voice_calls": True,
        "use_sms": True,
        "use_interactive_links": True,
        "max_escalation_time_minutes": 10
    }
    
    default_data.update(overrides)
    return CrisisActivationCreate(**default_data)


def create_personnel_update_data(**overrides):
    """Skapa PersonnelActivationUpdate data för tester"""
    from app.schemas.crisis_management import PersonnelActivationUpdate
    
    default_data = {
        "response_status": "confirmed",
        "estimated_arrival": datetime.now() + timedelta(minutes=30),
        "availability_comment": "Bekräftar deltagande"
    }
    
    default_data.update(overrides)
    return PersonnelActivationUpdate(**default_data)


def create_escalation_update_data(**overrides):
    """Skapa ManualEscalationUpdate data för tester"""
    from app.schemas.crisis_management import ManualEscalationUpdate
    
    default_data = {
        "assigned_to_operator": "Test Telefonist",
        "contact_result": "confirmed",
        "contact_notes": "Kontakt lyckades",
        "contact_successful": True
    }
    
    default_data.update(overrides)
    return ManualEscalationUpdate(**default_data)
