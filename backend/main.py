"""
AI Smart Tourism Recommendation System — FastAPI Backend
Endpoints:
  GET  /health
  GET  /destinations
  GET  /destinations/{dest_id}/pois
  POST /recommend
  POST /feedback
  GET  /performance
  GET  /users/{user_id}
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

# --- Startup / Shutdown ---
from engine import data_loader
from engine.hybrid import recommend as hybrid_recommend
from engine.metrics import compute_full_metrics
from engine.opentripmap import enrich_destinations_with_photos, search_nearby_pois
from engine.overpass import get_all_outdoor_features, get_hiking_trails
from engine.wikidata import rag_enrich_xai
from engine.weather import get_destination_weather
from engine.chatbot import chat_completion, build_travel_context
from engine.history import record_seen, get_seen, clear_seen, all_history
from engine.semantic_search import semantic_search
from engine.data_loader import get_sanitization_report
from engine.db import (
    init_db, get_user_history, add_to_history,
    save_like, unlike, is_liked, get_liked_categories, get_liked_destination_ids,
    get_social_context,
)
from engine.llm_agent import generate_agent_recommendations
from engine.tag_expander import expand_tags
from engine.cache import recommendation_cache
from engine.flights import get_flight_data, get_mock_reviews

# In-memory feedback store: { session_id: { dest_id: delta } }
_feedback_store: dict[str, dict[str, float]] = {}

# Cached metrics (recomputed lazily)
_cached_metrics: dict = {}

# Performance log: list of {path, method, status, duration_ms}
_perf_log: list[dict] = []
PERF_WARN_MS = 500   # warn if request exceeds this threshold


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all data on startup and init db."""
    data_loader.load_data()
    init_db()
    yield


app = FastAPI(
    title="AI Smart Tourism Recommendation API",
    version="1.0.0",
    description="Hybrid AI recommendation engine: Content-Based + Collaborative + Popularity with XAI.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def performance_timing_middleware(request, call_next):
    """
    Logs method, path, status code, and duration for every request.
    Flags requests over 500ms as [SLOW] in the server console.
    Stores results in _perf_log for the /performance/timing endpoint.
    """
    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - t0) * 1000, 1)

    entry = {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    }
    _perf_log.append(entry)
    if len(_perf_log) > 500:      # keep last 500 entries
        _perf_log.pop(0)

    tag = "[SLOW] " if duration_ms > PERF_WARN_MS else ""
    print(f"[Perf] {tag}{request.method} {request.url.path} "
          f"-> {response.status_code}  {duration_ms}ms")

    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response

@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": traceback.format_exc()})


# ────────────────────────────────────────────
# Request / Response models
# ────────────────────────────────────────────

class RecommendRequest(BaseModel):
    user_id: str = Field(default="new_user", description="Existing user ID or 'new_user' for cold-start")
    tags: list[str] = Field(default=[], description="User preference tags e.g. ['adventure','mountain']")
    budget_usd: float = Field(default=0, ge=0, description="Max budget in USD (0 = no limit)")
    accessibility_required: bool = Field(default=False)
    top_n: int = Field(default=10, ge=1, le=30)
    session_id: Optional[str] = Field(default=None, description="Session ID for feedback tracking")
    origin: str = Field(default="DEL", description="Origin IATA for flights")
    include_flights: bool = Field(default=False, description="Include flight prices")
    currency_preference: str = Field(default="INR", description="Preferred display currency")
    travel_style: Optional[str] = Field(default=None)
    include_photos: bool = Field(default=True)
    seen_ids: list[str] = Field(
        default=[],
        description="Destination IDs the user has already been shown. These are excluded from results."
    )
    weather_aware: bool = Field(
        default=False,
        description="If True, down-ranks destinations with active severe weather alerts (adds latency)."
    )
    surprise_mode: bool = Field(
        default=False,
        description="Ignore content-based filter, return 100% novelty hidden-gem picks."
    )
    liked_categories: list[str] = Field(
        default=[],
        description="List of category tags the user has liked (RL bias input). Loaded from /likes/{user_id}."
    )


class FeedbackRequest(BaseModel):
    session_id: str
    destination_id: str
    vote: int = Field(..., description="1 = thumbs up, -1 = thumbs down")


class FeedbackResponse(BaseModel):
    status: str
    session_id: str
    message: str


class LikeRequest(BaseModel):
    user_id: str
    destination_id: str


class ChatMessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageItem]
    destination: Optional[str] = None
    user_profile: Optional[dict] = None


# ────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/destinations", tags=["Destinations"])
async def get_destinations(
    continent: Optional[str] = None,
    climate: Optional[str] = None,
    max_cost: Optional[float] = None,
    tag: Optional[str] = None,
    include_photos: bool = False,
):
    """Return all destinations with optional filters."""
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    filtered = df.copy()
    if continent:
        filtered = filtered[filtered["continent"].str.lower() == continent.lower()]
    if climate:
        filtered = filtered[filtered["climate"].str.lower() == climate.lower()]
    if max_cost:
        filtered = filtered[filtered["avg_cost_usd"] <= max_cost]
    if tag:
        filtered = filtered[filtered["tags"].str.contains(tag, case=False, na=False)]

    records = filtered.to_dict(orient="records")

    if include_photos:
        records = await enrich_destinations_with_photos(records)

    return {"total": len(records), "destinations": records}


@app.get("/destinations/{dest_id}", tags=["Destinations"])
async def get_destination(dest_id: str, include_pois: bool = False):
    """Get a single destination by ID, optionally with nearby POIs from OpenTripMap."""
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    match = df[df["id"].astype(str) == dest_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Destination not found")

    dest = match.iloc[0].to_dict()

    # Enrich with photo
    enriched = await enrich_destinations_with_photos([dest])
    dest = enriched[0]

    if include_pois:
        pois = await search_nearby_pois(
            lat=float(dest.get("latitude", 0)),
            lon=float(dest.get("longitude", 0)),
            radius=10000,
        )
        dest["nearby_pois"] = pois[:8]

    return dest


@app.post("/recommend", tags=["Recommendations"])
async def recommend(req: RecommendRequest):
    """
    Core Agentic recommendation endpoint.
    Uses SQLite memory and Grok LLM to ensure diversity and novelty.
    """
    # Create or reuse session
    session_id = req.session_id or str(uuid.uuid4())

    # Merge travel style into tags
    tags = list(req.tags)
    if req.travel_style:
        tags.append(req.travel_style)

    # 1. Fetch History from SQLite
    history_ids = get_user_history(req.user_id, limit=20)
    combined_seen = list(dict.fromkeys(req.seen_ids + history_ids)) # deduplicate

    # 2. Semantic Intent Expansion
    expanded_tags = expand_tags(tags)

    # 3. Get candidates from the dataframe to reduce context size for LLM
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
        
    # Quick filter for budget and accessibility
    filtered = df.copy()
    if req.budget_usd > 0:
        if req.include_flights:
            # Assume a safe buffer of $800 for average international flights
            max_ground = max(0, (req.budget_usd * 1.3) - 800)
            filtered = filtered[filtered["avg_cost_usd"] <= max_ground]
        else:
            filtered = filtered[filtered["avg_cost_usd"] <= req.budget_usd * 1.3]
    if req.accessibility_required:
        filtered = filtered[filtered["accessibility"].astype(str).str.lower().isin(["true", "1", "yes"])]
        
    # Exclude seen
    filtered = filtered[~filtered["id"].astype(str).isin(combined_seen)]
    
    # We send ~30 best semantic candidates to the agent
    # By finding top matches via content-based or hybrid, or just sending a random sample
    # Here we'll use a basic score or simply grab the first 30 suitable
    # Let's use the hybrid recommender to get top 30 candidates to pass to LLM
    feedback_overrides = _feedback_store.get(session_id, {})
    
    candidates = hybrid_recommend(
        user_id=req.user_id,
        tags=tags,
        budget_usd=req.budget_usd,
        accessibility_required=req.accessibility_required,
        top_n=30,
        feedback_overrides=feedback_overrides,
        seen_ids=combined_seen,
        weather_aware=req.weather_aware,
        surprise_mode=req.surprise_mode,
    )
    
    # If no candidates, cold start or exhausted
    if not candidates:
        return {
            "session_id": session_id,
            "total": 0,
            "is_cold_start": True,
            "recommendations": [],
        }

    is_cold_start = candidates[0].get("is_cold_start", False)

    # Convert candidates to a compact dict for the LLM
    import asyncio as _aio
    
    async def _enrich_candidate(c):
        dest_dict = {
            "id": c["id"],
            "name": c["name"],
            "country": c["country"],
            "tags": c["tags"],
            "description": c.get("description", ""),
            "weather_alert": "true" if c.get("weather_flagged") else "false",
            "avg_cost_usd": c.get("avg_cost_usd", 0)
        }
        dest_iata = c["name"][:3].upper()
        dest_dict["flight_data"] = await get_flight_data(req.origin, dest_iata)
        dest_dict["destination_reviews"] = get_mock_reviews(c["name"])
        dest_dict["user_comments"] = get_social_context(str(c["id"]))
        return dest_dict
        
    raw_data_for_llm_tuples = await _aio.gather(*[_enrich_candidate(c) for c in candidates])
    raw_data_for_llm = list(raw_data_for_llm_tuples)

    # 4. Let the Agent "Think" (with cache)
    user_profile = {"budget_usd": req.budget_usd} if req.budget_usd > 0 else {}

    # Merge liked_categories from request payload + freshly fetched from DB
    db_liked_cats = get_liked_categories(req.user_id)
    all_liked_cats = list(req.liked_categories) + db_liked_cats

    # Build cache key — skip cache for surprise_mode (always want fresh picks)
    cache_key = recommendation_cache.make_key(
        tags=tags, budget_usd=req.budget_usd,
        weather_aware=req.weather_aware, surprise_mode=req.surprise_mode,
        include_flights=req.include_flights, currency_preference=req.currency_preference
    )
    ai_response_list = None if req.surprise_mode else recommendation_cache.get(cache_key)

    if ai_response_list is None:
        ai_response_list = await generate_agent_recommendations(
            user_tags=expanded_tags,
            history_ids=combined_seen,
            raw_data=raw_data_for_llm,
            user_profile=user_profile,
            liked_categories=all_liked_cats,
            surprise_mode=req.surprise_mode,
            include_flights=req.include_flights,
            currency_preference=req.currency_preference
        )
        if ai_response_list and not req.surprise_mode:
            recommendation_cache.set(cache_key, ai_response_list)
    else:
        print(f"[Cache] HIT for key {cache_key[:8]}…")
    
    # Map AI selections back to full destination objects
    final_results = []
    candidates_by_id = {str(c["id"]): c for c in candidates}
    
    # The AI returns [{id, reasoning, pivot_applied, pivot_reason}, ...]
    for pick in ai_response_list:
        pid = str(pick.get("id"))
        reasoning = pick.get("reasoning", "A fantastic choice matching your preferences.")

        if pid in candidates_by_id:
            dest = candidates_by_id[pid]
            dest["xai_snippet"] = reasoning
            dest["pivot_applied"] = bool(pick.get("pivot_applied", False))
            dest["pivot_reason"] = pick.get("pivot_reason", "")
            dest["is_surprise"] = req.surprise_mode
            final_results.append(dest)

    # Fallback if Agent failed to return valid picks
    if not final_results:
        final_results = candidates[:5]

    # Limit to top 5
    final_results = final_results[:5]

    # ── RAG: Enrich XAI snippets with Wikidata facts (async, concurrent) ──
    import asyncio as _aio
    async def _enrich_xai(item):
        item["xai_snippet"] = await rag_enrich_xai(
            dest_id=item["id"],
            dest_name=item["name"],
            base_xai=item.get("xai_snippet", ""),
        )
        return item
    final_results = await _aio.gather(*[_enrich_xai(r) for r in final_results])
    final_results = list(final_results)

    # ── Enrich with photos (OpenTripMap + curated) ──
    if req.include_photos:
        final_results = await enrich_destinations_with_photos(final_results)

    # 5. Log the new recommendations back to SQLite history
    shown_ids = [str(r["id"]) for r in final_results]
    add_to_history(req.user_id, shown_ids)

    return {
        "session_id": session_id,
        "total": len(final_results),
        "is_cold_start": is_cold_start,
        "user_id": req.user_id,
        "surprise_mode": req.surprise_mode,
        "novelty_count": sum(1 for r in final_results if r.get("is_novelty")),
        "discovery_count": sum(1 for r in final_results if r.get("is_discovery")),
        "weather_flagged_count": sum(1 for r in final_results if r.get("weather_flagged")),
        "pivot_count": sum(1 for r in final_results if r.get("pivot_applied")),
        "cache_stats": recommendation_cache.stats(),
        "recommendations": final_results,
    }


@app.get("/destinations/{dest_id}/outdoor", tags=["Destinations"])
async def get_outdoor_features(dest_id: str, radius_m: int = 15000):
    """Fetch hiking trails, peaks, viewpoints & campsites near destination (Overpass API)."""
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    match = df[df["id"].astype(str) == dest_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Destination not found")
    row = match.iloc[0]
    features = await get_all_outdoor_features(
        lat=float(row["latitude"]),
        lon=float(row["longitude"]),
        radius_m=radius_m,
    )
    return {"destination_id": dest_id, "destination_name": row["name"], **features}


@app.get("/destinations/{dest_id}/weather", tags=["Destinations"])
async def get_weather(dest_id: str):
    """Real-time weather + 5-day forecast for a destination (OpenWeatherMap)."""
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    match = df[df["id"].astype(str) == dest_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Destination not found")
    row = match.iloc[0]
    weather = await get_destination_weather(
        lat=float(row["latitude"]),
        lon=float(row["longitude"]),
    )
    return {
        "destination_id": dest_id,
        "destination_name": row["name"],
        **weather,
    }


@app.post("/feedback", response_model=FeedbackResponse, tags=["Recommendations"])
async def submit_feedback(req: FeedbackRequest):
    """
    Accept thumbs up (+1) or thumbs down (-1) for a destination.
    Adjusts score weight for the session's next recommendation call.
    """
    if req.vote not in (1, -1):
        raise HTTPException(status_code=400, detail="vote must be 1 or -1")

    if req.session_id not in _feedback_store:
        _feedback_store[req.session_id] = {}

    # Each vote shifts the score by ±0.15 (accumulative)
    current = _feedback_store[req.session_id].get(req.destination_id, 0.0)
    _feedback_store[req.session_id][req.destination_id] = current + (req.vote * 0.15)

    action = "boosted 👍" if req.vote == 1 else "suppressed 👎"
    return FeedbackResponse(
        status="ok",
        session_id=req.session_id,
        message=f"Destination {req.destination_id} {action}. Re-fetch /recommend to see updated results.",
    )


# ────────────────────────────────────────────
# Feedback Loop (RL) — Likes / Bucket List
# ────────────────────────────────────────────

@app.post("/likes", tags=["Feedback Loop"])
async def like_destination(req: LikeRequest):
    """
    Save a destination to the user's Bucket List.
    Persists in SQLite and feeds category data back to the LLM agent for RL bias.
    Supports toggle: calling again on an already-liked destination removes the like.
    """
    df = data_loader.get_destinations()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    match = df[df["id"].astype(str) == str(req.destination_id)]
    if match.empty:
        raise HTTPException(status_code=404, detail="Destination not found")

    row = match.iloc[0]
    categories = [t.strip() for t in str(row.get("tags", "")).split(",") if t.strip()]

    already_liked = is_liked(req.user_id, req.destination_id)
    if already_liked:
        unlike(req.user_id, req.destination_id)
        return {"status": "unliked", "user_id": req.user_id, "destination_id": req.destination_id, "liked": False}
    else:
        save_like(req.user_id, req.destination_id, categories)
        return {
            "status": "liked",
            "user_id": req.user_id,
            "destination_id": req.destination_id,
            "liked": True,
            "categories_saved": categories,
        }


@app.get("/likes/{user_id}", tags=["Feedback Loop"])
async def get_user_likes(user_id: str):
    """
    Return the user's liked destinations and their top liked categories.
    Pass `liked_categories` from this response into the /recommend payload
    to activate the Reinforcement Learning preference bias.
    """
    liked_ids = get_liked_destination_ids(user_id)
    liked_cats = get_liked_categories(user_id)

    from collections import Counter
    cat_counts = Counter(liked_cats).most_common(10)

    return {
        "user_id": user_id,
        "total_likes": len(liked_ids),
        "liked_destination_ids": liked_ids,
        "liked_categories": liked_cats,
        "top_categories": [cat for cat, _ in cat_counts],
    }


@app.get("/performance", tags=["Analytics"])
async def get_performance():
    """
    Returns Precision@10, Recall@10, MAP, and A/B test comparison.
    Cached after first computation.
    """
    global _cached_metrics
    if not _cached_metrics:
        _cached_metrics = compute_full_metrics()
    return _cached_metrics


@app.get("/users/{user_id}", tags=["Users"])
async def get_user(user_id: str):
    """Return user profile by ID."""
    user = data_loader.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@app.get("/users", tags=["Users"])
async def list_users():
    """List all user IDs and names."""
    df = data_loader.get_users()
    if df is None:
        return []
    return df[["user_id", "name", "travel_style", "budget_bracket"]].to_dict(orient="records")


# ────────────────────────────────────────────
# Semantic Search
# ────────────────────────────────────────────

@app.get("/search", tags=["Semantic Search"])
async def semantic_search_endpoint(
    q: str,
    top_n: int = 10,
):
    """
    Natural-language semantic search over all destinations.
    Uses sentence-transformer embeddings to match meaning, not just keywords.
    Example: 'peaceful hills' returns 'serene', 'remote', 'nature' destinations.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query 'q' must not be empty")
    results = semantic_search(q, top_n=min(top_n, 30))
    if not results:
        return {
            "query": q,
            "total": 0,
            "note": "Semantic search model not available. Install sentence-transformers.",
            "results": [],
        }
    return {"query": q, "total": len(results), "results": results}


# ────────────────────────────────────────────
# Anti-Repetition History
# ────────────────────────────────────────────

class SeenRequest(BaseModel):
    user_id: str
    dest_ids: list[str] = Field(..., description="Destination IDs to mark as seen")


@app.post("/history/seen", tags=["Anti-Repetition"])
async def log_seen(req: SeenRequest):
    """
    Manually record destinations as 'seen' for a user.
    Use this when the user views a destination detail page.
    """
    record_seen(req.user_id, req.dest_ids)
    return {
        "status": "ok",
        "user_id": req.user_id,
        "recorded": req.dest_ids,
        "total_seen": len(get_seen(req.user_id)),
    }


@app.get("/history/seen/{user_id}", tags=["Anti-Repetition"])
async def get_seen_history(user_id: str):
    """Return the list of destination IDs recently shown to this user."""
    return {"user_id": user_id, "seen_ids": get_seen(user_id)}


@app.delete("/history/seen/{user_id}", tags=["Anti-Repetition"])
async def clear_seen_history(user_id: str):
    """Clear the view history for a user (e.g., start a fresh discovery session)."""
    clear_seen(user_id)
    return {"status": "cleared", "user_id": user_id}


# ────────────────────────────────────────────
# Data Sanitization Admin
# ────────────────────────────────────────────

@app.get("/admin/sanitize", tags=["Admin"])
async def run_sanitize():
    """
    Re-run the data sanitizer on the live in-memory DataFrames
    and return a detailed report of what was (or would be) removed.
    Also returns the report from the last startup sanitization.
    """
    from engine.sanitizer import sanitize_dataframes
    df = data_loader.get_destinations()
    ratings = data_loader.get_ratings()
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    _, _, live_report = sanitize_dataframes(df, ratings, max_age_days=30)
    startup_report = get_sanitization_report()

    return {
        "startup_sanitization": startup_report,
        "live_check": live_report,
        "note": "live_check runs on already-sanitized data, so counts should be 0.",
    }


@app.post("/chat", tags=["AI Concierge"])
async def chat(req: ChatRequest):
    """
    Grok AI Travel Concierge chat endpoint.
    Accepts conversation history and optional user profile/destination context.
    Returns personalized travel advice powered by xAI Grok.
    """
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    if req.user_profile or req.destination:
        context = build_travel_context(
            user_profile=req.user_profile,
            destination=req.destination,
        )
        if context and messages:
            messages[0]["content"] = f"{context}\n\n{messages[0]['content']}"

    result = await chat_completion(messages)
    return {
        "reply": result.get("content", ""),
        "model": result.get("model", "grok-2-latest"),
        "tokens_used": result.get("tokens_used", 0),
        "error": result.get("error"),
    }


@app.get("/trekking-safety", tags=["AI Concierge"])
async def trekking_safety(city: str = "Manali"):
    """
    Smart Trekking Safety Assessment.
    Fetches live weather from OpenWeatherMap and generates a Grok AI safety warning.
    Returns: weather conditions, danger level (LOW/MEDIUM/HIGH), and 2-sentence AI safety warning.
    """
    from trekking_safety import get_ai_safety_assessment_async
    try:
        result = await get_ai_safety_assessment_async(city)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Safety assessment failed: {str(e)}")


@app.get("/trekking-route", tags=["Trekking"])
async def get_trekking_route(
    start: str,
    end: str,
    profile: str = "foot-hiking",
):
    """
    Get a trekking route between two places using OpenRouteService.
    - start: place name or 'lat,lon'
    - end: place name or 'lat,lon'
    - profile: foot-hiking (default) | foot-walking | cycling-mountain

    Returns: distance_km, duration_hrs, ascent_m, descent_m,
             GeoJSON geometry, turn-by-turn waypoints, elevation profile.
    """
    from engine.openrouteservice import get_trekking_route_by_name, get_trekking_route as get_route_coords

    # Support both "place name" and "lat,lon" formats
    def parse_coord(s: str):
        parts = s.split(",")
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except ValueError:
                pass
        return None

    start_coord = parse_coord(start)
    end_coord   = parse_coord(end)

    try:
        if start_coord and end_coord:
            result = await get_route_coords(
                start_lat=start_coord[0], start_lon=start_coord[1],
                end_lat=end_coord[0],   end_lon=end_coord[1],
                profile=profile,
            )
        else:
            result = await get_trekking_route_by_name(start, end, profile)

        if result.get("error"):
            raise HTTPException(status_code=502, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Route calculation failed: {str(e)}")


@app.get("/geocode", tags=["Trekking"])
async def geocode(place: str):
    """Convert a place name to coordinates using OpenRouteService geocoding."""
    from engine.openrouteservice import geocode_place
    result = await geocode_place(place)
    if not result:
        raise HTTPException(status_code=404, detail=f"Could not geocode '{place}'")
    return result


@app.get("/performance/timing", tags=["System"])
async def get_performance_timing():
    """
    Performance analysis report for all API requests since server start.
    Goal: < 500ms for the full Clean → Search → AI Suggest cycle.
    """
    import statistics

    if not _perf_log:
        return {"message": "No requests logged yet. Make some API calls first."}

    durations = [e["duration_ms"] for e in _perf_log]
    slow = [e for e in _perf_log if e["duration_ms"] > PERF_WARN_MS]

    # Per-endpoint breakdown
    by_path: dict[str, list[float]] = {}
    for e in _perf_log:
        key = f"{e['method']} {e['path']}"
        by_path.setdefault(key, []).append(e["duration_ms"])

    endpoint_stats = sorted(
        [
            {
                "endpoint": path,
                "calls": len(times),
                "avg_ms": round(statistics.mean(times), 1),
                "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 1),
                "max_ms": round(max(times), 1),
                "slow_count": sum(1 for t in times if t > PERF_WARN_MS),
            }
            for path, times in by_path.items()
        ],
        key=lambda x: -x["avg_ms"],
    )

    sorted_dur = sorted(durations)
    return {
        "target_ms": PERF_WARN_MS,
        "total_requests": len(_perf_log),
        "slow_requests_above_500ms": len(slow),
        "pct_within_target": round(
            (len(_perf_log) - len(slow)) / len(_perf_log) * 100, 1
        ),
        "cache_stats": recommendation_cache.stats(),
        "global": {
            "avg_ms":  round(statistics.mean(durations), 1),
            "median_ms": round(statistics.median(durations), 1),
            "p95_ms":  round(sorted_dur[int(len(sorted_dur) * 0.95)], 1),
            "p99_ms":  round(sorted_dur[int(len(sorted_dur) * 0.99)], 1),
            "max_ms":  round(max(durations), 1),
            "min_ms":  round(min(durations), 1),
        },
        "by_endpoint": endpoint_stats,
        "slowest_10_requests": sorted(
            [{"endpoint": f"{e['method']} {e['path']}", "duration_ms": e["duration_ms"]}
             for e in slow],
            key=lambda x: -x["duration_ms"]
        )[:10],
    }
