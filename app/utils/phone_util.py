"""
Phone number utility functions
"""
import re
from typing import Optional, Tuple

def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validates phone number format and returns:
    - boolean indicating if valid
    - normalized version of the phone number
    
    Handles:
    - Different delimiters (spaces, dashes, dots, parentheses)
    - Country codes with or without + prefix
    - Extra whitespace
    """
    # Remove all non-digit characters
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    
    # Handle various formats
    if cleaned.startswith('+'):
        # International format
        if len(cleaned) < 8 or len(cleaned) > 15:  # Including + and country code
            return False, None
        return True, cleaned
    else:
        # Assume US format if no country code
        if len(cleaned) == 10:
            # Standard US 10-digit
            return True, f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            # US with leading 1
            return True, f"+{cleaned}"
        else:
            return False, None

def format_phone_for_display(phone: str) -> str:
    """Format a phone number for display purposes"""
    # Keep as is if already has a plus sign
    if phone.startswith('+'):
        return phone
        
    # Remove all non-digit characters
    digits = re.sub(r'[^\d]', '', phone)
    
    # Format based on length
    if len(digits) == 10:  # US number without country code
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11 and digits.startswith('1'):  # US with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    else:
        # Return as is if we can't determine format
        return phone