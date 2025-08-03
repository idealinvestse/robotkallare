# 📋 Historisk implementationsplan: RabbitMQ Worker-arkitektur

> **⚠️ HISTORISK DOKUMENTATION**  
> Detta dokument bevaras för historisk referens. RabbitMQ-arkitekturen har redan implementerats i det aktuella systemet. Se [README_RABBITMQ.md](README_RABBITMQ.md) för aktuell konfiguration och användning.

## Översikt
Detta dokument beskriver den ursprungliga planen för att implementera en meddelandeköbaserad arkitektur med RabbitMQ för GDial-systemet. Målet var att förbättra skalbarhet, tillförlitlighet och prestanda genom att frikoppla samtalsbearbetning från huvudapplikationen.

## Current Architecture Analysis
The current system:
- Uses synchronous processing via `dial_contacts` in `dialer.py`
- Implements basic concurrency with Python's asyncio
- Has some parallelization with "bots" that handle multiple calls
- Uses direct Twilio API calls for each outgoing call
- TTS generation happens inline during call processing

## Implementation Plan

### 1. RabbitMQ Integration

#### 1.1 Setup RabbitMQ
- Add RabbitMQ to project dependencies
- Create connection module for RabbitMQ interactions

```python
# app/queue/rabbitmq.py
import pika
import json
import logging
import os
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger("rabbitmq")

@lru_cache()
def get_rabbitmq_connection():
    """Returns a cached connection to RabbitMQ"""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    try:
        params = pika.URLParameters(rabbitmq_url)
        return pika.BlockingConnection(params)
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        raise

def publish_message(queue_name: str, message: Dict[str, Any], persistent: bool = True) -> bool:
    """
    Publish a message to a RabbitMQ queue
    
    Parameters:
    - queue_name: Name of the queue
    - message: Dictionary to be serialized and published
    - persistent: Whether the message should be persistent
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # Ensure queue exists
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Set message properties
        properties = pika.BasicProperties(
            delivery_mode=2 if persistent else 1,  # 2 = persistent
            content_type='application/json'
        )
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=properties
        )
        
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Error publishing message to queue {queue_name}: {str(e)}")
        return False
```

#### 1.2 Define Message Schemas
Create well-defined schemas for job messages:

```python
# app/schemas/queue.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime

class CallJob(BaseModel):
    """Schema for a call job message"""
    contact_id: UUID
    phone_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    custom_message_id: Optional[UUID] = None
    custom_message_content: Optional[str] = None
    dtmf_responses: Optional[Dict[str, Dict[str, str]]] = None
    call_run_id: Optional[UUID] = None
    priority: int = 1
    job_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    
class CallBatchJob(BaseModel):
    """Schema for a batch of calls"""
    contacts: List[UUID]
    group_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    call_run_id: Optional[UUID] = None
    call_run_name: Optional[str] = None
    call_run_description: Optional[str] = None
    job_id: UUID = Field(default_factory=lambda: uuid.uuid4())
    created_at: datetime = Field(default_factory=datetime.now)
```

### 2. Worker Architecture

#### 2.1 Call Producer
Modify the `dial_contacts` function to publish jobs to the queue instead of making calls directly:

```python
# Updated dial_contacts function in app/dialer.py
async def dial_contacts(
    contacts: Sequence[uuid.UUID] | None = None,
    group_id: Optional[uuid.UUID] = None,
    message_id: Optional[uuid.UUID] = None,
    call_run_id: Optional[uuid.UUID] = None,
    call_run_name: Optional[str] = None,
    call_run_description: Optional[str] = None,
) -> Optional[uuid.UUID]:
    """
    Queue contacts for dialing through the worker system
    
    Parameters remain the same as before
    """
    # Import here to avoid circular dependencies
    from .database import engine
    from sqlmodel import Session
    from .settings import get_system_setting
    from .queue.rabbitmq import publish_message
    from .schemas.queue import CallBatchJob
    
    with Session(engine) as session:
        # Load contacts (with phone numbers) in this session (same as before)
        # ...existing code to load contacts...
        
        # Create or get a call run
        call_run = None
        # ...existing code to create/get call run...
        
        # Create a batch job
        batch_job = CallBatchJob(
            contacts=[contact.id for contact in to_dial],
            group_id=group_id,
            message_id=message_id,
            call_run_id=call_run.id if call_run else None,
            call_run_name=call_run_name,
            call_run_description=call_run_description,
        )
        
        # Publish the batch job to the queue
        success = publish_message("gdial.call.batch", batch_job.dict())
        
        if success:
            logger.info(f"Queued batch of {len(to_dial)} calls. Batch ID: {batch_job.job_id}")
            return call_run.id if call_run else None
        else:
            logger.error("Failed to queue call batch")
            return None
```

#### 2.2 Call Worker Implementation
Create a worker script that consumes jobs from the queue:

```python
# app/workers/call_worker.py
import os
import sys
import time
import json
import logging
import uuid
from datetime import datetime
import pika
import signal
from typing import Dict, Any
from sqlmodel import Session, select

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine
from app.models import Contact, PhoneNumber, CallLog, CallRun, Message, CustomMessageLog
from app.tts import generate_message_audio
from app.config import get_settings
from app.queue.rabbitmq import get_rabbitmq_connection
from app.twilio_io import build_twiml, build_custom_twiml
from twilio.rest import Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('call_worker.log')
    ]
)
logger = logging.getLogger("call_worker")

# Get settings
settings = get_settings()
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# Setup RabbitMQ consumer
def setup_rabbitmq():
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    # Declare queues with appropriate settings
    channel.queue_declare(queue="gdial.call.single", durable=True)
    channel.queue_declare(queue="gdial.call.batch", durable=True)
    
    # Set prefetch count (how many messages to process at once)
    channel.basic_qos(prefetch_count=5)
    
    return connection, channel

def process_call_job(job_data: Dict[str, Any]):
    """Process a single call job"""
    try:
        # Extract job data
        contact_id = uuid.UUID(job_data.get('contact_id'))
        phone_id = uuid.UUID(job_data.get('phone_id')) if job_data.get('phone_id') else None
        message_id = uuid.UUID(job_data.get('message_id')) if job_data.get('message_id') else None
        custom_message_id = uuid.UUID(job_data.get('custom_message_id')) if job_data.get('custom_message_id') else None
        custom_message_content = job_data.get('custom_message_content')
        dtmf_responses = job_data.get('dtmf_responses')
        call_run_id = uuid.UUID(job_data.get('call_run_id')) if job_data.get('call_run_id') else None
        
        with Session(engine) as session:
            # Load contact
            contact = session.exec(
                select(Contact)
                .where(Contact.id == contact_id)
                .options(selectinload(Contact.phone_numbers))
            ).first()
            
            if not contact:
                logger.error(f"Contact with ID {contact_id} not found")
                return
                
            # Determine which phone numbers to use
            phones_to_try = []
            if phone_id:
                phone = session.exec(
                    select(PhoneNumber)
                    .where(
                        (PhoneNumber.id == phone_id) & 
                        (PhoneNumber.contact_id == contact_id)
                    )
                ).first()
                
                if phone:
                    phones_to_try = [phone]
            else:
                # Sort by priority
                phones_to_try = sorted(contact.phone_numbers, key=lambda p: p.priority)
            
            if not phones_to_try:
                logger.error(f"No phone numbers found for contact {contact.name}")
                return
                
            # Process custom message if present
            if custom_message_content and not custom_message_id:
                # Create a CustomMessageLog
                custom_message = CustomMessageLog(
                    contact_id=contact_id,
                    message_content=custom_message_content,
                    message_type="call",
                    dtmf_responses=dtmf_responses or {},
                    created_at=datetime.now()
                )
                session.add(custom_message)
                session.commit()
                session.refresh(custom_message)
                custom_message_id = custom_message.id
            
            # Try each phone number
            for phone in phones_to_try:
                try:
                    # Create call log
                    call_log = CallLog(
                        contact_id=contact_id,
                        phone_number_id=phone.id,
                        call_sid="pending",
                        started_at=datetime.now(),
                        status="queued",
                        answered=False,
                        message_id=message_id,
                        custom_message_log_id=custom_message_id,
                        call_run_id=call_run_id
                    )
                    session.add(call_log)
                    session.commit()
                    session.refresh(call_log)
                    
                    # Make the call
                    base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
                    
                    if custom_message_id:
                        url = f"{base_url}/custom-voice?custom_message_id={custom_message_id}"
                    else:
                        url = f"{base_url}/voice"
                        if message_id:
                            url = f"{url}?message_id={message_id}"
                    
                    call = twilio_client.calls.create(
                        to=phone.number,
                        from_=settings.TWILIO_FROM_NUMBER,
                        url=url,
                        timeout=settings.CALL_TIMEOUT_SEC,
                        status_callback_event=["completed"],
                        status_callback=f"{base_url}/call-status",
                        status_callback_method="POST"
                    )
                    
                    # Update call log with SID
                    call_log.call_sid = call.sid
                    call_log.status = "initiated"
                    session.add(call_log)
                    session.commit()
                    
                    # For now, we'll let Twilio handle the call status callbacks
                    # We won't wait for an answer here since this is a worker that
                    # needs to process many calls.
                    
                    # Successfully initiated call, no need to try more numbers
                    logger.info(f"Call initiated for contact {contact.name} with SID {call.sid}")
                    break
                    
                except Exception as e:
                    logger.error(f"Error making call to {contact.name} at {phone.number}: {str(e)}")
                    
                    # Update call log to show error
                    if 'call_log' in locals():
                        call_log.status = "error"
                        session.add(call_log)
                        session.commit()
    
    except Exception as e:
        logger.error(f"Error processing call job: {str(e)}", exc_info=True)

def process_batch_job(job_data: Dict[str, Any]):
    """Process a batch of calls by breaking it down into individual jobs"""
    try:
        from app.queue.rabbitmq import publish_message
        
        # Extract batch data
        contacts = job_data.get('contacts', [])
        message_id = job_data.get('message_id')
        call_run_id = job_data.get('call_run_id')
        
        logger.info(f"Processing batch with {len(contacts)} contacts")
        
        # Queue individual jobs for each contact
        for contact_id in contacts:
            call_job = {
                'contact_id': contact_id,
                'message_id': message_id,
                'call_run_id': call_run_id,
                'job_id': str(uuid.uuid4()),
                'created_at': datetime.now().isoformat()
            }
            
            publish_message("gdial.call.single", call_job)
        
        logger.info(f"Queued {len(contacts)} individual call jobs")
        
    except Exception as e:
        logger.error(f"Error processing batch job: {str(e)}", exc_info=True)

def callback_single(ch, method, properties, body):
    """Callback for processing single call jobs"""
    try:
        job_data = json.loads(body)
        logger.info(f"Processing single call job {job_data.get('job_id')}")
        
        process_call_job(job_data)
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error in callback_single: {str(e)}", exc_info=True)
        # Requeue the message
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def callback_batch(ch, method, properties, body):
    """Callback for processing batch jobs"""
    try:
        job_data = json.loads(body)
        logger.info(f"Processing batch job {job_data.get('job_id')}")
        
        process_batch_job(job_data)
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error in callback_batch: {str(e)}", exc_info=True)
        # Requeue the message
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    """Main worker function"""
    try:
        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutting down worker...")
            if 'connection' in locals() and connection:
                connection.close()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Connect to RabbitMQ
        connection, channel = setup_rabbitmq()
        
        # Register consumers
        channel.basic_consume(
            queue="gdial.call.single",
            on_message_callback=callback_single
        )
        
        channel.basic_consume(
            queue="gdial.call.batch",
            on_message_callback=callback_batch
        )
        
        logger.info("Call worker started. Waiting for messages...")
        
        # Start consuming
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
        if 'connection' in locals() and connection:
            connection.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main worker loop: {str(e)}", exc_info=True)
        if 'connection' in locals() and connection:
            connection.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 3. Pre-generation of TTS Audio

Modify the TTS service to work asynchronously, pre-generating audio for messages:

```python
# app/queue/tts_worker.py
import os
import sys
import json
import logging
import uuid
from datetime import datetime
import pika
from typing import Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine
from app.models import Message, CustomMessageLog
from app.tts import text_to_audio, get_audio_url
from app.config import get_settings
from app.queue.rabbitmq import get_rabbitmq_connection
from sqlmodel import Session, select

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tts_worker.log')
    ]
)
logger = logging.getLogger("tts_worker")

# Get settings
settings = get_settings()

def setup_rabbitmq():
    """Setup RabbitMQ connection and channel"""
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    # Declare TTS queue
    channel.queue_declare(queue="gdial.tts", durable=True)
    
    # Set prefetch count
    channel.basic_qos(prefetch_count=1)  # TTS can be CPU intensive, process one at a time
    
    return connection, channel

def process_tts_job(job_data: Dict[str, Any]):
    """Process a TTS job"""
    try:
        message_id = job_data.get('message_id')
        custom_message_id = job_data.get('custom_message_id')
        text_content = job_data.get('text_content')
        base_url = job_data.get('base_url') or settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        if not (message_id or custom_message_id or text_content):
            logger.error("TTS job missing required fields")
            return False
            
        # Determine file ID and text content
        file_id = message_id or custom_message_id or str(uuid.uuid4())
        
        if not text_content:
            # Load message content from database
            with Session(engine) as session:
                if message_id:
                    message = session.exec(
                        select(Message).where(Message.id == uuid.UUID(message_id))
                    ).first()
                    if message:
                        text_content = message.content
                elif custom_message_id:
                    custom_message = session.exec(
                        select(CustomMessageLog).where(CustomMessageLog.id == uuid.UUID(custom_message_id))
                    ).first()
                    if custom_message:
                        text_content = custom_message.message_content
                        
        if not text_content:
            logger.error(f"No text content found for TTS job. Message ID: {message_id}, Custom message ID: {custom_message_id}")
            return False
            
        # Generate audio
        audio_path = text_to_audio(text_content, file_id=file_id)
        
        if not audio_path:
            logger.error(f"Failed to generate audio for text: {text_content[:50]}...")
            return False
            
        # Get audio URL
        audio_url = get_audio_url(audio_path, base_url)
        
        logger.info(f"Generated audio at {audio_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing TTS job: {str(e)}", exc_info=True)
        return False

def callback_tts(ch, method, properties, body):
    """Callback for processing TTS jobs"""
    try:
        job_data = json.loads(body)
        logger.info(f"Processing TTS job {job_data.get('job_id', 'unknown')}")
        
        success = process_tts_job(job_data)
        
        if success:
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Requeue if processing failed
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
    except Exception as e:
        logger.error(f"Error in callback_tts: {str(e)}", exc_info=True)
        # Requeue the message
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    """Main TTS worker function"""
    try:
        # Connect to RabbitMQ
        connection, channel = setup_rabbitmq()
        
        # Register consumer
        channel.basic_consume(
            queue="gdial.tts",
            on_message_callback=callback_tts
        )
        
        logger.info("TTS worker started. Waiting for messages...")
        
        # Start consuming
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("TTS worker interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in TTS worker loop: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 4. Supervisor Configuration
Create a supervisor configuration to manage the worker processes:

```ini
# supervisor/gdial_workers.conf
[program:call_worker]
command=/path/to/venv/bin/python /path/to/app/workers/call_worker.py
numprocs=3
process_name=%(program_name)s_%(process_num)02d
directory=/path/to/gdial
user=gdial
autostart=true
autorestart=true
startretries=10
redirect_stderr=true
stdout_logfile=/var/log/gdial/call_worker_%(process_num)02d.log
environment=PYTHONUNBUFFERED=1

[program:tts_worker]
command=/path/to/venv/bin/python /path/to/app/workers/tts_worker.py
numprocs=2
process_name=%(program_name)s_%(process_num)02d
directory=/path/to/gdial
user=gdial
autostart=true
autorestart=true
startretries=10
redirect_stderr=true
stdout_logfile=/var/log/gdial/tts_worker_%(process_num)02d.log
environment=PYTHONUNBUFFERED=1

[group:gdial_workers]
programs=call_worker,tts_worker
priority=999
```

### 5. System Monitoring

Integrate Prometheus metrics for monitoring queue depth and worker status:

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import threading
import time
import logging
from functools import wraps

# Metrics definitions
QUEUE_DEPTH = Gauge('gdial_queue_depth', 'Number of messages in queue', ['queue_name'])
JOBS_PROCESSED = Counter('gdial_jobs_processed', 'Number of jobs processed', ['job_type', 'status'])
PROCESSING_TIME = Histogram('gdial_processing_time', 'Time to process a job', ['job_type'])
WORKER_COUNT = Gauge('gdial_worker_count', 'Number of active workers', ['worker_type'])

def start_metrics_server(port=8000):
    """Start the Prometheus metrics server"""
    start_http_server(port)
    logging.info(f"Started metrics server on port {port}")

def timed_function(job_type):
    """Decorator to time function execution and record metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                JOBS_PROCESSED.labels(job_type=job_type, status='success').inc()
                return result
            except Exception as e:
                JOBS_PROCESSED.labels(job_type=job_type, status='error').inc()
                raise
            finally:
                PROCESSING_TIME.labels(job_type=job_type).observe(time.time() - start_time)
        return wrapper
    return decorator

def start_queue_monitor(rabbitmq_url, queue_names, check_interval=5):
    """Start a thread to monitor queue depths"""
    import pika
    
    def _monitor_queues():
        while True:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
                channel = connection.channel()
                
                for queue_name in queue_names:
                    try:
                        queue = channel.queue_declare(queue=queue_name, passive=True)
                        QUEUE_DEPTH.labels(queue_name=queue_name).set(queue.method.message_count)
                    except Exception as e:
                        logging.error(f"Error getting queue depth for {queue_name}: {str(e)}")
                
                connection.close()
            except Exception as e:
                logging.error(f"Error in queue monitor: {str(e)}")
                
            time.sleep(check_interval)
    
    thread = threading.Thread(target=_monitor_queues, daemon=True)
    thread.start()
    logging.info("Started queue depth monitor thread")
```

## Implementation Phases

### Phase 1: Infrastructure Setup
1. Add RabbitMQ to development environment
2. Implement rabbitmq.py connection module
3. Create basic queue message schemas
4. Set up supervisor configurations for workers

### Phase 2: Worker Processes
1. Implement the call_worker.py
2. Implement the tts_worker.py
3. Modify TwiML generation to use pre-generated audio when available

### Phase 3: API Modifications
1. Update dial_contacts to use queue instead of direct calls
2. Modify manual call functions to use queue
3. Add queue status endpoints to monitor system health

### Phase 4: Monitoring & Testing
1. Implement Prometheus metrics
2. Add worker health checks
3. Test with small batches, then scale up
4. Document new architecture in system documentation

## Benefits

1. **Improved Scalability:**
   - Workers can be deployed on multiple servers
   - Call processing decoupled from user interface
   - TTS generation handled asynchronously

2. **Enhanced Reliability:**
   - Message persistence during system failures
   - Better error handling and retries
   - Reduced chance of database deadlocks

3. **Monitoring & Observability:**
   - Real-time metrics on queue depth
   - Worker performance statistics
   - Improved logging and error tracking

4. **Future Extensibility:**
   - Easy to add new worker types for additional functionality
   - Support for priority queues
   - Potential for distributed TTS with Coqui/Piper

## Integration with Current System

The proposed changes maintain backward compatibility with existing code while enhancing functionality. The main application continues to work as before, but with improved performance and scalability. The RabbitMQ integration is designed to be optional, allowing the system to fall back to direct processing if needed.

## Coqui TTS/Piper Implementation

For phase 2 or 3, we can integrate Coqui TTS as an alternative to Google TTS:

```python
# app/tts/coqui.py
import os
import logging
import tempfile
import uuid
from pathlib import Path
from subprocess import Popen, PIPE

logger = logging.getLogger("coqui_tts")

# Configuration
PIPER_BINARY = os.getenv("PIPER_BINARY", "/usr/local/bin/piper")
PIPER_MODEL = os.getenv("PIPER_MODEL", "/usr/local/share/piper/sv/sv_SE-marin-medium.onnx")
AUDIO_DIR = Path("static/audio")

def generate_audio_coqui(text, file_id=None, voice_pitch=0, voice_speed=1.0):
    """
    Generate audio using Coqui TTS/Piper
    
    Parameters:
    - text: Text to convert to speech
    - file_id: Optional UUID for the output file (generated if None)
    - voice_pitch: Pitch adjustment (-10 to 10)
    - voice_speed: Speed adjustment (0.5 to 2.0)
    
    Returns:
    - Path to generated audio file or None if generation failed
    """
    try:
        # Generate a file ID if not provided
        if file_id is None:
            file_id = str(uuid.uuid4())
            
        # Ensure valid input
        if not text:
            logger.error("Empty text provided to Coqui TTS function")
            return None
            
        # Define output path
        output_path = AUDIO_DIR / f"{file_id}.wav"
        
        # Create a temporary file for the text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp:
            temp.write(text)
            temp_path = temp.name
            
        try:
            # Build piper command
            cmd = [
                PIPER_BINARY,
                "--model", PIPER_MODEL,
                "--output_file", str(output_path)
            ]
            
            # Add optional parameters
            if voice_pitch != 0:
                cmd.extend(["--pitch", str(voice_pitch)])
                
            if voice_speed != 1.0:
                cmd.extend(["--rate", str(voice_speed)])
                
            # Input from file
            cmd.extend(["--file", temp_path])
            
            # Execute piper
            logger.info(f"Executing Piper: {' '.join(cmd)}")
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Piper failed: {stderr.decode()}")
                return None
                
            # Convert to MP3 if needed (using pydub)
            try:
                from pydub import AudioSegment
                mp3_path = AUDIO_DIR / f"{file_id}.mp3"
                AudioSegment.from_wav(output_path).export(mp3_path, format="mp3")
                
                # Clean up WAV file
                if mp3_path.exists():
                    os.remove(output_path)
                    return mp3_path
            except Exception as e:
                logger.error(f"Error converting to MP3: {str(e)}")
                # Just return the WAV if conversion fails
                return output_path
                
            return output_path
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error generating speech with Coqui: {str(e)}", exc_info=True)
        return None
```

This would be integrated into the existing TTS module with a configuration option to choose between Google TTS and Coqui/Piper.