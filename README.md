# Auto-Dialer System

A minimal system that automatically calls a defined group of contacts, collects a simple acknowledgment via DTMF, and handles unanswered calls with a fallback flow.

## Setup

1. Copy `.env.example` to `.env` and fill in your Twilio credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to include `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER`.

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   ./run.sh
   ```

## Usage

- **Import contacts**:
  ```bash
  python app/importer.py contacts.csv
  ```
  CSV format: `name,phone1,phone2,...` (phone numbers in E.164 format, e.g., `+46701234567`).

 - **Trigger dialer**:
   ```bash
   curl -X POST http://titanic.urem.org:3003/trigger-dialer
   ```

 - **Check stats**:
   ```bash
   curl http://titanic.urem.org:3003/stats
   ```

 - **Health check**:
   ```bash
   curl http://titanic.urem.org:3003/health
   ```

## Testing

Run tests with:
```bash
pytest
```

## Notes

- The system uses SQLite by default. To switch to Postgres, update `SQLITE_DB` in `.env` to a Postgres connection string.
- Ensure the pre-recorded message URL in `twilio_io.py` is valid.
- Logs are stored in the `CallLog` table for auditing.
