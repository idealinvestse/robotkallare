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
from sqlmodel import Session, select, selectinload

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine
from app.models import Contact, PhoneNumber, CallLog, CallRun, Message, CustomMessageLog
# Import directly from the module to avoid circular imports
from app.tts import generate_message_audio  # tts.py module, not tts/ package
from app.config import get_settings
from app.queue.rabbitmq import get_rabbitmq_connection
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