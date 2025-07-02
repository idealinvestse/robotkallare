# GDial - Emergency Auto-Dialer & Notification System

## Svensk sammanfattning

GDial är ett automatiserat nödsamtalssystem som låter organisationer snabbt nå flera kontakter i krissituationer. Systemet består av:
- En RESTful API-server byggd med FastAPI.
- En RabbitMQ-baserad kö för asynkron hantering av Text-till-tal (TTS) och aviseringar.
- Skalbara worker-processer för hög prestanda.
- Ett modernt webbaserat dashboard för realtidsövervakning och hantering.

---

## 1. Overview

GDial is a comprehensive emergency notification system designed to rapidly contact individuals and groups through voice calls and SMS messages. It is built with a scalable, asynchronous architecture, making it suitable for high-throughput scenarios.

The system is managed via a modern web dashboard and a powerful REST API.

### Key Features

- **Multi-channel Notifications**: Send alerts via voice calls and SMS.
- **Contact & Group Management**: Organize contacts into groups for targeted mass-notifications.
- **Advanced TTS**: Asynchronous Text-to-Speech generation using Google Cloud TTS and Coqui-TTS.
- **Realtime AI Calls**: Initiate interactive calls with a conversational AI assistant.
- **Campaign Management**: Track outreach campaigns and monitor their status in real-time.
- **Real-time Monitoring**: A web dashboard provides live updates on system status and call logs.
- **Secure & Scalable**: Built with modern tools like FastAPI, RabbitMQ, and Docker for security, performance, and scalability.
- **Burn Messages**: Create self-destructing messages that are deleted after being viewed once.

## 2. Technical Architecture

GDial uses a decoupled architecture to ensure scalability and resilience. The FastAPI application handles API requests, while a RabbitMQ message queue manages background tasks. Dedicated worker processes consume these tasks, handling CPU-intensive operations like TTS generation and sending notifications.

```mermaid
flowchart TD
    subgraph User Interaction
        A[Web Dashboard] <--> B[REST API]
        C[External System] <--> B
    end

    subgraph Backend System
        B -- Publishes Job --> Q(RabbitMQ Queue)
        
        subgraph Workers (Scalable)
            W1[Outreach Worker] -- Consumes --> Q
            W2[TTS Worker] -- Consumes --> Q
        end

        W1 -- Makes Calls/SMS --> T[Twilio API]
        W2 -- Generates Audio --> S[File Storage]
        B -- Serves Audio --> A
    end

    T -- Sends Webhooks --> B
```

## 3. Getting Started

The recommended way to run GDial is using Docker.

### Prerequisites

- Docker and Docker Compose
- Twilio Account with a phone number
- Git

### Docker Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd gdial
    ```

2.  **Create an environment file:**
    Copy the example `.env` file and fill in your credentials, especially for Twilio.
    ```bash
    cp .env.example .env
    # Edit .env with your details
    # NANO .env
    ```
    **Key variables:**
    - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID.
    - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token.
    - `TWILIO_FROM_NUMBER`: Your Twilio phone number.
    - `PUBLIC_URL`: The public-facing URL of your server (for Twilio webhooks). Use a tool like `ngrok` for local development.

3.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```

4.  **Access the application:**
    -   **Web Dashboard**: `http://localhost:8080` (or the `FRONTEND_PORT` you defined).
    -   **API Server**: `http://localhost:3003` (or the `API_PORT` you defined).
    -   **API Docs**: `http://localhost:3003/docs`.

## 4. Configuration

System behavior can be configured via environment variables in the `.env` file.

-   `API_PORT`: Port for the backend API server.
-   `FRONTEND_PORT`: Port for the web dashboard.
-   `LOG_LEVEL`: Logging level (e.g., `DEBUG`, `INFO`).
-   `CALL_TIMEOUT_SEC`: Timeout for voice calls.
-   `OPENAI_API_KEY`: Required for the "Realtime AI" call mode.

## 5. Usage

### Sending a Notification

The primary way to send a notification is through the `/outreach` API endpoint.

**Example Request:**
```bash
curl -X POST http://localhost:3003/outreach/ \
-H "Content-Type: application/json" \
-d '{
  "campaign_name": "Test Campaign",
  "message_id": "your-message-template-uuid",
  "group_id": "your-target-group-uuid",
  "call_mode": "tts"
}'
```

**Call Modes:**
-   `tts`: (Default) Synthesizes speech from the message content. Requires a `message_id`.
-   `realtime_ai`: Connects the call to a conversational AI. `message_id` is not required.

### Project Structure

-   `app/`: Main directory for the FastAPI backend source code.
    -   `api/`: Contains API endpoint routers.
    -   `services/`: Houses the core business logic.
    -   `repositories/`: Handles database interactions.
    -   `workers/`: Logic for the RabbitMQ background workers.
    -   `models.py`: SQLModel database models.
    -   `schemas.py`: Pydantic data validation schemas.
    -   `main.py`: FastAPI application entrypoint.
-   `frontend_new/`: Source code for the React-based web dashboard.
-   `static/`: Legacy HTML/JS files.
-   `docker-compose.yml`: Defines the services for Docker.
-   `Dockerfile`: Instructions for building the backend Docker image.
-   `Dockerfile.frontend`: Instructions for building the frontend Docker image.
