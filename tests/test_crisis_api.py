"""
Tester för Crisis Management API endpoints
"""
import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import app
from app.models import CrisisActivation, PersonnelActivation, ManualEscalation, CrisisLevel, PersonnelRole
from app.schemas.crisis_management import CrisisActivationCreate

from tests.fixtures.database_fixtures import test_session, clean_test_session
from tests.fixtures.crisis_fixtures import (
    sample_user, emergency_contacts, sample_crisis_activation,
    personnel_activations, manual_escalation, crisis_test_data,
    create_crisis_activation_data
)


class TestCrisisActivationAPI:
    """Tester för krisaktivering API endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_crisis_service(self):
        """Mock för CrisisManagementService"""
        with patch('app.api.crisis_management.get_crisis_management_service') as mock:
            service = Mock()
            service.session = Mock()
            mock.return_value = service
            yield service
    
    def test_activate_crisis_success(self, client, mock_crisis_service, sample_user):
        """Test framgångsrik krisaktivering"""
        # Mock service response
        mock_crisis = Mock()
        mock_crisis.id = uuid.uuid4()
        mock_crisis.crisis_name = "Test Kris"
        mock_crisis.crisis_type = "test"
        mock_crisis.crisis_level = CrisisLevel.EMERGENCY
        mock_crisis.geographic_area = "Test Region"
        mock_crisis.activated_at = datetime.now()
        mock_crisis.activated_by_user_id = sample_user.id
        mock_crisis.is_active = True
        mock_crisis.resolved_at = None
        mock_crisis.primary_message = "Test meddelande"
        mock_crisis.urgency_level = 4
        mock_crisis.expected_duration = None
        mock_crisis.meeting_location = None
        mock_crisis.required_arrival_time = None
        
        mock_crisis_service.activate_crisis_response = AsyncMock(return_value=mock_crisis)
        
        # Test data
        crisis_data = {
            "crisis_name": "Test Kris",
            "crisis_type": "test",
            "crisis_level": "emergency",
            "geographic_area": "Test Region",
            "primary_message": "Test meddelande",
            "urgency_level": 4,
            "use_voice_calls": True,
            "use_sms": True,
            "use_interactive_links": True,
            "max_escalation_time_minutes": 15
        }
        
        # Gör API-anrop
        response = client.post("/api/v1/crisis/activate", json=crisis_data)
        
        # Verifiera respons
        assert response.status_code == 201
        data = response.json()
        assert data["crisis_name"] == "Test Kris"
        assert data["crisis_level"] == "emergency"
        assert data["is_active"] is True
    
    def test_activate_crisis_validation_error(self, client):
        """Test validering av krisaktivering"""
        # Ogiltig data (saknar obligatoriska fält)
        invalid_data = {
            "crisis_name": "Test",
            # Saknar crisis_type, crisis_level, etc.
        }
        
        response = client.post("/api/v1/crisis/activate", json=invalid_data)
        
        # Ska returnera valideringsfel
        assert response.status_code == 422
    
    def test_get_crisis_list(self, client, mock_crisis_service):
        """Test hämtning av krislista"""
        # Mock service response
        mock_crisis_service.session.query.return_value.count.return_value = 2
        mock_crisis_service.session.query.return_value.filter.return_value.count.return_value = 1
        mock_crisis_service.session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        response = client.get("/api/v1/crisis/")
        
        assert response.status_code == 200
        data = response.json()
        assert "crises" in data
        assert "total_count" in data
        assert "active_count" in data
        assert "resolved_count" in data
    
    def test_get_crisis_by_id(self, client, mock_crisis_service, sample_crisis_activation):
        """Test hämtning av specifik kris"""
        # Mock service response
        mock_crisis_service.session.get.return_value = sample_crisis_activation
        mock_crisis_service.session.query.return_value.filter.return_value.count.return_value = 5
        
        response = client.get(f"/api/v1/crisis/{sample_crisis_activation.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_crisis_activation.id)
        assert data["crisis_name"] == sample_crisis_activation.crisis_name
    
    def test_get_crisis_not_found(self, client, mock_crisis_service):
        """Test hämtning av icke-existerande kris"""
        mock_crisis_service.session.get.return_value = None
        
        non_existent_id = uuid.uuid4()
        response = client.get(f"/api/v1/crisis/{non_existent_id}")
        
        assert response.status_code == 404
    
    def test_get_crisis_dashboard(self, client, mock_crisis_service):
        """Test krisdashboard endpoint"""
        from app.schemas.crisis_management import CrisisDashboardData
        
        # Mock dashboard data
        mock_dashboard = Mock()
        mock_dashboard.crisis = Mock()
        mock_dashboard.statistics = {"total_personnel": 10, "confirmed": 5}
        mock_dashboard.role_breakdown = []
        mock_dashboard.communication_timeline = []
        mock_dashboard.critical_gaps = []
        mock_dashboard.pending_escalations = []
        
        mock_crisis_service.get_crisis_dashboard_data.return_value = mock_dashboard
        
        crisis_id = uuid.uuid4()
        response = client.get(f"/api/v1/crisis/{crisis_id}/dashboard")
        
        assert response.status_code == 200
        mock_crisis_service.get_crisis_dashboard_data.assert_called_once_with(crisis_id)
    
    def test_update_crisis(self, client, mock_crisis_service, sample_crisis_activation):
        """Test uppdatering av kris"""
        mock_crisis_service.session.get.return_value = sample_crisis_activation
        
        update_data = {
            "crisis_name": "Uppdaterat Krisnamn",
            "urgency_level": 5
        }
        
        response = client.put(f"/api/v1/crisis/{sample_crisis_activation.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["crisis_name"] == "Uppdaterat Krisnamn"
    
    def test_resolve_crisis(self, client, mock_crisis_service, sample_crisis_activation):
        """Test avslutning av kris"""
        sample_crisis_activation.is_active = True
        mock_crisis_service.session.get.return_value = sample_crisis_activation
        
        response = client.post(f"/api/v1/crisis/{sample_crisis_activation.id}/resolve")
        
        assert response.status_code == 200
        data = response.json()
        assert "resolved_at" in data
        assert sample_crisis_activation.is_active is False


class TestPersonnelActivationAPI:
    """Tester för personalaktivering API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_crisis_service(self):
        with patch('app.api.crisis_management.get_crisis_management_service') as mock:
            service = Mock()
            service.session = Mock()
            mock.return_value = service
            yield service
    
    def test_get_crisis_personnel(self, client, mock_crisis_service, sample_crisis_activation):
        """Test hämtning av krispersonal"""
        # Mock service response
        mock_crisis_service.session.get.return_value = sample_crisis_activation
        mock_crisis_service.session.query.return_value.filter.return_value.all.return_value = []
        
        response = client.get(f"/api/v1/crisis/{sample_crisis_activation.id}/personnel")
        
        assert response.status_code == 200
        data = response.json()
        assert "personnel_activations" in data
        assert "total_count" in data
        assert "confirmed_count" in data
    
    def test_get_crisis_personnel_with_filters(self, client, mock_crisis_service, sample_crisis_activation):
        """Test hämtning av krispersonal med filter"""
        mock_crisis_service.session.get.return_value = sample_crisis_activation
        mock_crisis_service.session.query.return_value.filter.return_value.all.return_value = []
        
        response = client.get(
            f"/api/v1/crisis/{sample_crisis_activation.id}/personnel",
            params={"role_filter": "crisis_leader", "status_filter": "confirmed"}
        )
        
        assert response.status_code == 200
    
    def test_update_personnel_activation(self, client, mock_crisis_service, personnel_activations):
        """Test uppdatering av personalaktivering"""
        activation = personnel_activations[0]
        mock_crisis_service.session.get.return_value = activation
        
        update_data = {
            "response_status": "confirmed",
            "availability_comment": "Kan komma omgående"
        }
        
        response = client.put(f"/api/v1/crisis/personnel/{activation.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response_status"] == "confirmed"


class TestEscalationAPI:
    """Tester för eskalering API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_crisis_service(self):
        with patch('app.api.crisis_management.get_crisis_management_service') as mock:
            service = Mock()
            service.session = Mock()
            mock.return_value = service
            yield service
    
    def test_get_pending_escalations(self, client, mock_crisis_service):
        """Test hämtning av väntande eskaleringar"""
        mock_crisis_service.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        response = client.get("/api/v1/crisis/escalations/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_pending_escalations_with_filter(self, client, mock_crisis_service):
        """Test hämtning av väntande eskaleringar med operatörsfilter"""
        mock_crisis_service.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        response = client.get(
            "/api/v1/crisis/escalations/pending",
            params={"operator_filter": "Telefonist Anna"}
        )
        
        assert response.status_code == 200
    
    def test_update_escalation(self, client, mock_crisis_service, manual_escalation):
        """Test uppdatering av eskalering"""
        mock_crisis_service.session.get.return_value = manual_escalation
        
        update_data = {
            "contact_result": "confirmed",
            "contact_notes": "Kontaktad via hemtelefon",
            "contact_successful": True
        }
        
        response = client.put(f"/api/v1/crisis/escalations/{manual_escalation.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["contact_result"] == "confirmed"
        assert data["contact_successful"] is True


class TestCrisisAPIIntegration:
    """Integrationstester för Crisis API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_full_crisis_api_workflow(self, client):
        """Test komplett API-flöde för krishantering"""
        # Detta skulle kräva en mer komplex setup med riktig databas
        # och mocking av alla dependencies
        pass
    
    def test_api_error_handling(self, client):
        """Test felhantering i API"""
        # Test ogiltiga UUID:er
        invalid_uuid = "not-a-uuid"
        
        response = client.get(f"/api/v1/crisis/{invalid_uuid}")
        assert response.status_code == 422  # Validation error
        
        response = client.get(f"/api/v1/crisis/{invalid_uuid}/dashboard")
        assert response.status_code == 422
    
    def test_api_authentication(self, client):
        """Test autentisering för API endpoints"""
        # Eftersom vi använder en placeholder för autentisering,
        # testar vi bara att endpoints är tillgängliga
        # I en riktig implementation skulle vi testa JWT tokens etc.
        pass


class TestCrisisAPIValidation:
    """Tester för API-validering"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_crisis_activation_validation(self, client):
        """Test validering av krisaktivering"""
        # Test med alla obligatoriska fält
        valid_data = {
            "crisis_name": "Valid Test Crisis",
            "crisis_type": "test",
            "crisis_level": "emergency",
            "geographic_area": "Test Area",
            "primary_message": "This is a test message",
            "urgency_level": 3
        }
        
        # Denna skulle lyckas om vi hade en komplett mock setup
        # response = client.post("/api/v1/crisis/activate", json=valid_data)
        
        # Test med ogiltiga värden
        invalid_data = {
            "crisis_name": "Test",
            "crisis_type": "test",
            "crisis_level": "invalid_level",  # Ogiltigt enum-värde
            "geographic_area": "Test",
            "primary_message": "Test",
            "urgency_level": 10  # Utanför gränser (1-5)
        }
        
        response = client.post("/api/v1/crisis/activate", json=invalid_data)
        assert response.status_code == 422
    
    def test_personnel_update_validation(self, client):
        """Test validering av personaluppdatering"""
        activation_id = uuid.uuid4()
        
        # Test med giltiga värden
        valid_update = {
            "response_status": "confirmed",
            "availability_comment": "Kan komma inom 30 minuter"
        }
        
        # Test med ogiltiga värden
        invalid_update = {
            "response_status": "invalid_status",  # Ogiltigt status
            "estimated_arrival": "not-a-datetime"  # Ogiltigt datetime-format
        }
        
        response = client.put(f"/api/v1/crisis/personnel/{activation_id}", json=invalid_update)
        assert response.status_code == 422


# Hjälpfunktioner för API-tester
def create_test_crisis_data():
    """Skapa testdata för krisaktivering"""
    return {
        "crisis_name": "API Test Crisis",
        "crisis_type": "api_test",
        "crisis_level": "elevated",
        "geographic_area": "API Test Region",
        "primary_message": "This is an API test crisis",
        "urgency_level": 3,
        "use_voice_calls": True,
        "use_sms": True,
        "use_interactive_links": True,
        "max_escalation_time_minutes": 15
    }


def create_test_personnel_update():
    """Skapa testdata för personaluppdatering"""
    return {
        "response_status": "confirmed",
        "estimated_arrival": (datetime.now() + timedelta(minutes=30)).isoformat(),
        "availability_comment": "Bekräftar deltagande"
    }


def create_test_escalation_update():
    """Skapa testdata för eskaleringsuppdatering"""
    return {
        "assigned_to_operator": "Test Operator",
        "contact_result": "confirmed",
        "contact_notes": "Successfully contacted via phone",
        "contact_successful": True
    }
