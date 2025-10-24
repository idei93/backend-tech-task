"""Analytics calculations"""
from datetime import timedelta

from models import EventDocument
from helpers import parse_date


async def calculate_dau(from_date: str, to_date: str):
    """Daily Active Users"""
    start = parse_date(from_date)
    end = parse_date(to_date) + timedelta(days=1)

    if start > end:
        raise ValueError("from_date must be before to_date")

    pipeline = [
        {"$match": {"occurred_at": {"$gte": start, "$lt": end}}},
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$occurred_at"}},
            "user_id": 1
        }},
        {"$group": {"_id": {"date": "$date", "user_id": "$user_id"}}},
        {"$group": {"_id": "$_id.date", "unique_users": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]

    result = []
    async for doc in EventDocument.aggregate(pipeline):
        result.append({"date": doc["_id"], "dau": doc["unique_users"]})

    return {"from": from_date, "to": to_date, "data": result}


async def calculate_top_events(from_date: str, to_date: str, limit: int):
    """Top event types by count"""
    start = parse_date(from_date)
    end = parse_date(to_date) + timedelta(days=1)

    pipeline = [
        {"$match": {"occurred_at": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    result = []
    async for doc in EventDocument.aggregate(pipeline):
        result.append({"event_type": doc["_id"], "count": doc["count"]})

    return {"from": from_date, "to": to_date, "limit": limit, "data": result}


async def calculate_retention(start_date: str, windows: int):
    """Cohort retention analysis"""
    cohort_start = parse_date(start_date)
    cohort_end = cohort_start + timedelta(days=1)

    pipeline = [
        {"$match": {
            "occurred_at": {
                "$gte": cohort_start,
                "$lt": cohort_end
            }
        }},
        {"$group": {"_id": "$user_id"}}
    ]

    cohort_users_cursor = EventDocument.aggregate(pipeline)
    cohort_users = [doc["_id"] async for doc in cohort_users_cursor]

    cohort_size = len(cohort_users)
    if cohort_size == 0:
        return {
            "cohort_date": start_date,
            "cohort_size": 0,
            "windows": windows,
            "retention": []
        }

    retention_data = []
    for window in range(windows):
        window_start = cohort_start + timedelta(days=window + 1)
        window_end = window_start + timedelta(days=1)

        retention_pipeline = [
            {"$match": {
                "user_id": {"$in": cohort_users},
                "occurred_at": {
                    "$gte": window_start,
                    "$lt": window_end
                }
            }},
            {"$group": {"_id": "$user_id"}}
        ]

        retained_cursor = EventDocument.aggregate(retention_pipeline)
        retained = [doc["_id"] async for doc in retained_cursor]

        rate = (len(retained) / cohort_size * 100) if cohort_size > 0 else 0

        retention_data.append({
            "day": window + 1,
            "date": window_start.strftime("%Y-%m-%d"),
            "retained_users": len(retained),
            "retention_rate": round(rate, 2)
        })

    return {
        "cohort_date": start_date,
        "cohort_size": cohort_size,
        "windows": windows,
        "retention": retention_data
    }


async def get_metrics():
    """System metrics"""
    total = await EventDocument.count()

    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]

    top_types = []
    async for doc in EventDocument.aggregate(pipeline):
        top_types.append({"event_type": doc["_id"], "count": doc["count"]})

    oldest = await EventDocument.find_one(sort=[("occurred_at", 1)])
    newest = await EventDocument.find_one(sort=[("occurred_at", -1)])

    return {
        "total_events": total,
        "top_event_types": top_types,
        "date_range": {
            "oldest": oldest.occurred_at.isoformat() if oldest else None,
            "newest": newest.occurred_at.isoformat() if newest else None
        }
    }