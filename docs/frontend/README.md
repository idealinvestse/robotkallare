# GDial Frontend Dokumentation

*Modern React-applikation för GDial-plattformen*

## Översikt

GDial Frontend är en modern React-applikation byggd med TypeScript och Tailwind CSS som tillhandahåller ett intuitivt gränssnitt för att hantera SMS-meddelanden, kontakter och grupper.

## Snabbstart

### Förutsättningar
- Node.js 18+ 
- npm eller yarn
- GDial Backend körs på `http://localhost:3003`

### Installation

```bash
# Navigera till frontend-katalogen
cd frontend_new

# Installera beroenden
npm install

# Starta utvecklingsserver
npm run dev
```

Applikationen kommer att vara tillgänglig på `http://localhost:5173`

## Teknisk Stack

### Kärnteknologier
- **React 18** - Moderna hooks och concurrent features
- **TypeScript** - Typsäker utveckling
- **Vite** - Snabb build-verktyg med HMR
- **Tailwind CSS** - Utility-first CSS framework

### State Management & API
- **Zustand** - Lättviktig state management
- **TanStack Query** - Server state management och caching
- **Axios** - HTTP-klient för API-anrop

### UI & UX
- **Lucide React** - Moderna ikoner
- **React Hook Form** - Formulärhantering
- **React Router** - Client-side routing

## Projektstruktur

```bash
frontend_new/
├── src/
│   ├── components/     # Återanvändbara UI-komponenter
│   ├── pages/          # Sidor/vyer (max 200 rader)
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API-tjänster och externa anrop
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Hjälpfunktioner
│   └── stores/         # Zustand stores
├── public/             # Statiska filer
└── docs/               # Komponentdokumentation
```

## Huvudfunktioner

### SMS-hantering
- Skicka SMS till enskilda kontakter eller grupper
- Skapa och hantera meddelandemallar
- Schemalägg meddelanden för framtida leverans
- Visa sändningsstatus och historik

### Kontakt- och grupphantering
- Lägg till och redigera kontakter
- Skapa och hantera kontaktgrupper
- Importera kontakter från CSV
- Sök och filtrera kontakter

### Övervakning
- Realtidsövervakning av meddelandestatus
- Leveransrapporter och statistik
- Felhantering och återförsök

## Utveckling

### Kodningsriktlinjer
Följ projektets [kodningsriktlinjer](../code-guidelines.md) för:
- Komponentstruktur (max 200 rader per fil)
- TypeScript-typer och interfaces
- State management patterns
- API-integration

### Testning
```bash
# Kör enhetstester
npm run test

# Kör tester med coverage
npm run test:coverage

# Kör E2E-tester
npm run test:e2e
```

### Build & Deploy
```bash
# Bygg för produktion
npm run build

# Förhandsgranska produktionsbygge
npm run preview
```

## API-integration

Frontend kommunicerar med GDial Backend via REST API:
- **Base URL**: `http://localhost:3003/api`
- **Autentisering**: JWT tokens
- **Dokumentation**: [OpenAPI Spec](../openapi.json)

### Exempel API-anrop
```typescript
// Skicka SMS
const response = await smsService.sendSms({
  contact_ids: [1, 2, 3],
  message_template_id: 1,
  scheduled_time: '2025-01-04T10:00:00'
});
```

## UI/UX-riktlinjer

### Design System
- **Färgschema**: Tailwind CSS default palette
- **Typografi**: Inter font family
- **Spacing**: Tailwind spacing scale
- **Responsivitet**: Mobile-first approach

### Komponentbibliotek
Återanvändbara komponenter finns i `src/components/`:
- `Button` - Primära och sekundära knappar
- `Input` - Formulärfält med validering
- `Modal` - Modala dialoger
- `Table` - Datavisning med sortering

## Felsökning

### Vanliga problem
1. **API-anslutning**: Kontrollera att backend körs på port 3003
2. **CORS-fel**: Verifiera CORS-konfiguration i backend
3. **Build-fel**: Rensa node_modules och kör `npm install`

### Utvecklingsverktyg
- **React DevTools** - Komponentinspektion
- **Redux DevTools** - State debugging (för Zustand)
- **Network tab** - API-anrop debugging

---

**Senast uppdaterad:** 2025-01-04  
**Version:** 2.0  
**Kompatibilitet:** React 18+, Node.js 18+
