"""Helper utilities"""
import time
from collections import defaultdict
from typing import Dict
from datetime import datetime


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, list] = defaultdict(list)

    def allow_request(self, client_id: str) -> bool:
        now = time.time()

        self.clients[client_id] = [
            ts for ts in self.clients[client_id]
            if now - ts < self.window_seconds
        ]

        if len(self.clients[client_id]) < self.max_requests:
            self.clients[client_id].append(now)
            return True
        return False


def parse_date(date_str: str) -> datetime:
    """Parse YYYY-MM-DD to datetime"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date: {date_str}. Use YYYY-MM-DD")


def to_uuid_str(uuid_obj) -> str:
    """Convert UUID to string for serialization"""
    from uuid import UUID
    return str(uuid_obj) if isinstance(uuid_obj, UUID) else uuid_obj


def from_uuid_str(uuid_str) -> 'UUID':
    """Convert string to UUID"""
    from uuid import UUID
    return UUID(uuid_str) if isinstance(uuid_str, str) else uuid_str