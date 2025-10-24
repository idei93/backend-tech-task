"""Worker process for consuming events from queue"""
import asyncio
import logging
import msgpack
import signal
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from models import EventInput, EventDocument
from db import connect_db, disconnect_db
from messaging import connect_queue, disconnect_queue, messagemq
from helpers import from_uuid_str

logging.basicConfig(level=logging.WARNING, format='{"time":"%(asctime)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self):
        self.running = True
        self.processed = 0
        self.failed = 0

    async def process_message(self, message):
        """Process single event message"""
        async with message.process(requeue=False):
            try:
                data = msgpack.unpackb(message.body, raw=False)

                if 'event_id' in data:
                    data['event_id'] = from_uuid_str(data['event_id'])

                event = EventInput(**data)

                doc = EventDocument(
                    event_id=event.event_id,
                    occurred_at=datetime.fromisoformat(event.occurred_at.replace('Z', '+00:00')),
                    user_id=event.user_id,
                    event_type=event.event_type,
                    properties=event.properties,
                    ingested_at=datetime.utcnow()
                )

                try:
                    await doc.insert()
                    self.processed += 1
                except DuplicateKeyError:
                    self.processed += 1

                if self.processed % 5000 == 0:
                    logger.warning(f"Processed: {self.processed}, Failed: {self.failed}")

            except Exception as e:
                self.failed += 1
                logger.error(f"Error: {e}")

    async def start(self):
        """Start worker"""
        await connect_db()
        await connect_queue()
        await messagemq.events_queue.consume(self.process_message)
        logger.warning("Worker started")

        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop worker gracefully"""
        self.running = False
        await disconnect_queue()
        await disconnect_db()
        logger.warning(f"Worker stopped. Processed: {self.processed}, Failed: {self.failed}")


async def main():
    worker = Worker()
    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

from models.event import EventInput
from services.event_service import EventService
from core.database import init_db, close_db
from core.rabbitmq import init_rabbitmq, close_rabbitmq, rabbitmq

logging.basicConfig(level=logging.WARNING, format='{"time":"%(asctime)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)


class EventWorker:
    def __init__(self):
        self.service = EventService()
        self.running = True
        self.processed = 0
        self.failed = 0

    async def process_message(self, message):
        """Process event from queue"""
        async with message.process(requeue=False):
            try:
                # Deserialize with msgpack
                data = msgpack.unpackb(message.body, raw=False)

                # Convert event_id string back to UUID
                if 'event_id' in data and isinstance(data['event_id'], str):
                    data['event_id'] = UUID(data['event_id'])

                event = EventInput(**data)

                await self.service.save_event(event)
                self.processed += 1

                if self.processed % 5000 == 0:
                    logger.warning(f"Processed: {self.processed}, Failed: {self.failed}")

            except Exception as e:
                self.failed += 1
                logger.error(f"Processing error: {e}")

    async def start(self):
        await init_db()
        await init_rabbitmq()

        await rabbitmq.events_queue.consume(self.process_message)
        logger.warning("Worker started")

        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        self.running = False
        await close_rabbitmq()
        await close_db()
        logger.warning(f"Worker stopped. Processed: {self.processed}, Failed: {self.failed}")


async def main():
    worker = EventWorker()
    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())