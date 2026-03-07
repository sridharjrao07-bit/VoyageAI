"""
GeoNames API Integration
Enriches destinations with geographic metadata:
altitude, population, timezone, country code, admin region.
API: http://api.geonames.org/searchJSON
Register at geonames.org for a free username (demo has rate limits).
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "demo")
GEONAMES_BASE = "http://api.geonames.org"


async def search_geoname(query: str, country_code: str = "", max_rows: int = 1) -> dict | None:
    """
    Search GeoNames for a place by name.
    Returns the top match with altitude, population, timezone, lat/lon.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{GEONAMES_BASE}/searchJSON",
                params={
                    "q": query,
                    "maxRows": max_rows,
                    "username": GEONAMES_USERNAME,
                    "country": country_code,
                    "featureClass": "P",  # Populated places
                    "orderby": "relevance",
                },
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            results = data.get("geonames", [])
            return results[0] if results else None
    except Exception as e:
        print(f"[GeoNames] Search error: {e}")
        return None


async def get_elevation(lat: float, lon: float) -> int | None:
    """
    Get elevation in meters for a coordinate using GeoNames SRTM3 data.
    """
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(
                f"{GEONAMES_BASE}/srtm3JSON",
                params={"lat": lat, "lng": lon, "username": GEONAMES_USERNAME},
            )
            if resp.status_code == 200:
                return resp.json().get("srtm3")
    except Exception:
        pass
    return None


async def get_timezone(lat: float, lon: float) -> str | None:
    """Get timezone string for a coordinate."""
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(
                f"{GEONAMES_BASE}/timezoneJSON",
                params={"lat": lat, "lng": lon, "username": GEONAMES_USERNAME},
            )
            if resp.status_code == 200:
                return resp.json().get("timezoneId")
    except Exception:
        pass
    return None


async def enrich_destination_geodata(dest: dict) -> dict:
    """
    Enriches a destination dict with GeoNames data:
    elevation_m, population, timezone, geonames_id.
    """
    name = dest.get("name", "")
    lat = float(dest.get("latitude", 0))
    lon = float(dest.get("longitude", 0))

    # Run in parallel conceptually via sequential calls (keep it simple & within rate limits)
    geo = await search_geoname(name)
    elevation = await get_elevation(lat, lon)
    timezone = await get_timezone(lat, lon)

    enriched = dict(dest)
    if geo:
        enriched["population"] = geo.get("population", 0)
        enriched["geonames_id"] = geo.get("geonameId")
        enriched["admin_region"] = geo.get("adminName1", "")
    if elevation is not None:
        enriched["elevation_m"] = elevation
    if timezone:
        enriched["timezone"] = timezone

    return enriched
