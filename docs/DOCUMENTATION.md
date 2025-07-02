# GDial - Emergency Notification System

This documentation provides instructions for setting up, running, and managing the GDial emergency notification system.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Starting the Server](#starting-the-server)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [API Documentation](#api-documentation)
7. [Troubleshooting](#troubleshooting)

## Overview

GDial is an emergency notification system designed to reach contacts through voice calls and SMS messages. The system supports both emergency and normal notifications with configurable delivery methods and response handling.

Key features:
- Voice call notifications with DTMF response handling
- SMS notifications with configurable content
- Group management for organizing contacts
- Manual handling for failed notification attempts
- Extensive configuration options for customizing behavior

## Installation

### Prerequisites

- Python 3.10+
- SQLite3
- Twilio account (for voice calls and SMS)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gdial.git
   cd gdial
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment variables by creating a `.env` file:
   ```
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_FROM_NUMBER=your_twilio_phone_number
   PUBLIC_URL=your_public_url  # Used for Twilio callbacks
   ```

## Starting the Server

There are two primary methods to start the GDial server:

### 1. Standard Start (without detailed logging)

Run the application using the standard script:

```bash
./run.sh
```

This script activates the virtual environment and starts the FastAPI server on the default port (3003).

### 2. Start with Logging

For more detailed logging during development or troubleshooting:

```bash
./run_with_logging.sh
```

This script will start the server with enhanced logging that shows detailed information about the system's operation, including API calls, Twilio interactions, and more.

### Server Configuration

The server runs on port 3003 by default. You can modify this in the following ways:

- Change the `API_PORT` environment variable in your `.env` file
- Edit the port number in the run scripts

The web interface will be available at:

```
http://localhost:3003
```

### Running in Production

For production environments, it's recommended to:

1. Use a process manager like Supervisor or systemd
2. Set up HTTPS with a proper certificate
3. Configure a reverse proxy (Nginx or Apache)

Example systemd service file (`/etc/systemd/system/gdial.service`):

```ini
[Unit]
Description=GDial Emergency Notification System
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/gdial
ExecStart=/path/to/gdial/run.sh
Restart=on-failure
RestartSec=5
Environment=PRODUCTION=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable gdial
sudo systemctl start gdial
```

## Configuration

GDial offers extensive configuration options through the web interface. Key configuration areas include:

1. **Notification Settings**
   - Email notifications for system events
   - Alert settings for failures and emergencies

2. **Call Timeout Settings**
   - Call timeout duration
   - Secondary attempt delay
   - Maximum retry attempts

3. **Ring Order Settings**
   - Normal vs. emergency call behavior
   - Sequential or parallel calling options
   - Number selection strategies

4. **SMS Settings**
   - SMS message format
   - Default prefixes and signatures

5. **Voice Call Settings**
   - Text-to-speech voice selection
   - Speech rate configuration
   - Message repetition settings

6. **DTMF Response Settings**
   - Customize response messages for keypad inputs

All settings can be configured through the Settings tab in the web interface.

## Usage Guide

### Basic Workflow

1. **Set up contacts and groups**
   - Add individual contacts with phone numbers
   - Organize contacts into groups for targeted notifications

2. **Create message templates**
   - Create reusable message templates for different scenarios
   - Specify if templates are for voice, SMS, or both

3. **Send notifications**
   - Choose between emergency and normal notifications
   - Select voice calls, SMS, or both delivery methods
   - Target all contacts or specific groups

4. **Monitor results**
   - View call and SMS logs
   - Handle manual calls for failed notification attempts

### Sending Configured Messages

1. Click "Send Configured Message" on the dashboard
2. Select a message from the dropdown
3. Choose delivery method (voice, SMS, or both)
4. Select message priority (normal or emergency)
5. Choose target audience (all contacts or specific group)
6. Click "Send Message" to initiate the notification

### Managing Manual Calls

The "Manual Handling" tab shows contacts that couldn't be reached automatically. 
Use this interface to:

1. View contacts requiring manual follow-up
2. See details of the attempted notification
3. Mark calls as completed after manual handling

## API Documentation

GDial provides a RESTful API for integration with other systems. Key endpoints include:

- `/send-message` - Send a configured message
- `/contacts` - Manage contacts
- `/groups` - Manage contact groups
- `/messages` - Manage message templates
- `/dtmf-responses` - Configure DTMF response messages

See the API section for detailed endpoint documentation.

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if another process is using port 3003
   - Verify the virtual environment is activated
   - Ensure all dependencies are installed

2. **Calls not being made**
   - Verify Twilio credentials in .env file
   - Check PUBLIC_URL is accessible from the internet
   - Review logs for specific Twilio errors

3. **Database errors**
   - Ensure the application has write permissions to the directory
   - Check for database corruption

### Log Files

Important log files to check:
- `gdial.log` - Main application log
- `server.log` - Server-related messages
- `startup.log` - Server startup information

Use the following command to view logs in real-time:
```bash
tail -f gdial.log
```

For additional help, please contact the system administrator.