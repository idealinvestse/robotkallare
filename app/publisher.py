import aio_pika
import logging
import json
from typing import Optional

# Constants (Consider moving to settings)
GDial_EXCHANGE_NAME = "gdial_exchange"

logger = logging.getLogger(__name__)

class QueuePublisher:
    def __init__(self, channel: aio_pika.abc.AbstractChannel, exchange_name: str = GDial_EXCHANGE_NAME):
        self.channel = channel
        self.exchange_name = exchange_name
        self._exchange: Optional[aio_pika.abc.AbstractExchange] = None
        logger.info(f"QueuePublisher initialized for exchange '{exchange_name}'")

    async def _ensure_exchange(self):
        """Declare exchange if not already done."""
        if not self._exchange:
            logger.debug(f"Declaring exchange '{self.exchange_name}'...")
            self._exchange = await self.channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
            )
            logger.debug(f"Exchange '{self.exchange_name}' declared.")
        return self._exchange

    async def publish(self, routing_key: str, body: dict):
        """Publish a JSON-serialized message to the configured exchange."""
        exchange = await self._ensure_exchange()
        message_body = json.dumps(body).encode('utf-8')
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT, 
            content_type='application/json',
            content_encoding='utf-8'
        )
        try:
            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"Published message to exchange '{self.exchange_name}' with routing key '{routing_key}' (Payload: {body})")
        except Exception as e:
            logger.error(f"Failed to publish message to exchange '{self.exchange_name}', routing key '{routing_key}': {e}", exc_info=True)
            raise
