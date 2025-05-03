# GDial - Emergency Auto-Dialer System

GDial is an automated emergency calling system that allows organizations to quickly reach multiple contacts in emergency situations.

## Svensk sammanfattning

GDial är ett automatiserat nödsamtalssystem som låter organisationer snabbt nå flera kontakter i krissituationer. Systemet består av:
- En RESTful API-server byggd med FastAPI.
- En RabbitMQ-baserad kö för asynkron Text-till-tal (TTS).
- Skalbara worker-processer (Google TTS & Coqui).
- Ett webbaserat dashboard för realtidsövervakning.

API:et erbjuder endpoints för:
- Skapa TTS-jobb (`POST /tts/jobs`)
- Hämta TTS-jobbstatus (`GET /tts/jobs/{job_id}`)
- Ladda ner ljudfil (`GET /tts/audio/{job_id}`)

Systemet kan skalas horisontellt genom att starta flera worker-instanser parallellt.

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
- `POST /tts/jobs` - Submit a new TTS job (async)
- `GET /tts/jobs/{job_id}` - Get status of a TTS job
- `GET /tts/audio/{job_id}` - Download the generated audio file (when ready)

---

## Text-to-Speech (TTS) - Asynchronous & Scalable

GDial använder en asynkron och skalbar TTS-arkitektur där all TTS-generering sker i separata worker-processer via en jobbkö (RabbitMQ). Detta möjliggör hög prestanda och oberoende skalning av TTS-tjänsten.

### TTS-arkitektur

```mermaid
flowchart TD
    subgraph API & Dashboard
        A[API: /tts/jobs] -->|Lägger till jobb| Q(RabbitMQ: "gdial.tts")
        B[API: /tts/jobs/{job_id}] -.->|Pollar status| S[Jobbstatus]
        C[API: /tts/audio/{job_id}] -.->|Hämtar ljud| F[Audiofil]
    end
    subgraph TTS Worker(s)
        Q --> W[Worker: process_tts_job]
        W -->|Sätter status, sparar fil| S
        W --> F
    end
```

- **API**: Tar emot TTS-förfrågningar och placerar dem i kön.
- **TTS Worker(s)**: Plockar upp jobb, genererar ljud (Google eller Coqui), uppdaterar status och sparar ljudfil.
- **Klient**: Pollar status och hämtar ljudfil när jobbet är klart.

### TTS API-användning

1. **Skapa ett TTS-jobb**
   ```http
   POST /tts/jobs
   Content-Type: application/json
   {
     "text": "Meddelande att läsa upp",
     "voice": "google", // eller "coqui"
     "output_format": "mp3" // eller "wav"
   }
   ```
   Svar:
   ```json
   { "job_id": "...", "status": "queued" }
   ```

2. **Hämta jobbstatus**
   ```http
   GET /tts/jobs/{job_id}
   ```
   Svar:
   ```json
   { "job_id": "...", "status": "queued|processing|done|failed" }
   ```

3. **Hämta ljudfil**
   ```http
   GET /tts/audio/{job_id}
   ```
   Svar: MP3/WAV-fil (HTTP 200) eller 404 om ej klar

### Skala TTS parallellt
- Starta flera instanser av TTS-workern för att parallellisera ljudgenerering.
- API och worker är helt separata processer och kan köras på olika servrar.

---

## License

[MIT License](LICENSE)

## Acknowledgments

- Thanks to Twilio for their excellent communication APIs