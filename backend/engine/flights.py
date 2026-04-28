"""
AviationStack Integration Module

Fetches real-time flight data and pricing to feed into the logistics AI.
"""
import os
import httpx
from typing import Dict, Any, List

from engine.redis_cache import redis_cache

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")


@redis_cache(prefix="flights", ttl=3600)
async def get_flight_data(origin: str, destination: str) -> List[Dict[str, Any]]:
    """
    Fetch flight schedules and prices from AviationStack.
    Cached by Redis via @redis_cache decorator (1 hour TTL).

    :param origin: IATA code of origin (e.g., 'DEL')
    :param destination: IATA code of destination (e.g., 'CDG')
    :return: List of flight data dicts, or empty list if unavailable
    :raises HTTPException: if API key is missing
    """
    if not AVIATIONSTACK_API_KEY:
        print("[Flights] AVIATIONSTACK_API_KEY not set — returning empty.")
        return []

    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': AVIATIONSTACK_API_KEY,
        'dep_iata': origin,
        'arr_iata': destination,
        'limit': 1
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)

            if resp.status_code != 200:
                print(f"[Flights] API Error {resp.status_code}: {resp.text}")
                return []

            data = resp.json()
            if "data" in data and data["data"]:
                return data["data"]
            else:
                return []

    except Exception as e:
        print(f"[Flights] Fetch Exception: {e}")
        return []
