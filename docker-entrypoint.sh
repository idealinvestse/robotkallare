#!/bin/bash
set -e

# Kontrollera om .env-filen finns i config-volymen och kopiera till arbetskatalogen
if [ -f /app/config/.env ]; then
    echo "Using .env file from mounted volume"
    cp /app/config/.env /app/.env
fi

# Ange simuleringsläge om ingen .env-fil finns
if [ ! -f /app/.env ]; then
    echo "No .env file found, setting GDIAL_CLI_SIMULATION=true"
    export GDIAL_CLI_SIMULATION=true
fi

# Kör CLI-verktyget med alla argument som skickas till containern
exec python /app/cli_call_tester.py "$@"
