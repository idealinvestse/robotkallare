# GDial - Emergency Auto-Dialer System

GDial is an automated emergency calling system that allows organizations to quickly reach multiple contacts in emergency situations.

## Features

- **Automated Emergency Calling**: Dial a list of contacts with a single click
- **Fallback Numbers**: Automatically try alternate numbers if primary contacts don't answer
- **Real-time Status**: Monitor call status through the dashboard
- **Contact Management**: Maintain a prioritized list of emergency contacts with phone number validation
- **Acknowledgment Tracking**: Record responses from call recipients
- **API-Driven**: RESTful API for integration with other systems
- **SMS Messaging**: Send SMS messages to contacts and groups

## Dashboard

GDial includes a web dashboard that provides real-time monitoring and control:

- **System Status**: View overall system health and call statistics
- **Call Logs**: Track all call attempts and responses
- **Contact Management**: View and manage emergency contacts
- **Emergency Trigger**: Initiate emergency calls with a single click

## Technical Stack

- **Backend**: Python with FastAPI
- **Database**: SQLite with SQLModel ORM
- **Telephony**: Twilio for placing calls
- **Frontend**: HTML/JavaScript dashboard

## Getting Started

### Prerequisites

- Python 3.8+
- Twilio account with a phone number

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gdial.git
   cd gdial
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your environment variables:
   ```
   cp .env.example .env
   # Edit .env with your Twilio credentials
   ```

5. Start the server:
   ```
   ./run.sh
   ```

6. Access the dashboard at http://localhost:3003

## API Endpoints

- `GET /health` - Check if the system is running
- `GET /stats` - Get call statistics
- `GET /contacts` - List all contacts
- `GET /call-logs` - View call history
- `POST /trigger-dialer` - Start emergency calls

## License

[MIT License](LICENSE)

## Acknowledgments

- Thanks to Twilio for their excellent communication APIs