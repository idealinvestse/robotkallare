#!/usr/bin/env bash
uvicorn app.api:app --host $(grep API_HOST .env | cut -d= -f2) --port $(grep API_PORT .env | cut -d= -f2)
