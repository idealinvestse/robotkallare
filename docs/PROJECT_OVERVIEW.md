# GDial - Projektöversikt

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
├── tests/                 # Backend-tester
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

## Testning

### Backend Testing
- Enhetstester med pytest
- Integrationstester för API-endpoints
- Mock-objekt för externa tjänster
- Databastester med separata testdatabaser

### Frontend Testing
- Komponenttester med React Testing Library
- Unit tests med Vitest
- Mock-adapters för API-anrop
- TypeScript-typkontroll

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
