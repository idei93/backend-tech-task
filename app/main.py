"""FastAPI application"""
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from typing import List
import logging

from models import EventInput, EventDocument
from db import connect_db, disconnect_db, seed_csv
from messaging import connect_queue, disconnect_queue, publish_event
from analytics import calculate_dau, calculate_top_events, calculate_retention, get_metrics
from helpers import RateLimiter, to_uuid_str, from_uuid_str
from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logging.basicConfig(level=logging.WARNING, format='{"time":"%(asctime)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await connect_queue()
    await seed_csv()
    logger.warning("System initialized")
    yield
    await disconnect_queue()
    await disconnect_db()


app = FastAPI(title="Event Analytics API", version="1.0.0", lifespan=lifespan)
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    if not rate_limiter.allow_request(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)


@app.post("/events", status_code=202)
async def ingest_events(events: List[EventInput]):
    """Ingest batch of events"""
    if not events or len(events) > 10000:
        raise HTTPException(status_code=400, detail="Invalid batch size")

    for event in events:
        event_dict = event.model_dump()
        event_dict['event_id'] = to_uuid_str(event_dict['event_id'])
        await publish_event(event_dict)

    return {"status": "accepted", "count": len(events)}


@app.get("/stats/dau")
async def get_dau(from_date: str, to_date: str):
    """Get Daily Active Users"""
    try:
        return await calculate_dau(from_date, to_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stats/top-events")
async def get_top_events(from_date: str, to_date: str, limit: int = 10):
    """Get top event types"""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be 1-100")
    try:
        return await calculate_top_events(from_date, to_date, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stats/retention")
async def get_retention(start_date: str, windows: int = 3):
    """Get cohort retention"""
    if windows < 1 or windows > 12:
        raise HTTPException(status_code=400, detail="Windows must be 1-12")
    try:
        return await calculate_retention(start_date, windows)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """System metrics"""
    return await get_metrics()