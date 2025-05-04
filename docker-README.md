# GDial Docker Deployment

Detta är den officiella Docker-lösningen för att köra GDial-systemet. Lösningen erbjuder en enkel och konsekvent installation oavsett miljö (utveckling, test eller produktion).

## Snabbstart

Enklaste sättet att komma igång är att använda det automatiska startskriptet:

```bash
# Ge skriptet körrättigheter
chmod +x launch-gdial.sh

# Kör startskriptet
./launch-gdial.sh
```

Skriptet kommer att guida dig genom konfigurationen och starta systemet.

## Manuell konfiguration

Om du föredrar att konfigurera systemet manuellt:

1. Skapa en config-mapp och kopiera din .env-fil dit:
   ```bash
   mkdir -p config
   cp .env config/.env
   ```

2. Starta systemet med Docker Compose:
   ```bash
   docker compose up -d
   ```

## Tillgängliga komponenter

GDial består av flera komponenter som kan köras separat eller tillsammans:

- **postgres**: PostgreSQL-databas för lagring av data
- **api**: Huvudapplikationen som hanterar API-anrop och webhooks
- **outbox-worker**: Hanterar asynkrona uppgifter och utskickskö
- **cli**: CLI-verktyg för testning av samtalsfunktionalitet
- **frontend**: Frontend-applikation (om den ska köras separat)

## Användning av CLI-verktyget

CLI-verktyget för samtalstest kan köras med:

```bash
docker compose run --rm cli
```

För att ringa ett testsamtal:

```bash
docker compose run --rm cli call --mode tts --phone +46XXXXXXXXX --message "Testmeddelande"
```

För att testa AI-samtal:

```bash
docker compose run --rm cli call --mode realtime_ai --phone +46XXXXXXXXX
```

## Hantera systemet

### Se loggar

```bash
docker compose logs -f
```

### Stoppa systemet

```bash
docker compose down
```

### Starta om enskild tjänst

```bash
docker compose restart api
```

## Konfigurationsvariabler

De viktigaste konfigurationsvariablerna som kan ställas in i .env-filen:

| Variabel | Beskrivning | Standardvärde |
|----------|-------------|---------------|
| DB_USER | Databasanvändare | gdial |
| DB_PASSWORD | Databaslösenord | gdialpassword |
| DB_NAME | Databasnamn | gdial |
| DB_PORT | Databasport | 5432 |
| API_PORT | API-port | 3003 |
| PUBLIC_URL | Publik URL för API | http://localhost:3003 |
| TWILIO_ACCOUNT_SID | Twilio Account SID | - |
| TWILIO_AUTH_TOKEN | Twilio Auth Token | - |
| TWILIO_FROM_NUMBER | Twilio telefonnummer | - |
| OPENAI_API_KEY | OpenAI API-nyckel | - |
| OPENAI_TTS_MODEL | OpenAI TTS-modell | gpt-4o-mini-tts |

## Mer information

Se huvuddokumentationen för GDial för ytterligare information om tillgängliga funktioner och användning.

## Felsökning

### Problem med databasanslutning

Om API-tjänsten inte kan ansluta till databasen, kontrollera att PostgreSQL-containern är igång:

```bash
docker compose ps postgres
```

Kontrollera också att databasuppgifterna i .env-filen är korrekta.

### Problem med API-anslutning

Om CLI-verktyget inte kan ansluta till API:t, kontrollera att API-tjänsten är igång:

```bash
docker compose ps api
```

Kontrollera också att PUBLIC_URL i .env-filen är korrekt.
