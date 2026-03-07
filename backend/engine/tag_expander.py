"""
Semantic Intent Tag Expander
Maps high-level user intents to specific OSM/OpenTripMap tag synonyms.

When a user asks for "adventure," they may mean: climbing, rafting, remote trails, etc.
This module expands the user's input tags into a richer set before scoring,
so the content-based TF-IDF search understands semantic intent.

Usage:
    from engine.tag_expander import expand_tags
    enriched = expand_tags(["adventure", "budget"])
"""
from __future__ import annotations

# ── Intent → Tag Expansion Map ────────────────────────────────────────────────
# Keys are common user intents. Values are OSM/OpenTripMap-aligned synonyms
# that appear in destination descriptions, tags, and overpass data.
INTENT_MAP: dict[str, list[str]] = {
    "adventure": [
        "climbing", "rafting", "trekking", "remote", "trails",
        "extreme_sports", "bungee", "kayaking", "paragliding", "wilderness",
        "hiking", "mountaineering", "expedition",
    ],
    "peaceful": [
        "serene", "quiet", "remote", "nature", "scenic",
        "rural", "tranquil", "offbeat", "secluded", "lake",
    ],
    "romantic": [
        "scenic", "sunset", "island", "luxury", "coastal",
        "intimate", "historic", "charming", "wine", "views",
    ],
    "budget": [
        "backpacker", "cheap", "affordable", "street_food",
        "hostel", "low_cost", "budget_friendly",
    ],
    "luxury": [
        "premium", "resort", "five_star", "spa", "gourmet",
        "exclusive", "yacht", "villa", "high_end",
    ],
    "cultural": [
        "culture", "history", "temples", "ancient", "heritage",
        "art", "museum", "festival", "indigenous", "architecture",
    ],
    "nature": [
        "wildlife", "forest", "national_park", "eco_tourism",
        "waterfall", "biodiversity", "jungle", "mountains",
    ],
    "beach": [
        "coastal", "snorkeling", "diving", "island", "tropical",
        "lagoon", "coral", "surf", "sand", "ocean",
    ],
    "food": [
        "cuisine", "street_food", "gastronomy", "market",
        "cooking", "wine", "local_food", "seafood",
    ],
    "spiritual": [
        "spirituality", "meditation", "monastery", "pilgrimage",
        "temples", "yoga", "zen", "ashram",
    ],
    "photography": [
        "scenic", "colorful", "unique", "viewpoint",
        "landscape", "wildlife", "architecture", "sunrise",
    ],
    "wellness": [
        "spa", "yoga", "meditation", "retreat", "thermal",
        "hot_springs", "detox", "mindfulness",
    ],
    "hiking": [
        "trails", "trekking", "mountains", "national_park",
        "wilderness", "remote", "summit", "ridge",
    ],
    "wildlife": [
        "safari", "nature", "photography", "national_park",
        "birds", "mammals", "marine", "endemic",
    ],
    "history": [
        "ancient", "ruins", "archaeology", "heritage",
        "colonial", "monuments", "UNESCO", "medieval",
    ],
}


def expand_tags(tags: list[str]) -> list[str]:
    """
    Given a list of user intent tags, return an enriched list that includes
    semantic synonyms. Original tags are always preserved.

    Example:
        expand_tags(["adventure", "budget"])
        → ["adventure", "budget", "climbing", "rafting", "trekking", ...]
    """
    expanded = list(tags)  # always keep originals
    seen = set(t.lower() for t in tags)

    for tag in tags:
        synonyms = INTENT_MAP.get(tag.lower(), [])
        for syn in synonyms:
            if syn.lower() not in seen:
                expanded.append(syn)
                seen.add(syn.lower())

    return expanded
