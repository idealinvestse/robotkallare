# GDial - Emergency Notification & Messaging Platform

Denna dokumentation ger instruktioner för att sätta upp, köra och hantera GDial emergency notification system.

## 🎯 **Senaste Uppdateringar (2025-08-05)**

✅ **Backend-testinfrastrukturen är nu produktionsklar!**
- 48 tester passerar framgångsrikt
- Robust databashantering med automatiska fixtures
- Omfattande mock-system för externa tjänster
- 24% testtäckning etablerad som baslinje

## Innehållsförteckning

1. [Översikt](#översikt)
2. [Installation](#installation)
3. [Starta systemet](#starta-systemet)
4. [Konfiguration](#konfiguration)
5. [🧪 Testning](#testning)
6. [Användningsguide](#användningsguide)
7. [API-dokumentation](#api-dokumentation)
8. [Felsökning](#felsökning)
9. [Utveckling](#utveckling)

## Översikt

GDial är en omfattande plattform för nödkommunikation och massutskick som möjliggör snabb kontakt med individer och grupper via röstsamtal och SMS-meddelanden. Systemet är byggt med en modern, skalbar arkitektur som hanterar scenarier med hög genomströmning.

### Huvudfunktioner
- **Multi-kanal kommunikation**: SMS och röstsamtal via Twilio
- **Kontakt- och grupphantering**: Organisera kontakter i grupper för riktade utskick
- **Avancerad TTS**: Text-till-tal med Google Cloud TTS och svenska röster
- **AI-assisterade samtal**: Interaktiva konversationer med AI
- **Realtidsövervakning**: Live-dashboard för kampanjstatus och samtalsloggar
- **Burn Messages**: Självförstörande meddelanden som raderas efter visning
- **Schemaläggning**: Framtida utskick och automatiska återförsök
- **RabbitMQ Integration**: Asynkron bearbetning för hög prestanda
- **Modern webbgränssnitt**: React-baserat dashboard med realtidsuppdateringar

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

## 🧪 Testning

### Backend Testing - **48 Tester Passerar** ✅

GDial har nu en robust och produktionsklar testinfrastruktur som säkerställer kod kvalitet och tillförlitlighet.

#### **Snabbstart - Köra Tester**

```bash
# Aktivera virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installera test-dependencies (om inte redan gjort)
pip install pytest pytest-asyncio pytest-cov

# Kör alla tester med täckning
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Snabba tester utan täckning
python -m pytest tests/ -v --tb=short

# Specifika testgrupper
python -m pytest tests/test_api.py -v
python -m pytest tests/test_services/ -v
python -m pytest tests/test_repositories/ -v
```

#### **Testinfrastruktur**

**🗄️ Databashantering**
- **SQLite in-memory**: Snabba, isolerade tester
- **TestDatabaseManager**: Säkerställer konsistent databasanvändning
- **Automatisk tabellskapande**: Alla SQLModel-tabeller skapas för varje test
- **Clean session management**: Automatisk städning efter varje test

**🎭 Mock-system för Externa Tjänster**

*Twilio API Mocks* (`tests/fixtures/twilio_mocks.py`):
- `MockTwilioClient`: Simulerar Twilio API-anrop
- `MockTwilioCall`: Realistisk samtalshantering
- `MockTwilioMessage`: SMS-funktionalitet med fel-simulering
- Stöder både framgångsrika och misslyckade scenarier

*TTS/OpenAI Mocks* (`tests/fixtures/tts_mocks.py`):
- `MockOpenAIClient`: Simulerar ljudgenerering
- Felhantering för API-nyckelproblem
- Temporära ljudkataloger för filtester

#### **Testkategorier**

**API-tester** (`tests/test_api.py`):
- FastAPI TestClient med dependency injection
- Endpoint-validering och felhantering
- Autentisering och auktorisering

**Service-tester** (`tests/test_*_service.py`):
- Affärslogik med mocks för externa beroenden
- SMS och samtalshantering
- TTS-integration

**Repository-tester** (`tests/test_*_repository.py`):
- Dataåtkomst och CRUD-operationer
- Relationer mellan entiteter
- Datavalidering

**Integration-tester**:
- End-to-end flöden
- API till databas-integration
- Externa tjänsteintegrationer

#### **Testtäckning och Kvalitet**

- **Nuvarande täckning**: 24% (baslinje etablerad)
- **Målsättning**: 60%+ testtäckning
- **CI/CD-förberedd**: Infrastrukturen stöder kontinuerlig integration
- **Prestanda**: Snabba tester med in-memory databas

#### **Testmiljöer**

**Utvecklingsmiljö**:
```bash
# Kopiera test-miljövariabler
cp .env.example .env.test

# Redigera .env.test med test-specifika värden
# DATABASE_URL=sqlite:///:memory:
# TWILIO_ACCOUNT_SID=test_sid
# TWILIO_AUTH_TOKEN=test_token
```

**CI/CD Pipeline**:
- Automatiserade tester vid varje commit
- Testtäckningsrapporter
- Kvalitetsgates för merge requests

#### **Felsökning av Tester**

**Vanliga Problem**:

1. **Import-fel**:
   ```bash
   # Säkerställ att PYTHONPATH är korrekt
   export PYTHONPATH=$PWD:$PYTHONPATH
   ```

2. **Databasfel**:
   ```bash
   # Kontrollera att alla modeller importeras
   python -c "from app.models import *; print('Models OK')"
   ```

3. **Mock-fel**:
   ```bash
   # Kör enskilda tester för debugging
   python -m pytest tests/test_sms_service.py::test_send_sms -v -s
   ```

**Debug-tips**:
- Använd `-v` för verbose output
- Använd `-s` för att se print-statements
- Använd `--tb=short` för kortare traceback
- Använd `--lf` för att köra endast senast misslyckade tester

#### **Bidra till Testerna**

**Lägga till nya tester**:
1. Skapa testfil i `tests/` katalogen
2. Använd befintliga fixtures från `tests/conftest.py`
3. Följ namnkonventionen `test_*.py`
4. Inkludera både positiva och negativa testfall

**Förbättra testtäckning**:
```bash
# Generera HTML-rapport för detaljerad täckning
python -m pytest tests/ --cov=app --cov-report=html

# Öppna htmlcov/index.html för att se vilka rader som saknar täckning
```

### Frontend Testing (Planerat)

- **Komponenttester**: React Testing Library
- **Enhetstester**: Vitest för snabb exekvering
- **E2E-tester**: Playwright för användarflöden
- **Mock-adapters**: API-anrop och externa tjänster

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

För ytterligare hjälp, kontakta systemadministratören.

## Utveckling

### Utvecklingsmiljö

#### Snabb uppstart med launch script
```bash
# Automatisk setup och start (rekommenderat för första gången)
./launch-gdial-backend.sh

# Scriptet kommer att:
# - Skapa virtuell miljö (gdial_venv)
# - Installera alla beroenden
# - Detektera GPU för CUDA-stöd
# - Ladda ner svenska TTS-modeller
# - Starta applikationen
```

**GPU-acceleration**: Om du har NVIDIA GPU kommer scriptet automatiskt installera CUDA-stöd för förbättrad TTS-prestanda.

#### Backend-utveckling
```bash
# Aktivera virtuell miljö
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installera utvecklingsberoenden
pip install -r requirements-dev.txt

# Starta med hot reload
uvicorn app.main:app --reload --port 3003
```

#### Frontend-utveckling
```bash
# Navigera till frontend-katalogen
cd frontend_new

# Installera beroenden
npm install

# Starta utvecklingsserver
npm run dev
```

### Docker-utveckling

#### Bygg och kör med Docker Compose
```bash
# Bygg alla tjänster
docker-compose build

# Starta alla tjänster
docker-compose up -d

# Visa loggar
docker-compose logs -f

# Stoppa tjänster
docker-compose down
```

#### Individuella Docker-kommandon
```bash
# Bygg backend
docker build -t gdial-backend .

# Bygg frontend
docker build -f Dockerfile.frontend -t gdial-frontend .

# Kör backend
docker run -p 3003:3003 gdial-backend
```

### Testing

#### Backend-tester
```bash
# Kör alla tester
pytest

# Kör med coverage
pytest --cov=app

# Kör specifika tester
pytest tests/test_outreach_service.py
```

#### Frontend-tester
```bash
cd frontend_new

# Kör enhetstester
npm test

# Kör med coverage
npm run test:coverage

# Kör i watch-läge
npm run test:watch
```

### Kodkvalitet

#### Backend linting och formatering
```bash
# Formatera kod med black
black app/

# Sortera imports
isort app/

# Kör linting
flake8 app/
```

#### Frontend linting
```bash
cd frontend_new

# Kör ESLint
npm run lint

# Fixa automatiska problem
npm run lint:fix
```

### Databashantering

#### Migrationer
```bash
# Kör databasmigrationer
python migrate_db.py

# Återställ databas
rm dialer.db
python app/seed_db.py
```

#### Backup och återställning
```bash
# Backup av databas
cp dialer.db dialer_backup_$(date +%Y%m%d).db

# Återställ från backup
cp dialer_backup_20250103.db dialer.db
```

### RabbitMQ-utveckling

#### Lokal RabbitMQ med Docker
```bash
# Starta RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Åtkomst till management UI
# http://localhost:15672 (guest/guest)
```

#### Worker-utveckling
```bash
# Starta outreach worker
python -m app.workers.outreach_worker

# Starta TTS worker
python -m app.workers.tts_worker
```

### API-utveckling

#### OpenAPI-dokumentation
```bash
# Generera OpenAPI-specifikation
python export_openapi.py

# Åtkomst till interaktiv dokumentation
# http://localhost:3003/docs (Swagger UI)
# http://localhost:3003/redoc (ReDoc)
```

#### API-testning
```bash
# Testa med curl
curl -X POST http://localhost:3003/api/trigger-sms \
  -H "Content-Type: application/json" \
  -d '{"message_content": "Test", "contact_ids": [1]}'

# Använd HTTPie för enklare testning
http POST localhost:3003/api/trigger-sms message_content="Test" contact_ids:='[1]'
```

### Prestanda och övervakning

#### Loggning
```bash
# Visa realtidsloggar
tail -f gdial.log

# Filtrera efter nivå
grep "ERROR" gdial.log

# Visa worker-loggar
tail -f logs/outreach_worker.log
```

#### Prestandaövervakning
```bash
# Övervaka systemresurser
top -p $(pgrep -f "uvicorn")

# Övervaka databasstorlek
ls -lh dialer.db

# Kontrollera RabbitMQ-köer
rabbitmqctl list_queues
```

### Deployment

#### Produktionsdistribution
```bash
# Bygg för produktion
docker-compose -f docker-compose.prod.yml build

# Deploy med minimal downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
```

#### Miljöhantering
```bash
# Kopiera miljövariabler
cp .env.example .env.prod

# Redigera produktionsinställningar
nano .env.prod
```

För ytterligare utvecklingsinformation, se:
- [Kodningsriktlinjer](code-guidelines.md)
- [Projektöversikt](PROJECT_OVERVIEW.md)
- [Utvecklingsguide](GDial_Development_Info.md)