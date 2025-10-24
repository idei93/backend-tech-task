"""Test idempotency"""
import pytest
from uuid import UUID
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from models import EventDocument
from db import connect_db, disconnect_db


@pytest.fixture(scope="function")
async def setup():
    """Setup and teardown for each test"""
    await connect_db()

    await EventDocument.find(
        EventDocument.event_type == "test"
    ).delete()

    test_uuids = [
        UUID("12345678-1234-1234-1234-123456789abc"),
        UUID("11111111-1111-1111-1111-111111111111"),
        UUID("22222222-2222-2222-2222-222222222222"),
        UUID("33333333-3333-3333-3333-333333333333"),
    ]

    for test_uuid in test_uuids:
        await EventDocument.find(
            EventDocument.event_id == test_uuid
        ).delete()

    yield

    await EventDocument.find(
        EventDocument.event_type == "test"
    ).delete()

    for test_uuid in test_uuids:
        await EventDocument.find(
            EventDocument.event_id == test_uuid
        ).delete()

    await disconnect_db()


@pytest.mark.asyncio
async def test_unique_uuid_constraint(setup):
    """Duplicate event_id should raise DuplicateKeyError"""
    event_id = UUID("12345678-1234-1234-1234-123456789abc")

    doc1 = EventDocument(
        event_id=event_id,
        occurred_at=datetime(2025, 8, 1, 12, 0, 0),
        user_id=999,
        event_type="test",
        properties={"test": "data"},
        ingested_at=datetime.utcnow()
    )

    await doc1.insert()

    doc2 = EventDocument(
        event_id=event_id,  # Same UUID
        occurred_at=datetime(2025, 8, 1, 13, 0, 0),  # Different time
        user_id=888,  # Different user
        event_type="test",
        properties={"test": "different"},
        ingested_at=datetime.utcnow()
    )

    with pytest.raises(DuplicateKeyError):
        await doc2.insert()


@pytest.mark.asyncio
async def test_different_uuids_allowed(setup):
    """Different event_ids should create separate records"""
    doc1 = EventDocument(
        event_id=UUID("11111111-1111-1111-1111-111111111111"),
        occurred_at=datetime(2025, 8, 1),
        user_id=1001,
        event_type="test",
        properties={},
        ingested_at=datetime.utcnow()
    )

    doc2 = EventDocument(
        event_id=UUID("22222222-2222-2222-2222-222222222222"),
        occurred_at=datetime(2025, 8, 1),
        user_id=1001,  # Same user, different event
        event_type="test",
        properties={},
        ingested_at=datetime.utcnow()
    )

    result1 = await doc1.insert()
    result2 = await doc2.insert()

    assert result1 is not None
    assert result2 is not None


@pytest.mark.asyncio
async def test_idempotent_insert(setup):
    """Worker should handle duplicates gracefully"""
    event_id = UUID("33333333-3333-3333-3333-333333333333")

    doc1 = EventDocument(
        event_id=event_id,
        occurred_at=datetime(2025, 8, 1),
        user_id=1,
        event_type="login",
        properties={},
        ingested_at=datetime.utcnow()
    )

    try:
        await doc1.insert()
        success_count = 1
    except DuplicateKeyError:
        success_count = 0

    doc2 = EventDocument(
        event_id=event_id,
        occurred_at=datetime(2025, 8, 1),
        user_id=1,
        event_type="login",
        properties={},
        ingested_at=datetime.utcnow()
    )

    try:
        await doc2.insert()
        success_count += 1
    except DuplicateKeyError:
        success_count += 1

    assert success_count == 2

    count = await EventDocument.find(EventDocument.event_id == event_id).count()
    assert count == 1