# GDial Settings Implementation Plan

## Current Structure Analysis

The GDial settings system currently consists of:

1. **SQLModel Database Models:**
   - `SystemSetting`: Key-value storage with type conversion for general settings
   - `DtmfSetting`: Settings specific to DTMF call responses
   - `SmsSettings`: Configuration for SMS delivery 
   - `NotificationSettings`: Admin notification preferences

2. **API Endpoints:**
   - Complete CRUD operations for all setting types
   - Group-based retrieval for system settings
   - Bulk update capability

3. **Usage Pattern:**
   - Settings initialized at app startup
   - Central access through get_*_settings() functions
   - Environment variables used for core system configuration

## High-Value Settings to Implement

Based on the recommended settings and current application structure, these are the most valuable settings to implement:

### 1. System Settings (General)

| Key | Value Type | Description | Default | Justification |
|-----|------------|-------------|---------|---------------|
| `timezone` | string | System default timezone | "UTC" | Critical for proper time display in logs and UI |
| `language` | string | Default UI language | "en-US" | Essential for internationalization |
| `max_concurrent_calls` | int | Maximum concurrent outbound calls | 50 | Performance and rate limiting |
| `max_concurrent_sms` | int | Maximum concurrent SMS messages | 200 | Performance and rate limiting |
| `maintenance_mode` | boolean | Put system in maintenance mode | false | Operational control |

### 2. Call Settings

| Key | Value Type | Description | Default | Justification |
|-----|------------|-------------|---------|---------------|
| `default_voice` | string | Default TTS voice to use | "alice" | Customization of voice calls |
| `call_recording` | boolean | Record outgoing calls | false | Compliance and verification |
| `voicemail_detection` | boolean | Enable voicemail detection | true | Improved call success rate |
| `voicemail_action` | string | Action on voicemail detection | "leave_message" | Call handling |
| `call_retry_delay_min` | int | Minutes between retry attempts | 5 | Refined retry strategy |

### 3. DTMF Settings Enhancements

| Key | Value Type | Description | Default | Justification |
|-----|------------|-------------|---------|---------------|
| `repeat_message_digit` | string | Digit to press to repeat message | "0" | Improves user experience |
| `confirm_receipt_digit` | string | Digit to confirm receipt | "1" | Standardizes input |
| `dtmf_menu_style` | string | Menu presentation style | "standard" | Improves clarity |

### 4. SMS Settings Enhancements

| Key | Value Type | Description | Default | Justification |
|-----|------------|-------------|---------|---------------|
| `sms_rate_limit_per_second` | int | Maximum SMS per second | 10 | Rate limiting |
| `allow_opt_out` | boolean | Allow recipients to opt out | true | Compliance requirement |
| `opt_out_keyword` | string | Keyword for opting out | "STOP" | Standard practice |

### 5. Security Settings

| Key | Value Type | Description | Default | Justification |
|-----|------------|-------------|---------|---------------|
| `force_https` | boolean | Force HTTPS for all connections | true | Basic security |
| `sensitive_data_masking` | boolean | Mask sensitive data in logs | true | Data protection |
| `auto_logout_inactive_min` | int | Auto-logout after inactivity | 30 | Security best practice |

## Implementation Steps

### 1. Add to System Settings Initialization

Update `app/settings.py` to add new system settings, including:
- timezone
- language
- max_concurrent_calls
- max_concurrent_sms
- maintenance_mode
- and other key system settings

### 2. Extend DTMF Settings Model

Update `app/models/settings.py` to add new fields to the `DtmfSetting` model:
- repeat_message_digit
- confirm_receipt_digit
- dtmf_menu_style

### 3. Extend SMS Settings Model

Update `app/models/settings.py` to add new fields to the `SmsSettings` model:
- sms_rate_limit_per_second
- allow_opt_out
- opt_out_keyword

### 4. Create Security Settings Model

Create a new `SecuritySettings` model in `app/models/settings.py`:
- force_https
- sensitive_data_masking
- auto_logout_inactive_min

### 5. Update Schemas

Update the corresponding schema files in `app/schemas/settings.py` to match the new model fields.

### 6. Add API Endpoints

Extend `app/settings_api.py` with new endpoints for the security settings.

### 7. Add UI Integration

Ensure the settings UI can display and edit the new settings by category.

## Implementation Priority

1. System settings (Highest priority due to core functionality)
2. Call and DTMF settings (High priority due to direct impact on core functionality)
3. SMS settings (Medium-high priority)
4. Security settings (Medium priority)

The plan focuses on implementing the most impactful settings first while ensuring backward compatibility with the existing application structure.