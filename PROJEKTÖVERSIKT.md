# GDial - Projektöversikt och Systembeskrivning

## 📋 Innehållsförteckning

1. [Projektöversikt](#projektöversikt)
2. [Systemarkitektur](#systemarkitektur)
3. [Kärnfunktioner](#kärnfunktioner)
4. [Teknisk Stack](#teknisk-stack)
5. [Databasstruktur](#databasstruktur)
6. [API-struktur](#api-struktur)
7. [Möjliga Förändringar](#möjliga-förändringar)

## 🎯 Projektöversikt

**GDial** är en omfattande meddelandeplattform som möjliggör automatiserad kommunikation via SMS och röstsamtal till kontakter och grupper. Systemet är byggt för att hantera stora volymer av meddelanden med hög tillförlitlighet och skalbarhet.

### Huvudsyfte
- **Massutskick**: Skicka SMS och röstmeddelanden till stora grupper
- **Kontakthantering**: Organisera kontakter i grupper för riktad kommunikation
- **Kampanjhantering**: Skapa och följa upp utskickskampanjer
- **Realtidsövervakning**: Spåra leveransstatus och svar

### Målgrupper
- **Företag**: För kundkommunikation och marknadsföring
- **Organisationer**: För medlemskommunikation
- **Myndigheter**: För medborgarinformation

## 🏗️ Systemarkitektur

### Backend (FastAPI)
```
app/
├── api/              # REST API endpoints
├── services/         # Affärslogik
├── repositories/     # Dataåtkomst
├── models/          # Datamodeller
├── schemas/         # API scheman
├── workers/         # Bakgrundsprocesser
├── config/          # Konfiguration
└── utils/           # Hjälpfunktioner
```

### Frontend (React/TypeScript)
```
frontend_new/
├── src/
│   ├── components/  # Återanvändbara komponenter
│   ├── pages/       # Sidor/vyer
│   ├── services/    # API-tjänster
│   └── types/       # TypeScript definitioner
```

### Infrastruktur
- **Databas**: SQLite (utveckling) / PostgreSQL (produktion)
- **Meddelandekö**: RabbitMQ för asynkron bearbetning
- **TTS**: OpenAI för text-till-tal
- **SMS/Röst**: Twilio för kommunikation

## ⚙️ Kärnfunktioner

### 1. Kontakthantering
**Beskrivning**: Hantera kontakter och organisera dem i grupper.

**Funktioner**:
- Skapa, redigera och ta bort kontakter
- Hantera flera telefonnummer per kontakt
- Grupporganisation med hierarkisk struktur
- Import/export av kontaktdata

**Fördelar**:
- Centraliserad kontaktdatabas
- Flexibel gruppindelning
- Enkel masshantering

**Nackdelar**:
- Kräver manuell datainmatning
- Risk för dubbletter

### 2. Meddelandehantering
**Beskrivning**: Skapa och hantera meddelanden för utskick.

**Funktioner**:
- Textmeddelanden (SMS)
- Röstmeddelanden (TTS eller inspelningar)
- Mallsystem för återanvändning
- Schemaläggning av meddelanden

**Fördelar**:
- Flexibel meddelandetyper
- Återanvändning genom mallar
- Automatisk schemaläggning

**Nackdelar**:
- TTS-kvalitet kan variera
- Begränsad personalisering

### 3. Kampanjhantering
**Beskrivning**: Organisera och genomföra utskickskampanjer.

**Funktioner**:
- Skapa kampanjer för grupper eller specifika kontakter
- Kombinera SMS och röstmeddelanden
- Spåra kampanjstatus och resultat
- Återförsöksmekanism för misslyckade meddelanden

**Fördelar**:
- Strukturerad kampanjhantering
- Detaljerad uppföljning
- Automatiska återförsök

**Nackdelar**:
- Komplex konfiguration
- Risk för spam-klassificering

### 4. Realtidsövervakning
**Beskrivning**: Övervaka systemstatus och meddelandeflöden.

**Funktioner**:
- Leveransstatus för meddelanden
- Systemhälsokontroller
- Felrapportering och loggning
- Prestandamätningar

**Fördelar**:
- Transparent systemstatus
- Snabb problemidentifiering
- Detaljerad loggning

**Nackdelar**:
- Kan generera mycket data
- Kräver aktiv övervakning

## 🛠️ Teknisk Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLModel**: ORM med Pydantic integration
- **RabbitMQ**: Meddelandekö för asynkron bearbetning
- **Twilio**: SMS och röstsamtal
- **OpenAI**: Text-till-tal tjänster

### Frontend
- **React 18**: Användarinterface
- **TypeScript**: Typsäker JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: State management

### Databas
- **SQLite**: Utveckling och testning
- **PostgreSQL**: Produktion (rekommenderat)

### DevOps
- **Docker**: Containerisering
- **Docker Compose**: Lokal utvecklingsmiljö
- **pytest**: Testning
- **GitHub Actions**: CI/CD (potentiellt)

## 🗄️ Databasstruktur

### Huvudtabeller

#### Contact
```sql
- id: UUID (PK)
- name: VARCHAR
- email: VARCHAR (optional)
- notes: TEXT (optional)
- created_at: TIMESTAMP
```

#### PhoneNumber
```sql
- id: UUID (PK)
- contact_id: UUID (FK)
- number: VARCHAR
- priority: INTEGER
```

#### ContactGroup
```sql
- id: UUID (PK)
- name: VARCHAR
- description: TEXT (optional)
```

#### Message
```sql
- id: UUID (PK)
- name: VARCHAR
- content: TEXT
- is_template: BOOLEAN
- message_type: VARCHAR (voice/sms)
- active: BOOLEAN
```

#### OutreachCampaign
```sql
- id: UUID (PK)
- name: VARCHAR
- description: TEXT
- message_id: UUID (FK)
- target_group_id: UUID (FK)
- status: VARCHAR
- created_at: TIMESTAMP
- completed_at: TIMESTAMP
```

#### SmsLog / CallLog
```sql
- id: UUID (PK)
- contact_id: UUID (FK)
- phone_number_id: UUID (FK)
- message_sid: VARCHAR
- status: VARCHAR
- sent_at: TIMESTAMP
- error_message: TEXT (optional)
```

### Relationer
- **En-till-många**: Contact → PhoneNumber
- **Många-till-många**: Contact ↔ ContactGroup
- **Många-till-många**: OutreachCampaign ↔ Contact

## 🔌 API-struktur

### Huvudendpoints

#### Kontakter
```
GET    /contacts              # Lista kontakter
POST   /contacts              # Skapa kontakt
GET    /contacts/{id}         # Hämta specifik kontakt
PUT    /contacts/{id}         # Uppdatera kontakt
DELETE /contacts/{id}         # Ta bort kontakt
```

#### Grupper
```
GET    /groups                # Lista grupper
POST   /groups                # Skapa grupp
GET    /groups/{id}           # Hämta specifik grupp
PUT    /groups/{id}           # Uppdatera grupp
DELETE /groups/{id}           # Ta bort grupp
```

#### Meddelanden
```
GET    /messages              # Lista meddelanden
POST   /messages              # Skapa meddelande
GET    /messages/{id}         # Hämta specifikt meddelande
PUT    /messages/{id}         # Uppdatera meddelande
DELETE /messages/{id}         # Ta bort meddelande
```

#### Kampanjer
```
POST   /api/v1/outreach       # Starta kampanj
GET    /campaigns             # Lista kampanjer
GET    /campaigns/{id}        # Hämta kampanjstatus
```

#### Webhooks
```
POST   /api/v1/webhooks/sms   # Twilio SMS status
POST   /api/v1/webhooks/call  # Twilio samtalsresultat
```

## 🔄 Möjliga Förändringar

### 1. Databasmigrering till PostgreSQL

**Beskrivning**: Migrera från SQLite till PostgreSQL för bättre prestanda och skalbarhet.

**Fördelar**:
- Bättre prestanda för stora dataset
- Avancerade datatyper och funktioner
- Bättre samtidighetsstöd
- Produktionsredo

**Nackdelar**:
- Ökad komplexitet i deployment
- Kräver databasserver
- Migreringsarbete krävs
- Högre infrastrukturkostnader

**Implementation**:
- Uppdatera connection strings
- Migrera befintlig data
- Testa alla funktioner
- Uppdatera deployment scripts

### 2. Microservices-arkitektur

**Beskrivning**: Dela upp monolitisk backend i separata tjänster.

**Fördelar**:
- Bättre skalbarhet per tjänst
- Oberoende deployment
- Teknologisk flexibilitet
- Förbättrad felhantering

**Nackdelar**:
- Ökad systemkomplexitet
- Nätverkskommunikation overhead
- Svårare debugging
- Kräver orchestration (Kubernetes)

**Potentiella tjänster**:
- Contact Service
- Message Service
- Campaign Service
- Notification Service

### 3. Caching-lager (Redis)

**Beskrivning**: Implementera Redis för caching av frekvent använd data.

**Fördelar**:
- Snabbare svarstider
- Minskad databasbelastning
- Bättre användarupplevelse
- Skalbarhet

**Nackdelar**:
- Ökad systemkomplexitet
- Konsistensutmaningar
- Extra infrastruktur
- Minneskostnader

**Användningsområden**:
- Kontaktlistor
- Meddelandemallar
- Kampanjstatus
- Användarautentisering

### 4. Real-time Dashboard

**Beskrivning**: Implementera WebSocket-baserad dashboard för realtidsövervakning.

**Fördelar**:
- Omedelbar statusuppdatering
- Bättre användarupplevelse
- Proaktiv problemhantering
- Visuell övervakning

**Nackdelar**:
- Ökad serverkomplexitet
- Mer resurskrävande
- WebSocket-hantering
- Potentiella anslutningsproblem

**Funktioner**:
- Live kampanjstatus
- Meddelandeflöden
- Systemhälsa
- Felnotifieringar

### 5. API Rate Limiting

**Beskrivning**: Implementera hastighetsbegränsning för API-endpoints.

**Fördelar**:
- Skydd mot överbelastning
- Förbättrad systemstabilitet
- Rättvis resursfördelning
- DDoS-skydd

**Nackdelar**:
- Kan begränsa legitima användare
- Kräver konfiguration
- Ökad komplexitet
- Övervakningsbehov

**Strategier**:
- Per-användare begränsningar
- Endpoint-specifika gränser
- Burst-hantering
- Graceful degradation

### 6. Avancerad Rapportering

**Beskrivning**: Utökad rapportering och analytics för kampanjer.

**Fördelar**:
- Bättre insikter i prestanda
- ROI-mätning
- Optimeringsmöjligheter
- Affärsintelligens

**Nackdelar**:
- Ökad datakomplexitet
- Lagringskrav
- Beräkningsoverhead
- Utvecklingstid

**Funktioner**:
- Leveransstatistik
- Svarsanalys
- Trendrapporter
- Export-funktioner

### 7. Multi-tenant Support

**Beskrivning**: Stöd för flera organisationer i samma system.

**Fördelar**:
- Skalbar affärsmodell
- Resurseffektivitet
- Centraliserad underhåll
- Kostnadsbesparingar

**Nackdelar**:
- Säkerhetsutmaningar
- Dataisolering krävs
- Ökad komplexitet
- Prestandapåverkan

**Implementering**:
- Tenant-ID i alla tabeller
- Row-level security
- Separata databaser per tenant
- API-nyckelhantering

## 📊 Rekommendationer

### Kortsiktiga förbättringar (1-3 månader)
1. **API Rate Limiting** - Kritiskt för systemstabilitet
2. **Redis Caching** - Förbättrar prestanda märkbart
3. **Förbättrad felhantering** - Ökar systemtillförlitlighet

### Medellånga förbättringar (3-6 månader)
1. **PostgreSQL-migrering** - Nödvändigt för skalning
2. **Real-time Dashboard** - Förbättrar användarupplevelse
3. **Avancerad rapportering** - Affärsnytta

### Långsiktiga förbättringar (6+ månader)
1. **Microservices-arkitektur** - För stor skalning
2. **Multi-tenant support** - Affärstillväxt
3. **AI/ML-integration** - Intelligent optimering

## 🔒 Säkerhetsaspekter

### Nuvarande säkerhet
- HTTPS-kommunikation
- API-nyckelautentisering
- Input-validering
- SQL-injection skydd

### Förbättringsområden
- JWT-baserad autentisering
- Role-based access control (RBAC)
- Audit logging
- Kryptering av känslig data
- Rate limiting per användare

## 📈 Skalbarhet

### Nuvarande begränsningar
- SQLite-prestanda vid stora dataset
- Monolitisk arkitektur
- Ingen horisontell skalning

### Skalningsstrategi
1. Vertikal skalning (mer CPU/RAM)
2. Databasoptimering och indexering
3. Caching-implementering
4. Horisontell skalning med load balancing
5. Microservices för oberoende skalning

---

*Denna projektöversikt uppdaterades: 2025-01-05*
*Version: 1.0*
