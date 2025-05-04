# GDial CLI Call Tester - Docker Edition

Detta är en Docker-container för GDial's CLI-verktyg för samtalstest. Containern gör det enkelt att testa GDial's samtalsfunktionalitet på vilken server som helst, utan att behöva installera några beroenden.

## Snabbstart

### Bygg Docker-imagen

```bash
docker build -f Dockerfile.cli -t gdial-cli .
```

### Kör med simuleringsläge (kräver ingen konfiguration)

```bash
docker run -it --rm gdial-cli
```

### Kör med egen konfigurationsfil

Skapa en katalog för att dela .env filen:

```bash
mkdir -p ~/gdial-config
cp .env ~/gdial-config/
```

Kör containern med konfigurationen:

```bash
docker run -it --rm -v ~/gdial-config:/app/config gdial-cli
```

## Användningsexempel

### Interaktivt läge

```bash
docker run -it --rm -v ~/gdial-config:/app/config gdial-cli
```

### TTS-samtal

```bash
docker run -it --rm -v ~/gdial-config:/app/config gdial-cli call --mode tts --phone +46XXXXXXXXX --message "Detta är ett testmeddelande"
```

### Realtime AI-samtal

```bash
docker run -it --rm -v ~/gdial-config:/app/config gdial-cli call --mode realtime_ai --phone +46XXXXXXXXX
```

### Kolla samtalsstatus

```bash
docker run -it --rm -v ~/gdial-config:/app/config gdial-cli status CALL_SID --watch
```

## Konfiguration

Container:n letar efter en .env-fil i `/app/config/` katalogen. För att tillhandahålla din egen konfiguration, montera en volym som innehåller din .env-fil.

Exempel på .env-fil:

```
# Database settings
SQLITE_DB=sqlite:///./dialer.db

# Twilio settings
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# API settings
PUBLIC_URL=http://your-api-server.com
```

Om ingen .env-fil tillhandahålls kommer container:n att automatiskt köras i simuleringsläge.

## För utvecklare

### Miljövariabler

Du kan åsidosätta konfigurationen genom att skicka miljövariabler direkt:

```bash
docker run -it --rm -e GDIAL_CLI_SIMULATION=true gdial-cli
```

### Felsökning

För att inspektera containern:

```bash
docker run -it --rm --entrypoint /bin/bash gdial-cli
```
