# GDial Development Guide

## Project Structure

- **app/**
  - **__init__.py**: Package initialization
  - **api.py**: FastAPI endpoints and route handlers
  - **config.py**: Configuration management using environment variables
  - **database.py**: Database connection and session management
  - **dialer.py**: Core dialing functionality that makes Twilio calls
  - **importer.py**: Contact import tool for CSV files
  - **models.py**: SQLModel database models (Contact, CallLog)
  - **schemas.py**: Pydantic schemas for API responses
  - **twilio_io.py**: Twilio integration, validation and TwiML generation

- **tests/**: Test cases for all components
- **run.sh**: Application startup script
- **run_with_logging.sh**: Startup with logging to gdial.log
- **requirements.txt**: Project dependencies
- **.env**: Environment configuration (not in version control)

## Development Workflow

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run with Live Reload (Development)**
   ```bash
   uvicorn app.api:app --reload --port 3003
   ```

3. **Run with Logging**
   ```bash
   ./run_with_logging.sh
   ```

## Key Implementation Notes

### Twilio Request Validation

All Twilio webhook endpoints validate the request signature:

```python
await validate_twilio_request(request)
```

This ensures requests are legitimately from Twilio by comparing the request signature against our auth token.

### Call Flow

1. `/trigger-dialer` endpoint initiates calls to all contacts
2. For each contact, we call their primary number first
3. When a call is answered, we play a pre-recorded message and collect DTMF input
4. The response is processed at the `/dtmf` endpoint
5. If a call isn't answered, we try fallback numbers

### Database Models

- **Contact**: Stores contact information and their phone numbers
- **CallLog**: Records all call attempts and responses

## Adding New Features

1. Add tests first in the tests/ directory
2. Implement the feature
3. Run the tests: `pytest`
4. Update documentation if needed

## Deployment

- Can run as a standalone service with `./run.sh`
- Docker support for containerized deployment
- Handles both SQLite (default) and PostgreSQL

## Security Considerations

- Environment variables for sensitive credentials
- Twilio request validation
- No sensitive info in logs
