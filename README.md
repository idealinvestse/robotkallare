# GDial - Emergency Notification & Messaging Platform

![GDial Logo](static/gdial-logo.png)

GDial är en omfattande plattform för nödkommunikation och massutskick som möjliggör snabb kontakt med individer och grupper via röstsamtal och SMS-meddelanden. Systemet är byggt med en modern, skalbar arkitektur som hanterar scenarier med hög genomströmning.

## 🎯 **Senaste Uppdateringar (2025-08-05)**

✅ **Backend-testinfrastrukturen är nu produktionsklar!**
- 48 tester passerar framgångsrikt
- Omfattande databasfixturer implementerade
- Twilio- och TTS-mocks integrerade
- Robust testmiljö för kontinuerlig utveckling
- 24% testtäckning etablerad som baslinje

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

# Automatisk setup och start (rekommenderat)
./launch-gdial-backend.sh

# Eller med Docker Compose
docker-compose up -d
```

**Webbgränssnitt:** [http://localhost:3003](http://localhost:3003)

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
├── tests/                 # Testinfrastruktur
│   ├── fixtures/          # Test fixtures och mocks
│   ├── test_*.py          # Enhetstester
│   └── conftest.py        # Pytest konfiguration
├── docs/                  # Dokumentation
└── docker-compose.yml     # Container orchestration
```

## 🧪 Testning och Utveckling

### Köra Tester

```bash
# Kör alla tester med täckning
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Kör specifika tester
python -m pytest tests/test_api.py -v

# Kör tester med detaljerad output
python -m pytest tests/ -v --tb=short
```

### Testinfrastruktur

- **48 tester passerar** - Robust testmiljö etablerad
- **Databasfixturer** - Automatisk SQLite in-memory databas för tester
- **Mock-system** - Omfattande mocks för Twilio, OpenAI TTS och externa tjänster
- **Testtäckning** - 24% baslinje med mål att nå 60%+
- **CI/CD-redo** - Testinfrastrukturen är förberedd för kontinuerlig integration

### Utvecklingsmiljö

```bash
# Sätt upp utvecklingsmiljö
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Kör backend i utvecklingsläge
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Kör frontend
cd frontend_new
npm install
npm run dev
```

## 🚀 API Användning

**Interaktiv API-dokumentation:** [http://localhost:3003/docs](http://localhost:3003/docs)

**Snabbexempel:**
```bash
# SMS till grupp
curl -X POST http://localhost:3003/api/trigger-sms \
  -H "Content-Type: application/json" \
  -d '{"message_content": "Test", "group_ids": ["group-uuid"]}'

# Röstsamtal
curl -X POST http://localhost:3003/api/outreach \
  -H "Content-Type: application/json" \
  -d '{"campaign_name": "Test", "group_id": "group-uuid"}'
```

*För fullständiga API-exempel och parametrar, se [live-dokumentationen](http://localhost:3003/docs).*

## 🧪 Utveckling

**Snabb utvecklingsstart:**
```bash
# Automatisk setup med GPU-stöd
./launch-gdial-backend.sh

# Manuell backend-utveckling
source venv/bin/activate
uvicorn app.main:app --reload --port 3003

# Frontend-utveckling
cd frontend_new && npm install && npm run dev
```

**Testning:**
```bash
pytest                    # Backend-tester
cd frontend_new && npm test  # Frontend-tester
```

## 📖 Dokumentation

- **[📋 Dokumentationsindex](docs/index.md)** - Komplett dokumentationsöversikt
- **[🚀 Progressionsvy](docs/PROGRESSION_VIEW.md)** - Kollaborationsplan och projektöversikt
- **[🏗️ Projektöversikt](docs/PROJECT_OVERVIEW.md)** - Systemarkitektur och struktur
- **[⚙️ Installation & Konfiguration](docs/DOCUMENTATION.md)** - Detaljerad setup-guide
- **[👨‍💻 Kodningsriktlinjer](docs/code-guidelines.md)** - Utvecklingsstandards för AI-agenter
- **[🐳 Docker Deployment](docs/docker-README.md)** - Container-baserad deployment
- **[🔌 API-dokumentation](http://localhost:3003/docs)** - Interaktiv OpenAPI-dokumentation

## 🔧 Konfiguration

Skapa `.env` från mall:
```bash
cp .env.example .env
# Redigera .env med dina Twilio-uppgifter
```

**Viktiga inställningar:**
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN` - Twilio API-uppgifter
- `TWILIO_PHONE_NUMBER` - Ditt Twilio-telefonnummer
- `DATABASE_URL` - Databasanslutning (standard: SQLite)
- `API_PORT` - Server-port (standard: 3003)

*Se [.env.example](.env.example) för alla tillgängliga inställningar.*

## 🐳 Docker Deployment

```bash
docker-compose up -d     # Starta alla tjänster
docker-compose logs -f   # Visa loggar
docker-compose down      # Stoppa tjänster
```

*För detaljerad Docker-dokumentation, se [docs/docker-README.md](docs/docker-README.md)*

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
