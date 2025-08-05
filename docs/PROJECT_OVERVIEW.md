# GDial - Projektöversikt

## 🎯 **Senaste Uppdateringar (2025-08-05)**

✅ **Backend-testinfrastrukturen är nu produktionsklar!**
- **48 tester passerar framgångsrikt** (tidigare 0 fungerande tester)
- **Robust databashantering** - SQLite in-memory med automatiska fixtures
- **Omfattande mock-system** - Twilio, OpenAI TTS, och externa tjänster
- **24% testtäckning** etablerad som baslinje (mål: 60%+)
- **CI/CD-förberedd** testinfrastruktur för kontinuerlig integration

## Systemöversikt

GDial är en omfattande plattform för nödkommunikation och massutskick som möjliggör snabb kontakt med individer och grupper via röstsamtal och SMS-meddelanden. Systemet är byggt med en skalbar, asynkron arkitektur som gör det lämpligt för scenarier med hög genomströmning.

## Arkitektur

### Backend (Python/FastAPI)
- **Huvudapplikation**: FastAPI-baserad REST API server
- **Databas**: SQLite med SQLModel ORM
- **Asynkron bearbetning**: RabbitMQ för köhantering
- **Realtid**: WebSocket-stöd för live-uppdateringar
- **Externa tjänster**: Twilio för SMS/samtal, Google Cloud TTS

### Frontend (React/TypeScript)
- **Ramverk**: React 18 med TypeScript
- **State Management**: Zustand + TanStack React Query
- **Styling**: Tailwind CSS
- **Routing**: React Router v7
- **Ikoner**: Lucide React + Remix Icons

### Infrastruktur
- **Containerisering**: Docker med multi-stage builds
- **Utveckling**: Vite för frontend, uvicorn för backend
- **Testing**: pytest (backend), Vitest (frontend)
- **Dokumentation**: MkDocs

## Katalogstruktur

```
gdial/
├── app/                    # Backend-applikation
│   ├── api/               # API-endpoints
│   ├── models/            # Datamodeller
│   ├── repositories/      # Dataåtkomstlager
│   ├── services/          # Affärslogik
│   ├── schemas/           # Pydantic-scheman
│   ├── workers/           # Background workers
│   ├── realtime/          # WebSocket-hantering
│   ├── tts/               # Text-till-tal
│   └── utils/             # Hjälpfunktioner
├── frontend_new/          # Modern React-frontend
│   ├── src/
│   │   ├── components/    # React-komponenter
│   │   ├── pages/         # Sidor/vyer
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API-tjänster
│   │   └── types/         # TypeScript-typer
├── tests/                 # Backend-testinfrastruktur
│   ├── fixtures/          # Test fixtures och mocks
│   │   ├── database_test_fixtures.py  # Databashantering för tester
│   │   ├── twilio_mocks.py           # Twilio API mocks
│   │   └── tts_mocks.py              # TTS/OpenAI mocks
│   ├── test_*.py          # Enhetstester (48 passerar)
│   └── conftest.py        # Pytest konfiguration
├── docs/                  # Dokumentation
├── scripts/               # Deployment/utility scripts
└── static/                # Statiska filer
```

## Kärnfunktionalitet

### 1. Kontakt- och Grupphantering
- CRUD-operationer för kontakter och grupper
- Telefonnummervalidering och formatering
- Gruppmedlemskap och hierarkier

### 2. Meddelandehantering
- **Fördefinierade meddelanden**: Mallar för snabb utskick
- **Anpassade meddelanden**: Dynamisk innehållsgenerering
- **Burn Messages**: Självförstörande meddelanden
- **Schemaläggning**: Framtida utskick

### 3. Kommunikationskanaler
- **SMS**: Via Twilio SMS API
- **Röstsamtal**: Automatiserade samtal med TTS
- **Interaktiva samtal**: AI-assisterade konversationer
- **DTMF-hantering**: Knapptryckningsrespons

### 4. Realtidsövervakning
- Live-status för pågående kampanjer
- Samtals- och SMS-loggar
- Systemhälsa och prestanda
- WebSocket-baserade uppdateringar

### 5. Säkerhet och Autentisering
- API-nyckelbaserad autentisering
- Twilio webhook-validering
- Miljöbaserad konfiguration
- Säker hantering av känslig data

## Teknisk Stack

### Backend Dependencies (Huvudsakliga)
- **FastAPI**: Web framework
- **SQLModel**: ORM och datavalidering
- **Pydantic**: Data serialisering
- **APScheduler**: Schemaläggning
- **Twilio**: Kommunikations-API
- **RabbitMQ**: Meddelandekö
- **Google Cloud TTS**: Text-till-tal
- **pytest**: Testing framework

### Frontend Dependencies (Huvudsakliga)
- **React**: UI-ramverk
- **TypeScript**: Typsäkerhet
- **Vite**: Build-verktyg
- **Tailwind CSS**: Styling
- **Zustand**: State management
- **TanStack React Query**: Server state
- **Axios**: HTTP-klient
- **Vitest**: Testing framework

## Utvecklingsmiljö

### Lokala Krav
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- RabbitMQ (kan köras via Docker)

### Utvecklingsverktyg
- **Backend**: uvicorn, pytest, black, isort
- **Frontend**: ESLint, Prettier, TypeScript compiler
- **Databas**: SQLite för utveckling
- **API-dokumentation**: Automatisk OpenAPI-generering

## Deployment

### Docker-baserad Deployment
- Multi-stage builds för optimerade images
- Separata containers för backend, frontend och workers
- Docker Compose för lokal utveckling
- Produktionsklara konfigurationer

### Miljöhantering
- Miljövariabler för konfiguration
- Separata inställningar för dev/test/prod
- Säker hantering av API-nycklar och hemligheter

## 🧪 Testinfrastruktur (Produktionsklar)

### Backend Testing - **48 Tester Passerar** ✅

#### **Omfattande Testinfrastruktur**
- **Robust databashantering**: SQLite in-memory med automatiska fixtures
- **TestDatabaseManager**: Säkerställer konsistent databasanvändning mellan tester
- **Automatisk tabellskapande**: Alla SQLModel-tabeller skapas automatiskt för varje test
- **Clean session management**: Automatisk städning efter varje test

#### **Mock-system för Externa Tjänster**
- **Twilio API Mocks** (`tests/fixtures/twilio_mocks.py`):
  - MockTwilioClient, MockTwilioCall, MockTwilioMessage
  - Simulering av både framgångsrika och misslyckade API-anrop
  - Realistisk beteende för SMS och samtalshantering

- **TTS/OpenAI Mocks** (`tests/fixtures/tts_mocks.py`):
  - MockOpenAIClient med realistisk ljudgenerering
  - Felhantering för API-nyckelproblem
  - Temporära ljudkataloger för filtester

#### **Testkategorier**
- **API-tester**: FastAPI TestClient med dependency injection
- **Service-tester**: Affärslogik med mocks för externa beroenden
- **Repository-tester**: Dataåtkomst och CRUD-operationer
- **Integration-tester**: End-to-end flöden

#### **Testtäckning och Kvalitet**
- **Nuvarande täckning**: 24% (baslinje etablerad)
- **Målsättning**: 60%+ testtäckning
- **CI/CD-förberedd**: Infrastrukturen stöder kontinuerlig integration
- **Prestanda**: Snabba tester med in-memory databas

#### **Köra Tester**
```bash
# Alla tester med täckning
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Specifika testgrupper
python -m pytest tests/test_api.py -v
python -m pytest tests/test_services/ -v
python -m pytest tests/test_repositories/ -v

# Snabba tester utan täckning
python -m pytest tests/ -v --tb=short
```

### Frontend Testing
- **Komponenttester**: React Testing Library
- **Enhetstester**: Vitest för snabb exekvering
- **Mock-adapters**: API-anrop och externa tjänster
- **TypeScript-typkontroll**: Statisk analys
- **E2E-tester**: Playwright för användarflöden (planerat)

### Testmiljöer
- **Utveckling**: Lokala tester med `.env.test`
- **CI/CD**: Automatiserade tester vid varje commit
- **Staging**: Integrationstester mot staging-miljö
- **Produktion**: Smoke tests och hälsokontroller

## Övervakningsområden

### Prestanda
- API-responstider
- Databasfrågeprestanda
- Worker-genomströmning
- Minnesutnyttjande

### Tillförlitlighet
- Felhantering och återhämtning
- Kötillstånd och backlog
- Externa API-beroenden
- Systemuppetid

### Säkerhet
- API-autentisering och auktorisering
- Datavalidering och sanering
- Loggning av säkerhetshändelser
- Säker konfigurationshantering

## Framtida Utvecklingsområden

### Skalbarhet
- Horisontell skalning av workers
- Databas-optimering och sharding
- Caching-strategier
- Load balancing

### Funktionalitet
- Avancerad kampanjanalys
- A/B-testning av meddelanden
- Integrationer med fler kommunikationskanaler
- Förbättrad AI-konversation

### Användarupplevelse
- Mobil-responsiv design
- Offline-funktionalitet
- Förbättrad realtidsvisualisering
- Användarpersonalisering
