# GDial Group Messenger Feature

The Group Messenger is a new feature of GDial that provides a more manageable interface for sending notifications to large groups of contacts. This document outlines the implementation details and usage guidelines.

## Features

- **Card-Based Contact Management**: Displays contacts as cards with clear status indicators
- **Efficient Group Selection**: Easily select contacts from specific groups or all contacts
- **Message Type Switching**: Toggle between voice calls and SMS messages
- **Status Tracking**: Real-time status updates for message delivery
- **Search & Filtering**: Quickly find specific contacts
- **Batch Operations**: Select and send to multiple contacts at once
- **Retry Capabilities**: Easily retry failed messages

## Implementation Files

The feature is implemented using the following files:

- `static/group-messenger.html` - The main HTML page for the feature
- `static/js/group-messenger.js` - JavaScript component that handles the UI logic
- `static/css/group-messenger.css` - Styling for the group messenger interface
- `static/css/header.css` - Common header styling shared with the main application

## Usage Guide

### Accessing the Group Messenger

You can access the Group Messenger in two ways:
1. Directly navigate to `/static/group-messenger.html`
2. Click the "Group Messenger" link in the main application header

### Sending to a Group

1. **Select Message Type**: Choose between "Voice Call" or "SMS"
2. **Select Message**: Choose a message from the dropdown (filtered by message type)
3. **Select Group**: Choose a contact group or "All Contacts"
4. **Select Recipients**: 
   - Use the search field to filter contacts
   - Click individual contacts to select them
   - Use "Select All" / "Deselect All" buttons for batch selection
5. **Send Messages**: 
   - Click "Send to Selected" to send to all selected contacts
   - Click "Send" on individual contact cards to send to just that contact

### Understanding Status Indicators

Contact cards display a colored border and status badge with the following meanings:

- **Gray (Pending)**: Message not yet sent
- **Blue (Sending)**: Message is being processed
- **Green (Success)**: Message was successfully delivered
- **Red (Failed)**: Message delivery failed

For failed messages, a "Retry" button appears on the contact card, allowing a quick resend.

## Technical Details

### Data Flow

The component fetches data from the following API endpoints:
- `/messages` - To populate the message dropdown
- `/groups` - To populate the group dropdown
- `/contacts` or `/groups/{group_id}` - To fetch contacts

When sending messages, it uses:
- `/trigger-manual-call` - For voice calls
- `/trigger-sms` - For SMS messages

### State Management

The component maintains the following internal state:
- List of all contacts
- Set of selected contact IDs
- Message delivery status for each contact
- Current message ID and type
- Current group ID
- Current search term

### Responsive Design

The interface is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## Future Enhancements

Potential improvements for future versions:

1. **Scheduled Messages**: Add the ability to schedule messages for later delivery
2. **Delivery Reports**: More detailed delivery reporting and analytics
3. **Contact Management**: Edit contacts directly from the interface
4. **Template Creation**: Create new message templates directly in the interface
5. **Search Improvements**: Advanced search filters (by status, phone, etc.)
6. **Saved Selections**: Save and reuse contact selections
7. **Export/Import**: Export results and import contact lists