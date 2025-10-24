"""Database connection and seeding"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
import csv
from pathlib import Path
from uuid import UUID
import json

from models import EventDocument
from config import MONGODB_URL, MONGODB_DB, CSV_PATH

logger = logging.getLogger(__name__)

class DB:
    client: AsyncIOMotorClient = None

db = DB()

async def connect_db():
    """Initialize Beanie ODM"""
    db.client = AsyncIOMotorClient(MONGODB_URL)
    await init_beanie(
        database=db.client[MONGODB_DB],
        document_models=[EventDocument]
    )
    logger.warning("Database connected")

async def disconnect_db():
    """Close database connection"""
    if db.client:
        db.client.close()

async def seed_csv():
    """Idempotent CSV seeding"""
    if await EventDocument.count() > 0:
        logger.warning(f"Database already seeded, skipping")
        return

    csv_path = Path(CSV_PATH)
    if not csv_path.exists():
        logger.warning("No CSV found, skipping seed")
        return

    logger.warning(f"Seeding from {csv_path}")
    batch, errors = [], 0

    with open(csv_path, 'r') as f:
        for row in csv.DictReader(f):
            try:
                from datetime import datetime
                event = EventDocument(
                    event_id=UUID(row['event_id']),
                    occurred_at=datetime.fromisoformat(row['occurred_at'].replace('Z', '+00:00')),
                    user_id=int(row['user_id']),
                    event_type=row['event_type'],
                    properties=json.loads(row['properties_json']),
                    ingested_at=datetime.utcnow()
                )
                batch.append(event)

                if len(batch) >= 1000:
                    await EventDocument.insert_many(batch, ordered=False)
                    batch = []
            except Exception as e:
                errors += 1
                if errors <= 3:
                    logger.error(f"Parse error: {e}")

    if batch:
        await EventDocument.insert_many(batch, ordered=False)

    total = await EventDocument.count()
    logger.warning(f"Seeded {total} events, {errors} errors")