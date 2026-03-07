"""
Overpass API Integration
Fetches real hiking trails, trekking paths, and outdoor POIs from OpenStreetMap.
API: https://overpass-api.de/api/interpreter
No key required — free & open data.
"""
import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Trail type tags from OSM
TRAIL_KINDS = {
    "hiking": 'way["highway"="path"]["sac_scale"]',
    "trekking": 'way["highway"="track"]["tracktype"]',
    "nature_walk": 'way["highway"="footway"]["foot"="yes"]',
    "mtb": 'way["highway"="path"]["mtb:scale"]',
}


def _build_trail_query(lat: float, lon: float, radius_m: int, trail_type: str) -> str:
    """Build an Overpass QL query for trails near a coordinate."""
    selector = TRAIL_KINDS.get(trail_type, TRAIL_KINDS["hiking"])
    return f"""
    [out:json][timeout:15];
    (
      {selector}(around:{radius_m},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """


async def get_hiking_trails(
    lat: float,
    lon: float,
    radius_m: int = 15000,
    trail_type: str = "hiking",
    max_results: int = 10,
) -> list[dict]:
    """
    Returns a list of hiking/trekking trails near the given coordinates.
    Each item has: name, difficulty (sac_scale), length_km (approx), osm_id.
    """
    query = _build_trail_query(lat, lon, radius_m, trail_type)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            if resp.status_code != 200:
                return []

            data = resp.json()
            elements = data.get("elements", [])

            trails = []
            seen_ids = set()

            for el in elements:
                if el.get("type") != "way":
                    continue
                if el["id"] in seen_ids:
                    continue
                seen_ids.add(el["id"])

                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("name:en") or "Unnamed Trail"

                trail = {
                    "osm_id": el["id"],
                    "name": name,
                    "trail_type": trail_type,
                    "difficulty": tags.get("sac_scale") or tags.get("tracktype") or "Unknown",
                    "surface": tags.get("surface", "natural"),
                    "description": tags.get("description") or tags.get("note", ""),
                    "website": tags.get("website") or tags.get("url", ""),
                    "osm_url": f"https://www.openstreetmap.org/way/{el['id']}",
                }
                trails.append(trail)

                if len(trails) >= max_results:
                    break

            return trails

    except Exception as e:
        print(f"[Overpass] Error fetching trails: {e}")
        return []


async def get_all_outdoor_features(lat: float, lon: float, radius_m: int = 10000) -> dict:
    """
    Returns a combined dict of outdoor features near the destination:
    - hiking trails
    - nature reserves
    - viewpoints
    - campsites
    """
    viewpoint_query = f"""
    [out:json][timeout:10];
    (
      node["tourism"="viewpoint"](around:{radius_m},{lat},{lon});
      node["natural"="peak"](around:{radius_m},{lat},{lon});
      node["tourism"="camp_site"](around:{radius_m},{lat},{lon});
      node["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});
    );
    out body;
    """

    features = {
        "hiking_trails": [],
        "viewpoints": [],
        "peaks": [],
        "camp_sites": [],
        "nature_reserves": [],
    }

    # Fetch hiking trails
    features["hiking_trails"] = await get_hiking_trails(lat, lon, radius_m)

    # Fetch viewpoints, peaks, campsites
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": viewpoint_query})
            if resp.status_code == 200:
                data = resp.json()
                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en") or "Unnamed"
                    tourism = tags.get("tourism", "")
                    natural = tags.get("natural", "")

                    item = {
                        "osm_id": el.get("id"),
                        "name": name,
                        "lat": el.get("lat"),
                        "lon": el.get("lon"),
                        "elevation": tags.get("ele", ""),
                        "description": tags.get("description", ""),
                    }

                    if tourism == "viewpoint":
                        features["viewpoints"].append(item)
                    elif natural == "peak":
                        features["peaks"].append(item)
                    elif tourism == "camp_site":
                        features["camp_sites"].append(item)
                    elif tags.get("leisure") == "nature_reserve":
                        features["nature_reserves"].append(item)

                # Trim to reasonable sizes
                for key in features:
                    features[key] = features[key][:8]

    except Exception as e:
        print(f"[Overpass] Error fetching outdoor features: {e}")

    return features
