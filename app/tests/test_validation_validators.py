"""Unit tests for validation validators."""
import pytest
from unittest.mock import patch
import uuid

from app.validation.validators import (
    ValidationError,
    validate_phone_number,
    validate_uuid,
    validate_uuid_list,
    validate_message_content,
    validate_message_type,
    validate_contact_name,
    validate_contact_email,
    validate_dtmf_digit,
    validate_dtmf_response,
    validate_request_data,
    sanitize_string_input,
    PhoneNumberValidator,
    MessageValidator,
    ContactValidator,
    DTMFValidator,
    RequestValidator
)


class TestValidationError:
    """Test ValidationError custom exception."""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError with message and field."""
        error = ValidationError("Invalid input", field="test_field")
        assert str(error) == "Invalid input"
        assert error.field == "test_field"
        assert error.details is None
    
    def test_validation_error_with_details(self):
        """Test creating ValidationError with details."""
        details = {"expected": "string", "received": "int"}
        error = ValidationError("Type mismatch", field="value", details=details)
        assert error.details == details


class TestPhoneNumberValidation:
    """Test phone number validation functions."""
    
    def test_validate_phone_number_swedish_valid(self):
        """Test valid Swedish phone numbers."""
        valid_numbers = [
            "+46701234567",
            "+46 70 123 45 67",
            "0701234567",
            "070-123 45 67"
        ]
        
        for number in valid_numbers:
            result = validate_phone_number(number)
            assert result is True
    
    def test_validate_phone_number_international_valid(self):
        """Test valid international phone numbers."""
        valid_numbers = [
            "+1234567890",
            "+44 20 7946 0958",
            "+49 30 12345678"
        ]
        
        for number in valid_numbers:
            result = validate_phone_number(number, allow_international=True)
            assert result is True
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone numbers."""
        invalid_numbers = [
            "",
            "123",
            "abc123",
            "+46 123",  # Too short
            "070123456789012345",  # Too long
            "+46 abc 123 45 67"  # Contains letters
        ]
        
        for number in invalid_numbers:
            with pytest.raises(ValidationError):
                validate_phone_number(number)
    
    def test_validate_phone_number_international_disabled(self):
        """Test international numbers when not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            validate_phone_number("+1234567890", allow_international=False)
        
        assert "Swedish phone numbers only" in str(exc_info.value)


class TestUUIDValidation:
    """Test UUID validation functions."""
    
    def test_validate_uuid_valid(self):
        """Test valid UUID strings."""
        valid_uuid = str(uuid.uuid4())
        result = validate_uuid(valid_uuid)
        assert result is True
    
    def test_validate_uuid_invalid(self):
        """Test invalid UUID strings."""
        invalid_uuids = [
            "",
            "not-a-uuid",
            "123-456-789",
            "12345678-1234-1234-1234-123456789012-extra"
        ]
        
        for invalid_uuid in invalid_uuids:
            with pytest.raises(ValidationError):
                validate_uuid(invalid_uuid)
    
    def test_validate_uuid_list_valid(self):
        """Test valid UUID list."""
        valid_uuids = [str(uuid.uuid4()) for _ in range(3)]
        result = validate_uuid_list(valid_uuids)
        assert result is True
    
    def test_validate_uuid_list_invalid(self):
        """Test invalid UUID list."""
        invalid_list = [str(uuid.uuid4()), "invalid-uuid", str(uuid.uuid4())]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid_list(invalid_list)
        
        assert "Invalid UUID at index 1" in str(exc_info.value)
    
    def test_validate_uuid_list_empty(self):
        """Test empty UUID list."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid_list([])
        
        assert "UUID list cannot be empty" in str(exc_info.value)


class TestMessageValidation:
    """Test message validation functions."""
    
    def test_validate_message_content_valid(self):
        """Test valid message content."""
        valid_messages = [
            "Hello, this is a test message.",
            "Short msg",
            "A" * 1000  # Long but within limit
        ]
        
        for message in valid_messages:
            result = validate_message_content(message)
            assert result is True
    
    def test_validate_message_content_invalid(self):
        """Test invalid message content."""
        invalid_messages = [
            "",  # Empty
            "   ",  # Only whitespace
            "A" * 2000  # Too long
        ]
        
        for message in invalid_messages:
            with pytest.raises(ValidationError):
                validate_message_content(message)
    
    def test_validate_message_type_valid(self):
        """Test valid message types."""
        valid_types = ["sms", "voice", "email"]
        
        for msg_type in valid_types:
            result = validate_message_type(msg_type)
            assert result is True
    
    def test_validate_message_type_invalid(self):
        """Test invalid message types."""
        invalid_types = ["", "invalid", "SMS", "VOICE"]  # Case sensitive
        
        for msg_type in invalid_types:
            with pytest.raises(ValidationError):
                validate_message_type(msg_type)


class TestContactValidation:
    """Test contact validation functions."""
    
    def test_validate_contact_name_valid(self):
        """Test valid contact names."""
        valid_names = [
            "John Doe",
            "Anna-Lisa Svensson",
            "José María",
            "李小明"  # Unicode characters
        ]
        
        for name in valid_names:
            result = validate_contact_name(name)
            assert result is True
    
    def test_validate_contact_name_invalid(self):
        """Test invalid contact names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Only whitespace
            "A",  # Too short
            "A" * 101,  # Too long
            "John<script>",  # Potential XSS
            "DROP TABLE users"  # Potential SQL injection
        ]
        
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_contact_name(name)
    
    def test_validate_contact_email_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name+tag@domain.co.uk",
            "firstname.lastname@company.org"
        ]
        
        for email in valid_emails:
            result = validate_contact_email(email)
            assert result is True
    
    def test_validate_contact_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "",
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user name@domain.com"  # Space in local part
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_contact_email(email)


class TestDTMFValidation:
    """Test DTMF validation functions."""
    
    def test_validate_dtmf_digit_valid(self):
        """Test valid DTMF digits."""
        valid_digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "#"]
        
        for digit in valid_digits:
            result = validate_dtmf_digit(digit)
            assert result is True
    
    def test_validate_dtmf_digit_invalid(self):
        """Test invalid DTMF digits."""
        invalid_digits = ["", "a", "10", "**", "##"]
        
        for digit in invalid_digits:
            with pytest.raises(ValidationError):
                validate_dtmf_digit(digit)
    
    def test_validate_dtmf_response_valid(self):
        """Test valid DTMF responses."""
        valid_responses = [
            "123",
            "*0#",
            "1*2#3",
            "#"
        ]
        
        for response in valid_responses:
            result = validate_dtmf_response(response)
            assert result is True
    
    def test_validate_dtmf_response_invalid(self):
        """Test invalid DTMF responses."""
        invalid_responses = [
            "",
            "abc",
            "1a2",
            "1" * 21  # Too long
        ]
        
        for response in invalid_responses:
            with pytest.raises(ValidationError):
                validate_dtmf_response(response)


class TestRequestValidation:
    """Test request data validation."""
    
    def test_validate_request_data_valid(self):
        """Test valid request data."""
        valid_data = {
            "name": "John Doe",
            "phone": "+46701234567",
            "message": "Hello world"
        }
        
        schema = {
            "name": {"type": "string", "required": True, "min_length": 2},
            "phone": {"type": "phone", "required": True},
            "message": {"type": "string", "required": True}
        }
        
        result = validate_request_data(valid_data, schema)
        assert result is True
    
    def test_validate_request_data_missing_required(self):
        """Test request data with missing required field."""
        invalid_data = {
            "name": "John Doe"
            # Missing required phone field
        }
        
        schema = {
            "name": {"type": "string", "required": True},
            "phone": {"type": "phone", "required": True}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_request_data(invalid_data, schema)
        
        assert "Required field 'phone' is missing" in str(exc_info.value)
    
    def test_validate_request_data_invalid_type(self):
        """Test request data with invalid field type."""
        invalid_data = {
            "name": 123,  # Should be string
            "phone": "+46701234567"
        }
        
        schema = {
            "name": {"type": "string", "required": True},
            "phone": {"type": "phone", "required": True}
        }
        
        with pytest.raises(ValidationError):
            validate_request_data(invalid_data, schema)


class TestSanitization:
    """Test input sanitization functions."""
    
    def test_sanitize_string_input_normal(self):
        """Test sanitizing normal string input."""
        input_str = "Hello, World!"
        result = sanitize_string_input(input_str)
        assert result == "Hello, World!"
    
    def test_sanitize_string_input_html(self):
        """Test sanitizing HTML input."""
        input_str = "<script>alert('xss')</script>Hello"
        result = sanitize_string_input(input_str)
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_string_input_sql(self):
        """Test sanitizing potential SQL injection."""
        input_str = "'; DROP TABLE users; --"
        result = sanitize_string_input(input_str)
        assert "DROP TABLE" not in result
    
    def test_sanitize_string_input_whitespace(self):
        """Test sanitizing whitespace."""
        input_str = "  Hello   World  "
        result = sanitize_string_input(input_str, strip_whitespace=True)
        assert result == "Hello   World"
    
    def test_sanitize_string_input_max_length(self):
        """Test sanitizing with max length."""
        input_str = "A" * 100
        result = sanitize_string_input(input_str, max_length=50)
        assert len(result) == 50


class TestValidatorClasses:
    """Test validator classes."""
    
    def test_phone_number_validator(self):
        """Test PhoneNumberValidator class."""
        validator = PhoneNumberValidator()
        
        # Valid phone number
        assert validator.validate("+46701234567") is True
        
        # Invalid phone number
        with pytest.raises(ValidationError):
            validator.validate("invalid")
    
    def test_message_validator(self):
        """Test MessageValidator class."""
        validator = MessageValidator()
        
        # Valid message
        assert validator.validate_content("Hello world") is True
        assert validator.validate_type("sms") is True
        
        # Invalid message
        with pytest.raises(ValidationError):
            validator.validate_content("")
        
        with pytest.raises(ValidationError):
            validator.validate_type("invalid")
    
    def test_contact_validator(self):
        """Test ContactValidator class."""
        validator = ContactValidator()
        
        # Valid contact data
        assert validator.validate_name("John Doe") is True
        assert validator.validate_email("john@example.com") is True
        
        # Invalid contact data
        with pytest.raises(ValidationError):
            validator.validate_name("")
        
        with pytest.raises(ValidationError):
            validator.validate_email("invalid-email")
    
    def test_dtmf_validator(self):
        """Test DTMFValidator class."""
        validator = DTMFValidator()
        
        # Valid DTMF data
        assert validator.validate_digit("1") is True
        assert validator.validate_response("123*") is True
        
        # Invalid DTMF data
        with pytest.raises(ValidationError):
            validator.validate_digit("a")
        
        with pytest.raises(ValidationError):
            validator.validate_response("abc")
    
    def test_request_validator(self):
        """Test RequestValidator class."""
        validator = RequestValidator()
        
        # Valid request
        data = {"name": "John", "age": 25}
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": False}
        }
        
        assert validator.validate(data, schema) is True
        
        # Invalid request
        invalid_data = {"age": 25}  # Missing required name
        
        with pytest.raises(ValidationError):
            validator.validate(invalid_data, schema)


class TestValidationIntegration:
    """Test validation integration scenarios."""
    
    def test_full_contact_validation(self):
        """Test complete contact validation scenario."""
        contact_data = {
            "name": "Anna Svensson",
            "phone": "+46701234567",
            "email": "anna@example.com"
        }
        
        # Validate each field
        assert validate_contact_name(contact_data["name"]) is True
        assert validate_phone_number(contact_data["phone"]) is True
        assert validate_contact_email(contact_data["email"]) is True
    
    def test_full_message_validation(self):
        """Test complete message validation scenario."""
        message_data = {
            "type": "sms",
            "content": "Hello, this is a test message!",
            "recipients": [str(uuid.uuid4()), str(uuid.uuid4())]
        }
        
        # Validate each field
        assert validate_message_type(message_data["type"]) is True
        assert validate_message_content(message_data["content"]) is True
        assert validate_uuid_list(message_data["recipients"]) is True
    
    def test_sanitization_integration(self):
        """Test sanitization with validation."""
        potentially_malicious_input = "<script>alert('xss')</script>John Doe"
        
        # Sanitize first
        sanitized = sanitize_string_input(potentially_malicious_input)
        
        # Then validate
        assert validate_contact_name(sanitized) is True
        assert "<script>" not in sanitized
    
    @pytest.mark.parametrize("phone_number,expected", [
        ("+46701234567", True),
        ("0701234567", True),
        ("+1234567890", True),
        ("invalid", False),
        ("", False)
    ])
    def test_phone_validation_parametrized(self, phone_number, expected):
        """Test phone validation with parametrized inputs."""
        if expected:
            assert validate_phone_number(phone_number, allow_international=True) is True
        else:
            with pytest.raises(ValidationError):
                validate_phone_number(phone_number)
    
    def test_validation_error_chaining(self):
        """Test validation error handling in chains."""
        try:
            # This should raise ValidationError
            validate_phone_number("")
        except ValidationError as e:
            # Re-raise with additional context
            raise ValidationError(
                f"Contact validation failed: {str(e)}",
                field="contact.phone",
                details={"original_error": str(e)}
            )
        except Exception:
            pytest.fail("Expected ValidationError")
    
    def test_async_validation_compatibility(self):
        """Test that validators work in async contexts."""
        import asyncio
        
        async def async_validate():
            # These should work in async context
            assert validate_phone_number("+46701234567") is True
            assert validate_message_content("Test message") is True
            return True
        
        # Run async validation
        result = asyncio.run(async_validate())
        assert result is True
