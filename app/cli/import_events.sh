#!/bin/bash
[ ! -f "$1" ] && echo "Usage: $0 <csv-file>" && exit 1

CSV_FILE="$1"
CONTAINER="events-api"

docker cp "$CSV_FILE" "$CONTAINER:/tmp/import.csv"
docker exec "$CONTAINER" python -c """
import asyncio
import csv
import json
import os
from uuid import UUID
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_HOST, MONGODB_PORT, MONGODB_USER, MONGODB_PASSWORD, MONGODB_DB
from models import EventDocument
from beanie import init_beanie

async def import_csv():

    mongo_url = os.getenv('MONGODB_URL')
    client = AsyncIOMotorClient(mongo_url)
    await init_beanie(database=client[MONGODB_DB], document_models=[EventDocument])

    batch = []
    with open('/tmp/import.csv', 'r') as f:
        for row in csv.DictReader(f):
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

    if batch:
        await EventDocument.insert_many(batch, ordered=False)

    print(f'Imported {await EventDocument.count()} events')

asyncio.run(import_csv())
"""