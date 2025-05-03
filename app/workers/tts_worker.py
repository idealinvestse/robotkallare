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
# Import directly from the module to avoid circular imports
from app.tts import text_to_audio, get_audio_url  # tts.py module, not tts/ package
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