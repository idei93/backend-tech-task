"""Integration tests"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from main import app
from db import connect_db, disconnect_db
from models import EventDocument


@pytest.fixture(scope="function")
async def setup():
    """Setup and teardown for each test"""
    await connect_db()

    # Clean up test data before each test
    await EventDocument.find(
        EventDocument.event_type == "test"
    ).delete()

    yield

    # Clean up after test
    await EventDocument.find(
        EventDocument.event_type == "test"
    ).delete()

    await disconnect_db()


@pytest.mark.asyncio
async def test_event_ingestion(setup):
    """Test event ingestion endpoint"""
    # Mock the message queue publishing
    with patch('main.publish_event', new_callable=AsyncMock) as mock_publish:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/events", json=[{
                "event_id": str(uuid4()),
                "occurred_at": datetime.utcnow().isoformat() + "Z",
                "user_id": 1,
                "event_type": "test",
                "properties": {"test": "data"}
            }])

            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            # Verify the event was published to the queue
            assert mock_publish.called


@pytest.mark.asyncio
async def test_validation_error(setup):
    """Test input validation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Invalid UUID
        response = await client.post("/events", json=[{
            "event_id": "not-a-uuid",
            "occurred_at": "2025-08-01T10:00:00Z",
            "user_id": 1,
            "event_type": "test",
            "properties": {}
        }])

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_dau_endpoint(setup):
    """Test DAU statistics endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/stats/dau",
            params={
                "from_date": "2025-08-01",
                "to_date": "2025-08-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "from" in data
        assert "to" in data
        assert "data" in data


@pytest.mark.asyncio
async def test_health_check(setup):
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"