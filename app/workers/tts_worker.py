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
from app.tts import text_to_audio
from app.config import get_settings
from app.tts_queue import set_tts_job_status

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
    """Process a TTS job (scalable, parallel, async-safe)."""
    try:
        job_id = job_data.get('job_id')
        text = job_data.get('text')
        voice = job_data.get('voice', 'google')
        output_format = job_data.get('output_format', 'mp3')

        if not job_id or not text:
            logger.error("TTS job missing required fields: job_id or text")
            return False

        set_tts_job_status(job_id, "processing")
        
        # Generate audio (sync call, but worker can be run in parallel processes)
        audio_path = text_to_audio(text, output_format=output_format, file_id=job_id)
        if not audio_path:
            logger.error(f"Failed to generate audio for job {job_id}")
            set_tts_job_status(job_id, "failed")
            return False
        set_tts_job_status(job_id, "done", audio_path=audio_path)
        logger.info(f"Generated audio for job {job_id} at {audio_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing TTS job: {str(e)}", exc_info=True)
        if job_data.get('job_id'):
            set_tts_job_status(job_data['job_id'], "failed")
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