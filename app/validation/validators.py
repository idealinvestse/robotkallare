"""Input validation utilities for API endpoints and data processing."""
import re
import uuid
import logging
from typing import Any, List, Optional, Dict, Union
from datetime import datetime
from pydantic import BaseModel, Field
try:
    from pydantic import validator
except ImportError:
    from pydantic.v1 import validator

try:
    from pydantic.validators import str_validator
except ImportError:
    # Fallback for newer Pydantic versions
    def str_validator(v):
        return str(v) if v is not None else v

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error with detailed information."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class PhoneNumberValidator:
    """Validator for phone numbers with international support."""
    
    # Swedish phone number patterns
    SWEDISH_MOBILE_PATTERN = re.compile(r'^(\+46|0)7[0-9]{8}$')
    SWEDISH_LANDLINE_PATTERN = re.compile(r'^(\+46|0)[1-9][0-9]{7,8}$')
    
    # International phone number pattern (E.164 format)
    INTERNATIONAL_PATTERN = re.compile(r'^\+[1-9]\d{1,14}$')
    
    @classmethod
    def validate_phone_number(cls, phone: str, allow_international: bool = True) -> str:
        """
        Validate and normalize phone number.
        
        Args:
            phone: Phone number to validate
            allow_international: Whether to allow international numbers
            
        Returns:
            Normalized phone number
            
        Raises:
            ValidationError: If phone number is invalid
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone number is required and must be a string", "phone", phone)
        
        # Clean the phone number
        cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())
        
        # Check Swedish mobile
        if cls.SWEDISH_MOBILE_PATTERN.match(cleaned):
            # Normalize to international format
            if cleaned.startswith('0'):
                return '+46' + cleaned[1:]
            return cleaned
        
        # Check Swedish landline
        if cls.SWEDISH_LANDLINE_PATTERN.match(cleaned):
            # Normalize to international format
            if cleaned.startswith('0'):
                return '+46' + cleaned[1:]
            return cleaned
        
        # Check international format
        if allow_international and cls.INTERNATIONAL_PATTERN.match(cleaned):
            return cleaned
        
        raise ValidationError(
            f"Invalid phone number format: {phone}. Expected Swedish or international format.",
            "phone",
            phone
        )
    
    @classmethod
    def is_swedish_number(cls, phone: str) -> bool:
        """Check if phone number is Swedish."""
        try:
            normalized = cls.validate_phone_number(phone)
            return normalized.startswith('+46')
        except ValidationError:
            return False


class UUIDValidator:
    """Validator for UUID fields."""
    
    @classmethod
    def validate_uuid(cls, value: Union[str, uuid.UUID], field_name: str = "id") -> uuid.UUID:
        """
        Validate and convert UUID.
        
        Args:
            value: UUID string or UUID object
            field_name: Name of the field for error messages
            
        Returns:
            UUID object
            
        Raises:
            ValidationError: If UUID is invalid
        """
        if value is None:
            raise ValidationError(f"{field_name} is required", field_name, value)
        
        if isinstance(value, uuid.UUID):
            return value
        
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                raise ValidationError(
                    f"Invalid UUID format for {field_name}: {value}",
                    field_name,
                    value
                )
        
        raise ValidationError(
            f"{field_name} must be a valid UUID string or UUID object",
            field_name,
            value
        )
    
    @classmethod
    def validate_uuid_list(cls, values: List[Union[str, uuid.UUID]], field_name: str = "ids") -> List[uuid.UUID]:
        """
        Validate a list of UUIDs.
        
        Args:
            values: List of UUID strings or UUID objects
            field_name: Name of the field for error messages
            
        Returns:
            List of UUID objects
            
        Raises:
            ValidationError: If any UUID is invalid
        """
        if not isinstance(values, list):
            raise ValidationError(f"{field_name} must be a list", field_name, values)
        
        if not values:
            raise ValidationError(f"{field_name} cannot be empty", field_name, values)
        
        validated_uuids = []
        for i, value in enumerate(values):
            try:
                validated_uuids.append(cls.validate_uuid(value, f"{field_name}[{i}]"))
            except ValidationError as e:
                raise ValidationError(
                    f"Invalid UUID at index {i} in {field_name}: {e.message}",
                    field_name,
                    values
                )
        
        return validated_uuids


class MessageValidator:
    """Validator for message content and properties."""
    
    MAX_MESSAGE_LENGTH = 1000
    MIN_MESSAGE_LENGTH = 1
    
    @classmethod
    def validate_message_content(cls, content: str, max_length: int = None) -> str:
        """
        Validate message content.
        
        Args:
            content: Message content to validate
            max_length: Optional custom max length
            
        Returns:
            Validated message content
            
        Raises:
            ValidationError: If content is invalid
        """
        if not content or not isinstance(content, str):
            raise ValidationError("Message content is required and must be a string", "content", content)
        
        content = content.strip()
        max_len = max_length or cls.MAX_MESSAGE_LENGTH
        
        if len(content) < cls.MIN_MESSAGE_LENGTH:
            raise ValidationError(
                f"Message content must be at least {cls.MIN_MESSAGE_LENGTH} character(s)",
                "content",
                content
            )
        
        if len(content) > max_len:
            raise ValidationError(
                f"Message content must not exceed {max_len} characters",
                "content",
                content
            )
        
        return content
    
    @classmethod
    def validate_message_type(cls, message_type: str) -> str:
        """
        Validate message type.
        
        Args:
            message_type: Message type to validate
            
        Returns:
            Validated message type
            
        Raises:
            ValidationError: If message type is invalid
        """
        valid_types = ["sms", "voice", "both"]
        
        if not message_type or not isinstance(message_type, str):
            raise ValidationError("Message type is required and must be a string", "message_type", message_type)
        
        message_type = message_type.lower().strip()
        
        if message_type not in valid_types:
            raise ValidationError(
                f"Invalid message type: {message_type}. Must be one of: {', '.join(valid_types)}",
                "message_type",
                message_type
            )
        
        return message_type


class ContactValidator:
    """Validator for contact information."""
    
    @classmethod
    def validate_contact_name(cls, name: str) -> str:
        """
        Validate contact name.
        
        Args:
            name: Contact name to validate
            
        Returns:
            Validated contact name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Contact name is required and must be a string", "name", name)
        
        name = name.strip()
        
        if len(name) < 1:
            raise ValidationError("Contact name cannot be empty", "name", name)
        
        if len(name) > 100:
            raise ValidationError("Contact name must not exceed 100 characters", "name", name)
        
        # Check for potentially dangerous characters
        if re.search(r'[<>"\']', name):
            raise ValidationError("Contact name contains invalid characters", "name", name)
        
        return name
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Validated email address
            
        Raises:
            ValidationError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string", "email", email)
        
        email = email.strip().lower()
        
        # Basic email pattern
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not email_pattern.match(email):
            raise ValidationError(f"Invalid email format: {email}", "email", email)
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address is too long", "email", email)
        
        return email


class DTMFValidator:
    """Validator for DTMF responses and configurations."""
    
    VALID_DTMF_DIGITS = set('0123456789*#')
    
    @classmethod
    def validate_dtmf_digit(cls, digit: str) -> str:
        """
        Validate DTMF digit.
        
        Args:
            digit: DTMF digit to validate
            
        Returns:
            Validated DTMF digit
            
        Raises:
            ValidationError: If digit is invalid
        """
        if not digit or not isinstance(digit, str):
            raise ValidationError("DTMF digit is required and must be a string", "digit", digit)
        
        digit = digit.strip()
        
        if len(digit) != 1:
            raise ValidationError("DTMF digit must be exactly one character", "digit", digit)
        
        if digit not in cls.VALID_DTMF_DIGITS:
            raise ValidationError(
                f"Invalid DTMF digit: {digit}. Must be one of: {', '.join(sorted(cls.VALID_DTMF_DIGITS))}",
                "digit",
                digit
            )
        
        return digit
    
    @classmethod
    def validate_dtmf_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate DTMF response configuration.
        
        Args:
            response: DTMF response configuration
            
        Returns:
            Validated DTMF response configuration
            
        Raises:
            ValidationError: If response is invalid
        """
        if not isinstance(response, dict):
            raise ValidationError("DTMF response must be a dictionary", "dtmf_response", response)
        
        required_fields = ["digit", "action"]
        for field in required_fields:
            if field not in response:
                raise ValidationError(f"DTMF response missing required field: {field}", field, response)
        
        # Validate digit
        response["digit"] = cls.validate_dtmf_digit(response["digit"])
        
        # Validate action
        valid_actions = ["confirm", "repeat", "transfer", "callback", "custom"]
        action = response.get("action", "").lower().strip()
        
        if action not in valid_actions:
            raise ValidationError(
                f"Invalid DTMF action: {action}. Must be one of: {', '.join(valid_actions)}",
                "action",
                response
            )
        
        response["action"] = action
        
        return response


def validate_request_data(data: Dict[str, Any], validators: Dict[str, callable]) -> Dict[str, Any]:
    """
    Validate request data using provided validators.
    
    Args:
        data: Request data to validate
        validators: Dictionary mapping field names to validator functions
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    validated_data = {}
    errors = []
    
    for field, validator_func in validators.items():
        if field in data:
            try:
                validated_data[field] = validator_func(data[field])
            except ValidationError as e:
                errors.append(f"{field}: {e.message}")
            except Exception as e:
                errors.append(f"{field}: Validation error - {str(e)}")
    
    if errors:
        raise ValidationError(f"Validation failed: {'; '.join(errors)}")
    
    return validated_data


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent injection attacks.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If string is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string", "value", value)
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Check length
    if len(sanitized) > max_length:
        raise ValidationError(f"String too long (max {max_length} characters)", "value", value)
    
    return sanitized
