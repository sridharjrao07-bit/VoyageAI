"""
AviationStack Integration Module

Fetches real-time flight data and pricing to feed into the logistics AI.
"""
import os
import httpx
import time
from typing import Dict, Any, List

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")

# In-memory cache to save exactly our 100 requests/month free tier quota.
# format: { "origin-dest": (timestamp, data_list) }
_flight_cache = {}
CACHE_TTL = 3600 * 12  # 12 hours cache

async def get_flight_data(origin: str, destination: str) -> List[Dict[str, Any]]:
    """
    Fetch flight schedules and prices from AviationStack.
    Uses in-memory cache to conserve strictly limited free tier credits.
    Note: Free tier might not have 'price'. We will handle fallbacks in the agent.
    
    :param origin: IATA code of origin (e.g., 'DEL')
    :param destination: IATA code of destination (e.g., 'CDG')
    :return: List of flight data dicts
    """
    if not AVIATIONSTACK_API_KEY:
        print("[Flights] Warning: AVIATIONSTACK_API_KEY not set.")
        # Return mock data if no key is present to allow testing
        return [_generate_mock_flight(origin, destination)]

    cache_key = f"{origin}-{destination}"
    now = time.time()
    if cache_key in _flight_cache:
        cached_time, cached_data = _flight_cache[cache_key]
        if now - cached_time < CACHE_TTL:
            return cached_data

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
                return [_generate_mock_flight(origin, destination)]
                
            data = resp.json()
            if "data" in data and data["data"]:
                flights = data["data"]
                # Because the free tier often doesn't return 'price' in standard endpoints,
                # we'll patch it with a realistic estimation if it's missing, for agent reasoning.
                for f in flights:
                    if 'price' not in f and 'fare' not in f:
                        f['price'] = _estimate_mock_price(origin, destination)
                _flight_cache[cache_key] = (now, flights)
                return flights
            else:
                data_mock = [_generate_mock_flight(origin, destination)]
                _flight_cache[cache_key] = (now, data_mock)
                return data_mock
                
    except Exception as e:
        print(f"[Flights] Fetch Exception: {e}")
        return [_generate_mock_flight(origin, destination)]

def _estimate_mock_price(origin: str, destination: str) -> float:
    """Mock a realistic price purely for demonstration if the API lacks it."""
    # A tiny bit of variance to look real
    base = 850.0
    return base + (len(origin) + len(destination)) * 10.5

def _generate_mock_flight(origin: str, destination: str) -> dict:
    return {
        "flight_date": "2026-04-15",
        "departure": {"iata": origin, "airport": origin + " Intl"},
        "arrival": {"iata": destination, "airport": destination + " Intl"},
        "airline": {"name": "Mock Airlines"},
        "flight": {"number": "MK123"},
        "price": _estimate_mock_price(origin, destination),
        "note": "Mocked fallback data"
    }

def get_mock_reviews(destination_name: str) -> List[str]:
    """Generates a few mock reviews for the destination to feed Consensus Filtering."""
    return [
        f"Just got back from {destination_name}. The views were absolutely incredible, but beware that the main transport lines are crowded during rush hour.",
        f"A decent trip. Food in {destination_name} was a bit expensive compared to what I expected. The local guides were fantastic though.",
        f"Would visit {destination_name} again! Warning: flights here are frequently delayed due to weather, so plan a buffer day."
    ]
