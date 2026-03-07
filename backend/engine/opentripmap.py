"""
OpenTripMap API integration
Fetches real POI photos and details for destinations.
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENTRIPMAP_API_KEY", "")
BASE_URL = os.getenv("OPENTRIPMAP_BASE_URL", "https://api.opentripmap.com/0.1/en/places")

# In-memory photo URL cache: {dest_id -> photo_url}  (survives restart-free for the process)
_photo_cache: dict[str, str] = {}
_CACHE_MAX = 1000

# Throttle: at most 8 concurrent external calls so we don't flood the network
_PHOTO_SEMAPHORE = asyncio.Semaphore(8)

# Fallback images per climate/tag
FALLBACK_IMAGES = {
    "tropical": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800",
    "mediterranean": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800",
    "mountain": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800",
    "cold": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800",
    "arid": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800",
    "highland": "https://images.unsplash.com/photo-1526772662000-3f88f10405ff?w=800",
    "subarctic": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800",
    "temperate": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
    "subtropical": "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800",
    "default": "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800",
}

# Pre-curated high-quality images for top destinations (override)
CURATED_IMAGES = {
    "1":  "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800",   # Bali
    "2":  "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800",   # Patagonia
    "3":  "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800",   # Santorini
    "4":  "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=800",   # Kyoto
    "5":  "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=800",   # Machu Picchu
    "6":  "https://images.unsplash.com/photo-1520769945061-0a448c463865?w=800",   # Reykjavik
    "7":  "https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800",   # Kenya Safari
    "8":  "https://images.unsplash.com/photo-1533587851505-d119e13fa0d7?w=800",   # Amalfi
    "9":  "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?w=800",   # Queenstown
    "10": "https://images.unsplash.com/photo-1489493585363-d69421e0edd3?w=800",   # Marrakech
    "11": "https://images.unsplash.com/photo-1540202404-a2f29016b523?w=800",   # Maldives
    "12": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=800",   # Prague
    "13": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",   # Banff
    "15": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",   # Tokyo
    "16": "https://images.unsplash.com/photo-1548182741-fd3e6e783b87?w=800",   # Petra
    "21": "https://images.unsplash.com/photo-1531210483974-4f8c1f33fd35?w=800",   # Swiss Alps
    "35": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=800",   # Norway Fjords
    "39": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",   # Bhutan
    "62": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=800",   # Cappadocia
    "84": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=800",   # Dolomites
    "95": "https://images.unsplash.com/photo-1472396961693-142e6e269027?w=800",   # Yosemite
}


async def get_destination_photo(dest_id: str, xid: str, climate: str) -> str:
    """
    Returns an image URL for a destination.
    Priority: cache → curated → OpenTripMap API → fallback by climate.
    """
    # 1. Fast path: in-memory cache
    if dest_id in _photo_cache:
        return _photo_cache[dest_id]

    # 2. Curated overrides
    if dest_id in CURATED_IMAGES:
        _photo_cache[dest_id] = CURATED_IMAGES[dest_id]
        return CURATED_IMAGES[dest_id]

    # 3. OpenTripMap API (with semaphore throttle)
    if xid and API_KEY:
        try:
            async with _PHOTO_SEMAPHORE:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(
                        f"{BASE_URL}/xid/{xid}",
                        params={"apikey": API_KEY}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        img = (
                            data.get("preview", {}).get("source") or
                            data.get("image") or
                            ""
                        )
                        if img:
                            url = img
                            # Store in cache (evict oldest if full)
                            if len(_photo_cache) >= _CACHE_MAX:
                                oldest = next(iter(_photo_cache))
                                del _photo_cache[oldest]
                            _photo_cache[dest_id] = url
                            return url
        except Exception:
            pass

    # 4. Climate-based fallback
    fallback = FALLBACK_IMAGES.get(climate, FALLBACK_IMAGES["default"])
    _photo_cache[dest_id] = fallback
    return fallback


async def enrich_destinations_with_photos(destinations: list[dict]) -> list[dict]:
    """Add photo URLs to a list of destination dicts."""
    import asyncio

    async def fetch_one(dest):
        photo = await get_destination_photo(
            dest.get("id", ""),
            dest.get("xid", ""),
            dest.get("climate", "default")
        )
        return {**dest, "photo_url": photo}

    return await asyncio.gather(*[fetch_one(d) for d in destinations])


async def search_nearby_pois(lat: float, lon: float, radius: int = 5000, kinds: str = "interesting_places") -> list[dict]:
    """Fetch nearby points of interest from OpenTripMap."""
    if not API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{BASE_URL}/radius",
                params={
                    "apikey": API_KEY,
                    "radius": radius,
                    "lon": lon,
                    "lat": lat,
                    "kinds": kinds,
                    "limit": 10,
                    "format": "json",
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return []
