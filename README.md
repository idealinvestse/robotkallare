# GDial - Emergency Notification & Messaging Platform

![GDial Logo](static/gdial-logo.png)

GDial är en omfattande plattform för nödkommunikation och massutskick som möjliggör snabb kontakt med individer och grupper via röstsamtal och SMS-meddelanden. Systemet är byggt med en modern, skalbar arkitektur som hanterar scenarier med hög genomströmning.

## 🚀 Snabbstart

### Förutsättningar
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Twilio-konto för SMS/samtal

### Installation

```bash
# Klona projektet
git clone https://github.com/yourusername/gdial.git
cd gdial

# Starta med Docker Compose
docker-compose up -d

# Eller kör lokalt
./launch-gdial-backend.sh
```

Öppna [http://localhost:3003](http://localhost:3003) för att komma åt webbgränssnittet.

## ✨ Huvudfunktioner

- **📱 Multi-kanal kommunikation**: SMS och röstsamtal via Twilio
- **👥 Kontakt- och grupphantering**: Organisera kontakter i grupper för riktade utskick
- **🎤 Avancerad TTS**: Text-till-tal med Google Cloud TTS och svenska röster
- **🤖 AI-assisterade samtal**: Interaktiva konversationer med AI
- **📊 Realtidsövervakning**: Live-dashboard för kampanjstatus
- **🔥 Burn Messages**: Självförstörande meddelanden
- **⏰ Schemaläggning**: Framtida utskick och återförsök

## 🏗️ Arkitektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web    │    │   FastAPI       │    │   RabbitMQ      │
│   Dashboard     │◄──►│   Backend       │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐         ┌─────────────┐
                       │   SQLite    │         │   Twilio    │
                       │  Database   │         │    API      │
                       └─────────────┘         └─────────────┘
```

### Teknisk Stack

**Backend:**
- FastAPI (Python 3.11)
- SQLModel + SQLite
- RabbitMQ för asynkron bearbetning
- Twilio för kommunikation
- Google Cloud TTS

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- Zustand + TanStack React Query
- Vite build system

## 📁 Projektstruktur

```
gdial/
├── app/                    # Backend (FastAPI)
│   ├── api/               # API endpoints
│   ├── services/          # Affärslogik
│   ├── repositories/      # Dataåtkomst
│   ├── workers/           # Background workers
│   └── models/            # Datamodeller
├── frontend_new/          # Frontend (React)
│   ├── src/components/    # React komponenter
│   ├── src/pages/         # Applikationssidor
│   └── src/hooks/         # Custom hooks
├── docs/                  # Dokumentation
├── tests/                 # Tester
└── docker-compose.yml     # Container orchestration
```

## 🚀 API Användning

### Skicka SMS till grupp
```bash
curl -X POST http://localhost:3003/api/trigger-sms \
-H "Content-Type: application/json" \
-d '{
  "message_content": "Viktigt meddelande!",
  "group_ids": ["group-uuid"],
  "scheduled_time": null
}'
```

### Starta röstsamtalskampanj
```bash
curl -X POST http://localhost:3003/api/outreach \
-H "Content-Type: application/json" \
-d '{
  "campaign_name": "Nödsamtal",
  "message_id": "message-uuid",
  "group_id": "group-uuid",
  "call_mode": "tts"
}'
```

## 🧪 Utveckling

### Lokala utvecklingsmiljö
```bash
# Backend
cd app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 3003

# Frontend
cd frontend_new
npm install
npm run dev
```

### Testning
```bash
# Backend tester
pytest

# Frontend tester
cd frontend_new
npm test
```

## 📖 Dokumentation

- **[Projektöversikt](docs/PROJECT_OVERVIEW.md)** - Detaljerad systemöversikt
- **[Kodningsriktlinjer](docs/code-guidelines.md)** - Utvecklingsstandards
- **[API-dokumentation](docs/api/)** - REST API referens
- **[Docker Setup](docs/docker-README.md)** - Container deployment
- **[Utvecklingsguide](docs/GDial_Development_Info.md)** - Utvecklarinformation

## 🔧 Konfiguration

Skapa en `.env`-fil baserad på `.env.example`:

```env
# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Database
DATABASE_URL=sqlite:///./gdial.db

# API
API_PORT=3003
LOG_LEVEL=INFO

# TTS
GOOGLE_CLOUD_TTS_KEY_PATH=path/to/credentials.json
```

## 🐳 Docker Deployment

```bash
# Bygg och starta alla tjänster
docker-compose up -d

# Visa loggar
docker-compose logs -f

# Stoppa tjänster
docker-compose down
```

## 🤝 Bidra

1. Forka projektet
2. Skapa en feature branch (`git checkout -b feature/amazing-feature`)
3. Commita dina ändringar (`git commit -m 'Add amazing feature'`)
4. Pusha till branchen (`git push origin feature/amazing-feature`)
5. Öppna en Pull Request

Se [kodningsriktlinjerna](docs/code-guidelines.md) för utvecklingsstandards.

## 📝 Licens

Detta projekt är licensierat under MIT-licensen - se [LICENSE](LICENSE) filen för detaljer.

## 🆘 Support

- **Dokumentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/gdial/issues)
- **Diskussioner**: [GitHub Discussions](https://github.com/yourusername/gdial/discussions)

## 🏆 Erkännanden

- Twilio för kommunikations-API
- Google Cloud för TTS-tjänster
- FastAPI och React communities

---

**GDial** - Snabb, tillförlitlig nödkommunikation när det verkligen räknas. 🚨
