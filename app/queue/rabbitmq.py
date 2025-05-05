import pika
import json
import logging
import os
from typing import Dict, Any, Optional
from functools import lru_cache
from app.models import OutboxJob
from app.utils.safe_call import safe_call
from sqlmodel import Session

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

@safe_call(default=False)
def publish_message(queue_name: str, message: Dict[str, Any], persistent: bool = True, session: Optional[Session] = None) -> bool:
    """
    Publish a message to a RabbitMQ queue. If fails, persist to OutboxJob for retry.
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
        # Persist to OutboxJob for retry if session is provided
        if session is not None:
            job = OutboxJob(service="rabbitmq", payload={"queue_name": queue_name, "message": message, "persistent": persistent})
            session.add(job)
            session.commit()
            logger.info(f"Persisted failed RabbitMQ job to OutboxJob: {job.id}")
        return False