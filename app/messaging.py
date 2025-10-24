"""RabbitMQ connection and setup"""
import aio_pika
import logging
import asyncio

from config import RABBITMQ_URL

logger = logging.getLogger(__name__)


class MessageMQ:
    connection: aio_pika.Connection = None
    channel: aio_pika.Channel = None
    events_queue: aio_pika.Message = None


messagemq = MessageMQ()


async def connect_queue():
    """Initialize RabbitMQ with DLQ"""
    for attempt in range(10):
        try:
            messagemq.connection = await aio_pika.connect_robust(RABBITMQ_URL, timeout=10)
            messagemq.channel = await messagemq.connection.channel()
            await messagemq.channel.set_qos(prefetch_count=100)

            # Dead letter exchange
            dlx = await messagemq.channel.declare_exchange(
                "events_dlx",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            dlq = await messagemq.channel.declare_queue("events_dead_letter", durable=True)
            await dlq.bind(dlx, routing_key="events")

            messagemq.events_queue = await messagemq.channel.declare_queue(
                "events",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "events_dlx",
                    "x-dead-letter-routing-key": "events"
                }
            )

            logger.warning("Queue connected")
            return
        except Exception as e:
            if attempt < 9:
                await asyncio.sleep(5)
            else:
                raise Exception(f"Failed to connect to RabbitMQ: {e}")


async def disconnect_queue():
    """Close RabbitMQ connection"""
    if messagemq.connection and not messagemq.connection.is_closed:
        await messagemq.connection.close()


async def publish_event(event_dict: dict):
    """Publish event to queue"""
    import msgpack
    body = msgpack.packb(event_dict)

    message = aio_pika.Message(
        body=body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/msgpack"
    )

    await messagemq.channel.default_exchange.publish(message, routing_key="events")