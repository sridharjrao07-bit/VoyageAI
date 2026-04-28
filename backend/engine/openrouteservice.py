"""
OpenRouteService Integration
Provides trekking-specific routes and elevation profiles.
API: https://api.openrouteservice.org

Set OPENROUTESERVICE_API_KEY in your .env file.

Endpoints used:
  - /v2/directions/foot-hiking  → trekking route between two coordinates
  - /elevation/line             → elevation profile for a polyline
  - /geocode/search             → convert place names to coordinates
"""
import os
import httpx
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

ORS_KEY  = os.getenv("OPENROUTESERVICE_API_KEY", "")
ORS_BASE = "https://api.openrouteservice.org"
HEADERS  = {
    "Authorization": ORS_KEY,
    "Content-Type":  "application/json",
    "Accept":        "application/json, application/geo+json",
}


async def geocode_place(place_name: str) -> Optional[dict]:
    """Convert a place name to lat/lon using ORS geocoding."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{ORS_BASE}/geocode/search",
                params={"api_key": ORS_KEY, "text": place_name, "size": 1, "lang": "en"},
            )
            if resp.status_code != 200:
                return None
            features = resp.json().get("features", [])
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]  # [lon, lat]
            label  = features[0]["properties"].get("label", place_name)
            return {"lon": coords[0], "lat": coords[1], "label": label}
    except Exception as e:
        print(f"[ORS] Geocode error for '{place_name}': {e}")
        return None


async def get_trekking_route(
    start_lat: float, start_lon: float,
    end_lat: float,   end_lon: float,
    profile: str = "foot-hiking",
) -> dict:
    """
    Get a hiking/trekking route between two coordinates.
    profile: 'foot-hiking' (default) | 'foot-walking' | 'cycling-mountain'

    Returns:
        distance_km, duration_hours, ascent_m, descent_m,
        bbox, geometry (GeoJSON), waypoints summary, instructions
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{ORS_BASE}/v2/directions/{profile}/geojson",
                headers=HEADERS,
                json={
                    "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
                    "elevation": True,
                    "instructions": True,
                    "language": "en",
                    "units": "km",
                    "geometry_simplify": False,
                    "extra_info": ["surface", "steepness", "traildifficulty"],
                },
            )
            if resp.status_code != 200:
                return {"error": f"ORS routing error {resp.status_code}: {resp.text[:200]}"}

            data = resp.json()
            feature = data.get("features", [{}])[0]
            props   = feature.get("properties", {})
            summary = props.get("summary", {})
            segs    = props.get("segments", [{}])
            steps   = segs[0].get("steps", []) if segs else []

            return {
                "profile":       profile,
                "distance_km":   round(summary.get("distance", 0), 2),
                "duration_hrs":  round(summary.get("duration", 0) / 3600, 2),
                "ascent_m":      round(summary.get("ascent", 0), 1),
                "descent_m":     round(summary.get("descent", 0), 1),
                "bbox":          feature.get("bbox"),
                "geometry":      feature.get("geometry"),       # GeoJSON LineString
                "waypoints":     [
                    {
                        "instruction": step.get("instruction", ""),
                        "distance_km": round(step.get("distance", 0), 2),
                        "duration_min": round(step.get("duration", 0) / 60, 1),
                        "name": step.get("name", ""),
                    }
                    for step in steps[:20]  # cap at 20 turn-by-turn steps
                ],
                "error": None,
            }
    except Exception as e:
        print(f"[ORS] Routing error: {e}")
        return {"error": str(e)}


async def get_elevation_profile(coordinates: list[list[float]]) -> dict:
    """
    Get elevation data for a list of [lon, lat] coordinates.
    Returns the same coordinates with an added elevation value: [lon, lat, ele_m].
    Also returns min/max/avg elevation stats.
    """
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{ORS_BASE}/elevation/line",
                headers=HEADERS,
                json={
                    "format_in":  "encodedpolyline" if False else "geojson",
                    "format_out": "geojson",
                    "geometry": {"coordinates": coordinates, "type": "LineString"},
                },
            )
            if resp.status_code != 200:
                return {"error": f"ORS elevation error {resp.status_code}"}

            data   = resp.json()
            pts    = data.get("geometry", {}).get("coordinates", [])
            elevs  = [p[2] for p in pts if len(p) >= 3]

            return {
                "coordinates_with_elevation": pts,
                "elevation_min_m":  round(min(elevs), 1) if elevs else 0,
                "elevation_max_m":  round(max(elevs), 1) if elevs else 0,
                "elevation_avg_m":  round(sum(elevs) / len(elevs), 1) if elevs else 0,
                "total_points":     len(pts),
                "error": None,
            }
    except Exception as e:
        print(f"[ORS] Elevation error: {e}")
        return {"error": str(e)}


async def get_trekking_route_by_name(
    start_place: str,
    end_place: str,
    profile: str = "foot-hiking",
) -> dict:
    """
    Full pipeline: geocode both places → get route → attach elevation profile.
    Returns everything needed to render a trekking map + elevation chart.
    """
    import asyncio
    start, end = await asyncio.gather(
        geocode_place(start_place),
        geocode_place(end_place),
    )

    if not start:
        return {"error": f"Could not geocode start location: '{start_place}'"}
    if not end:
        return {"error": f"Could not geocode end location: '{end_place}'"}

    route = await get_trekking_route(
        start_lat=start["lat"], start_lon=start["lon"],
        end_lat=end["lat"],     end_lon=end["lon"],
        profile=profile,
    )

    if route.get("error"):
        return route

    # Attach elevation profile to the route geometry
    route_coords = route.get("geometry", {}).get("coordinates", [])
    if route_coords:
        # Sample every Nth point to stay under ORS limits (max 2000 pts)
        step = max(1, len(route_coords) // 500)
        sampled = route_coords[::step]
        elev = await get_elevation_profile(sampled)
        route["elevation_profile"] = elev

    route["start"] = start
    route["end"]   = end
    return route
