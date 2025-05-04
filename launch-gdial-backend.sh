#!/bin/bash
# GDial Backend Launch Script
# Detta skript gör det enkelt att konfigurera och starta GDial-backend med Docker Compose

set -e
clear

# Färgdefinitioner
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner och introduktion
echo -e "${BLUE}"
echo -e "╔═════════════════════════════════════════════════╗"
echo -e "║  GDial System Launcher - Powered by Docker      ║"
echo -e "╚═════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "Detta skript hjälper dig att konfigurera och starta GDial-systemet."
echo -e "Du kommer att guidas genom de viktigaste inställningarna."
echo -e ""

# Kontrollera om Docker och Docker Compose är installerade
echo -e "${YELLOW}Kontrollerar systemkrav...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker är inte installerat. Installera Docker först:${NC}"
    echo -e "https://docs.docker.com/engine/install/ubuntu/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose är inte installerat. Installera Docker Compose:${NC}"
    echo -e "https://docs.docker.com/compose/install/linux/"
    exit 1
fi

echo -e "${GREEN}Docker och Docker Compose är installerade!${NC}"
echo ""

# Skapa config-mapp om den inte finns
mkdir -p config

# Skapa eller uppdatera .env-filen
ENV_FILE="config/.env"
echo -e "${YELLOW}Konfigurerar systemet...${NC}"

read -p "Vill du använda tidigare konfiguration om den finns? (y/n): " use_existing
if [ "$use_existing" == "y" ] && [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}Använder befintlig konfiguration från $ENV_FILE${NC}"
else
    # Databasinställningar
    echo -e "${BLUE}=== Databasinställningar ===${NC}"
    read -p "Databasanvändare [gdial]: " DB_USER
    DB_USER=${DB_USER:-gdial}
    
    read -p "Databaslösenord [gdialpassword]: " DB_PASSWORD
    DB_PASSWORD=${DB_PASSWORD:-gdialpassword}
    
    read -p "Databasnamn [gdial]: " DB_NAME
    DB_NAME=${DB_NAME:-gdial}
    
    read -p "Databasport [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}
    
    # API-inställningar
    echo -e "${BLUE}=== API-inställningar ===${NC}"
    read -p "API Port [3003]: " API_PORT
    API_PORT=${API_PORT:-3003}
    
    read -p "Public URL [http://localhost:$API_PORT]: " PUBLIC_URL
    PUBLIC_URL=${PUBLIC_URL:-http://localhost:$API_PORT}
    
    # Twilio-inställningar
    echo -e "${BLUE}=== Twilio-inställningar ===${NC}"
    read -p "Twilio Account SID: " TWILIO_ACCOUNT_SID
    read -p "Twilio Auth Token: " TWILIO_AUTH_TOKEN
    read -p "Twilio Från-nummer (E.164 format, t.ex +46XXXXXXXXX): " TWILIO_FROM_NUMBER
    
    # OpenAI-inställningar
    echo -e "${BLUE}=== OpenAI-inställningar ===${NC}"
    read -p "OpenAI API-nyckel: " OPENAI_API_KEY
    read -p "OpenAI TTS-modell [gpt-4o-mini-tts]: " OPENAI_TTS_MODEL
    OPENAI_TTS_MODEL=${OPENAI_TTS_MODEL:-gpt-4o-mini-tts}
    
    # Skapa .env-fil
    cat > "$ENV_FILE" << EOF
# Databasinställningar
SQLITE_DB=sqlite:///./dialer.db
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_PORT=${DB_PORT}

# API-inställningar
API_PORT=${API_PORT}
PUBLIC_URL=${PUBLIC_URL}
BASE_URL=${PUBLIC_URL}

# Twilio-inställningar
TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
TWILIO_FROM_NUMBER=${TWILIO_FROM_NUMBER}

# OpenAI-inställningar
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_TTS_MODEL=${OPENAI_TTS_MODEL}
AUDIO_DIR=static/audio
VOICE=coral

# Säkerhetsinställningar
SECRET_KEY="$(openssl rand -hex 32)"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Systeminställningar
CALL_TIMEOUT_SEC=25
SECONDARY_BACKOFF_SEC=120
MAX_SECONDARY_ATTEMPTS=2
EOF

    # Kopiera .env-filen till projektets rot för lokal utveckling
    cp "$ENV_FILE" ./.env
    
    echo -e "${GREEN}Konfiguration sparad i $ENV_FILE och .env${NC}"
fi

# Fråga vilka komponenter som ska startas
echo -e "\n${BLUE}=== Vilka backend-komponenter vill du starta? ===${NC}"
echo "1) Endast Backend-API (minimalt system)"
echo "2) Backend-API + Databas (standard)"
echo "3) Komplett backend (API, Databas, Worker)"
echo "4) Utvecklingsläge (Backend + Frontend)"
read -p "Välj ett alternativ [2]: " components
components=${components:-2}

# Bygg Docker-images
echo -e "\n${YELLOW}Bygger Backend Docker-images...${NC}"
case $components in
    1)
        docker compose build backend-api
        startup_command="docker compose up -d backend-api"
        ;;
    2)
        docker compose build backend-api
        startup_command="docker compose up -d backend-db backend-api"
        ;;
    3)
        docker compose build backend-api backend-worker
        startup_command="docker compose up -d backend-db backend-api --profile backend-workers"
        ;;
    4)
        docker compose build
        startup_command="docker compose up -d backend-db backend-api --profile backend-workers --profile frontend"
        ;;
    *)
        echo -e "${RED}Ogiltigt val. Använder standardalternativet.${NC}"
        docker compose build backend-api
        startup_command="docker compose up -d backend-db backend-api"
        ;;
esac

# Fråga om Backend CLI-verktyget också ska byggas
read -p "Vill du också bygga Backend CLI-verktyget för testning? (y/n) [y]: " build_cli
build_cli=${build_cli:-y}

if [ "$build_cli" == "y" ]; then
    echo -e "${YELLOW}Bygger Backend CLI-verktyget...${NC}"
    docker compose build backend-cli
fi

# Starta backend-systemet
echo -e "\n${YELLOW}Startar GDial Backend...${NC}"
eval $startup_command

# Visa information om körstatus
echo -e "\n${GREEN}GDial Backend har startats!${NC}"
echo -e "Backend API-server körs på: ${PUBLIC_URL}"

if [ "$build_cli" == "y" ]; then
    echo -e "\n${BLUE}För att köra Backend CLI-verktyget:${NC}"
    echo -e "docker compose run --rm backend-cli"
    echo -e "eller för att ringa ett testsamtal:"
    echo -e "docker compose run --rm backend-cli call --mode tts --phone +XXXXXXXXXX --message \"Testmeddelande\""
fi

echo -e "\n${BLUE}För att stoppa backend-systemet:${NC}"
echo -e "docker compose down"

echo -e "\n${BLUE}För att visa backend-loggar:${NC}"
echo -e "docker compose logs -f"

echo -e "\n${GREEN}Lycka till med GDial Backend!${NC}"
