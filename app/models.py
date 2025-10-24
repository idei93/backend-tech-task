"""Data models for events"""
from pydantic import BaseModel, Field, field_validator
from beanie import Document
from pymongo import IndexModel, ASCENDING
from typing import Dict, Any
from datetime import datetime
from uuid import UUID

class EventInput(BaseModel):
    """API input validation"""
    event_id: UUID
    occurred_at: str
    user_id: int
    event_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('occurred_at')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO-8601: {v}")

    @field_validator('event_type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("event_type required")
        return v.strip()

    @field_validator('user_id')
    @classmethod
    def validate_user(cls, v: int) -> int:
        if v < 1:
            raise ValueError("user_id must be positive")
        return v

class EventDocument(Document):
    """MongoDB document with indexes"""
    event_id: UUID
    occurred_at: datetime
    user_id: int
    event_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "events"
        indexes = [
            IndexModel([("event_id", ASCENDING)], unique=True),
            IndexModel([("occurred_at", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("event_type", ASCENDING)]),
            IndexModel([("occurred_at", ASCENDING), ("user_id", ASCENDING)]),
            IndexModel([("occurred_at", ASCENDING), ("event_type", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("occurred_at", ASCENDING)]),
        ]