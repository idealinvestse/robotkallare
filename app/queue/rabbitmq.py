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