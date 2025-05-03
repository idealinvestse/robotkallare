"""
Tests for phone number utilities
"""
import pytest
from app.utils.phone_util import validate_phone_number, format_phone_for_display

def test_validate_phone_number():
    """Test phone number validation"""
    # Valid phone numbers
    assert validate_phone_number("123-456-7890") == (True, "+11234567890")
    assert validate_phone_number("(123) 456-7890") == (True, "+11234567890")
    assert validate_phone_number("123.456.7890") == (True, "+11234567890")
    assert validate_phone_number("123 456 7890") == (True, "+11234567890")
    assert validate_phone_number("11234567890") == (True, "+11234567890")
    assert validate_phone_number("1234567890") == (True, "+11234567890")
    assert validate_phone_number("+11234567890") == (True, "+11234567890")
    
    # Invalid phone numbers
    assert validate_phone_number("123-456-789") == (False, None)  # Too short
    assert validate_phone_number("abcdefghij") == (False, None)  # Non-numeric
    assert validate_phone_number("") == (False, None)  # Empty string

def test_format_phone_for_display():
    """Test phone number formatting for display"""
    assert format_phone_for_display("1234567890") == "(123) 456-7890"
    assert format_phone_for_display("11234567890") == "+1 (123) 456-7890"
    assert format_phone_for_display("+11234567890") == "+11234567890"  # Already formatted
    assert format_phone_for_display("invalid") == "invalid"  # Can't be formatted