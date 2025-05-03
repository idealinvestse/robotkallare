/**
 * Client-side phone number validation utilities
 */

// Validate phone number format
function validatePhoneNumber(phoneNumber) {
    if (!phoneNumber) return { isValid: false, message: "Phone number is required" };
    
    // Remove spaces, dashes, parentheses, dots
    const cleaned = phoneNumber.replace(/[\s\-\(\)\.\+]/g, "");
    
    // Check if it contains only digits after cleaning
    if (!/^\d+$/.test(cleaned)) {
        return { isValid: false, message: "Phone number should contain only digits, spaces, and punctuation" };
    }
    
    // Check length - most countries have phone numbers between 8 and 15 digits
    if (cleaned.length < 7 || cleaned.length > 15) {
        return { isValid: false, message: "Phone number length is invalid" };
    }
    
    return { isValid: true, message: "" };
}

// Format a phone number for display
function formatPhoneForDisplay(phoneNumber) {
    // For Swedish numbers or general formatting
    const digits = phoneNumber.replace(/\D/g, "");
    
    // Convert to Swedish format by default if no country code
    if (digits.length === 9 && !phoneNumber.startsWith("+")) {
        return `+46 ${digits.substring(0, 3)} ${digits.substring(3, 6)} ${digits.substring(6)}`;
    } else if (digits.length === 10 && !phoneNumber.startsWith("+")) {
        // Handle 10-digit Swedish numbers (with leading 0)
        if (digits.startsWith("0")) {
            return `+46 ${digits.substring(1, 4)} ${digits.substring(4, 7)} ${digits.substring(7)}`;
        }
        // US format as fallback for 10 digits
        return `(${digits.substring(0, 3)}) ${digits.substring(3, 6)}-${digits.substring(6)}`;
    } else if (digits.length === 11 && digits.startsWith("1") && !phoneNumber.startsWith("+")) {
        return `+1 (${digits.substring(1, 4)}) ${digits.substring(4, 7)}-${digits.substring(7)}`;
    } else if (phoneNumber.startsWith("+")) {
        return phoneNumber; // Keep international format as is
    }
    
    // Return as-is if we can't determine format
    return phoneNumber;
}

// Add validation to phone input fields
function setupPhoneValidation() {
    const phoneInputs = document.querySelectorAll('.phone-input');
    
    phoneInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const result = validatePhoneNumber(this.value);
            const feedbackElement = this.nextElementSibling;
            
            if (!result.isValid) {
                this.classList.add('is-invalid');
                if (feedbackElement) {
                    feedbackElement.textContent = result.message;
                    feedbackElement.style.display = 'block';
                }
            } else {
                this.classList.remove('is-invalid');
                if (feedbackElement) {
                    feedbackElement.style.display = 'none';
                }
                
                // Format the phone number for display if valid
                this.value = formatPhoneForDisplay(this.value);
            }
        });
    });
}

// Call this function when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupPhoneValidation();
});