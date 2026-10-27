import asyncio
import os
import uuid

import requests
from fastapi import Request
from starlette.concurrency import run_in_threadpool

from app.http_utils import get_client_ip
from app.settings import GA_MEASUREMENT_ID

GA_API_SECRET = os.getenv("GA_API_SECRET", "")
GA_MP_ENDPOINT = "https://www.google-analytics.com/mp/collect"


def ga4_configured() -> bool:
    return bool(GA_MEASUREMENT_ID) and bool(GA_API_SECRET)


def client_id_for_request(request: Request) -> str:
    """Stable-but-anonymous client id derived from the request IP (no cookies)."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, get_client_ip(request)))


def _send_event(client_id: str, name: str, params: dict) -> None:
    try:
        requests.post(
            GA_MP_ENDPOINT,
            params={"measurement_id": GA_MEASUREMENT_ID, "api_secret": GA_API_SECRET},
            json={"client_id": client_id, "events": [{"name": name, "params": params}]},
            timeout=2,
        )
    except Exception as e:
        print(f"🔥 GA4 event send error ({name}): {e}")


async def track_event(client_id: str, name: str, params: dict | None = None) -> None:
    """Fire a GA4 Measurement Protocol event without blocking the response."""
    if not ga4_configured():
        return
    asyncio.create_task(run_in_threadpool(_send_event, client_id, name, params or {}))
