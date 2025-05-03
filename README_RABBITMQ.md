# RabbitMQ Message Queue System for GDial

This document provides instructions for setting up and using the RabbitMQ message queue system that has been integrated into GDial.

## Overview

GDial now uses RabbitMQ to handle call jobs, which provides several advantages:

- Improved scalability through distributed worker processes
- Better resilience with message persistence
- Ability to prioritize and schedule jobs
- Reduced load on the main application server
- Pre-generation of TTS audio for faster call handling

## Installation

### RabbitMQ Server

You'll need a RabbitMQ server. For production, we recommend using a managed service or Docker.

**Docker option:**
```bash
docker run -d --hostname rabbit --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

**Local installation (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
sudo systemctl start rabbitmq-server
```

### Python Dependencies

The required Python dependencies have been added to your environment:

- `pika`: Python client for RabbitMQ
- `prometheus_client`: For metrics (optional)
- `psutil`: For worker health monitoring

## Configuration

Set the following environment variables to configure the system:

```bash
# RabbitMQ connection
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"

# Worker settings
export CALL_WORKERS_COUNT=3
export TTS_WORKERS_COUNT=2
```

## Worker Processes

GDial includes the following worker processes:

1. **Call Workers**: Process call jobs by making Twilio API calls
2. **TTS Workers**: Pre-generate TTS audio files for calls

### Starting Workers

To start the workers:

```bash
./scripts/start_workers.sh
```

To stop them:

```bash
./scripts/stop_workers.sh
```

## Using the Queue System

The workers will automatically pick up jobs from the queue. The system includes several queue types:

- `gdial.call.single`: For individual call jobs
- `gdial.call.batch`: For batches of calls
- `gdial.tts`: For text-to-speech generation

You don't need to interact with these queues directly, as the application handles this for you.

## Monitoring

### Logs

Worker logs are stored in the `logs/` directory:
- `logs/call_worker.log`
- `logs/tts_worker.log`

### Metrics

The system collects metrics using Prometheus. To enable the metrics server:

```python
from app.monitoring.metrics import start_metrics_server, start_queue_monitor

# Start metrics server on port 8000
start_metrics_server(port=8000)

# Start queue monitoring (checks queue depths)
start_queue_monitor(
    rabbitmq_url="amqp://guest:guest@localhost:5672/",
    queue_names=["gdial.call.single", "gdial.call.batch", "gdial.tts"]
)
```

You can then view metrics at http://localhost:8000/metrics or connect a Prometheus server to scrape them.

## Troubleshooting

If you encounter issues:

1. Check that RabbitMQ is running:
   ```bash
   systemctl status rabbitmq-server
   # or for Docker:
   docker ps | grep rabbitmq
   ```

2. Verify connection settings:
   ```bash
   rabbitmqctl status
   ```

3. Check the worker logs:
   ```bash
   tail -f logs/call_worker.log
   ```

4. Restart the workers:
   ```bash
   ./scripts/stop_workers.sh
   ./scripts/start_workers.sh
   ```

## Coqui TTS/Piper Integration

The system now supports Coqui TTS/Piper as an alternative to Google TTS. To use it:

1. Install Piper:
   ```bash
   # Install piper and download the Swedish model
   pip install piper-tts
   ```

2. Set the environment variables:
   ```bash
   export TTS_ENGINE="coqui"
   export PIPER_BINARY="/path/to/piper"
   export PIPER_MODEL="/path/to/sv_SE-marin-medium.onnx"
   ```

3. Restart the TTS workers:
   ```bash
   ./scripts/stop_workers.sh
   ./scripts/start_workers.sh
   ```