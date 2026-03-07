"""
Smart Trekking Safety Assistant — Powered by Grok AI + OpenWeatherMap
Equivalent of the Gemini-based safety assessment, re-implemented with xAI Grok.

Run standalone:
    python trekking_safety.py
Or import: from trekking_safety import get_ai_safety_assessment
"""
import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY    = os.getenv("GROK_API_KEY", "")
WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
GROK_BASE_URL   = "https://api.x.ai/v1"
GROK_MODEL      = "grok-2"


def get_ai_safety_assessment(city_name: str) -> str:
    """
    Synchronous version — mirrors the original Gemini implementation exactly.
    Fetches live weather for the city and returns a Grok AI safety warning.
    """
    # ── STEP 1: Fetch Live Weather from OpenWeatherMap ──────────────────────
    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city_name}&appid={WEATHER_API_KEY}&units=metric"
    )
    resp = httpx.get(weather_url, timeout=10.0)
    resp.raise_for_status()
    weather_data = resp.json()

    temp       = weather_data["main"]["temp"]
    wind_speed = weather_data["wind"]["speed"]
    condition  = weather_data["weather"][0]["description"]

    # ── STEP 2: Feed data into Grok (the Agentic Logic) ─────────────────────
    prompt = f"""Act as a Smart Trekking Safety Assistant for an Incident Response System.
Current conditions in {city_name}:
- Temperature: {temp}°C
- Wind Speed: {wind_speed} m/s
- Weather: {condition}

Task: Provide a 2-sentence safety warning for a trekker.
If conditions are dangerous (high wind or extreme cold), advise them to seek the nearest shelter."""

    grok_resp = httpx.post(
        f"{GROK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.6,
        },
        timeout=20.0,
    )
    grok_resp.raise_for_status()
    return grok_resp.json()["choices"][0]["message"]["content"]


async def get_ai_safety_assessment_async(city_name: str) -> dict:
    """
    Async version for use inside FastAPI endpoints.
    Returns a dict with 'safety_warning', raw weather data, and city.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        wr = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city_name, "appid": WEATHER_API_KEY, "units": "metric"},
        )
        wr.raise_for_status()
        w = wr.json()

    temp       = w["main"]["temp"]
    wind_speed = w["wind"]["speed"]
    condition  = w["weather"][0]["description"]
    feels_like = w["main"]["feels_like"]
    humidity   = w["main"]["humidity"]

    prompt = f"""Act as a Smart Trekking Safety Assistant for an Incident Response System.
Current conditions in {city_name}:
- Temperature: {temp}°C (feels like {feels_like}°C)
- Wind Speed: {wind_speed} m/s
- Humidity: {humidity}%
- Weather: {condition}

Task: Provide a 2-sentence safety warning for a trekker.
If conditions are dangerous (high wind >10 m/s or extreme cold <0°C or storm conditions), 
advise them to seek the nearest shelter and give a specific reason why."""

    async with httpx.AsyncClient(timeout=20.0) as client:
        gr = await client.post(
            f"{GROK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.6,
            },
        )
        gr.raise_for_status()

    safety_warning = gr.json()["choices"][0]["message"]["content"]

    # Compute a simple danger level
    danger_level = "LOW"
    if wind_speed > 15 or temp < -5:
        danger_level = "HIGH"
    elif wind_speed > 10 or temp < 5 or "storm" in condition or "snow" in condition:
        danger_level = "MEDIUM"

    return {
        "city": city_name,
        "weather": {
            "temp_c": temp,
            "feels_like_c": feels_like,
            "wind_mps": wind_speed,
            "humidity_pct": humidity,
            "condition": condition,
        },
        "danger_level": danger_level,
        "safety_warning": safety_warning,
    }


if __name__ == "__main__":
    import sys
    city = sys.argv[1] if len(sys.argv) > 1 else "Manali"
    print(f"\n🏔️  Trekking Safety Assessment for: {city}\n{'─' * 50}")
    
    try:
        warning = get_ai_safety_assessment(city)
        print(f"\n⚠️  SAFETY WARNING:\n{warning}\n")
    except httpx.HTTPStatusError as e:
        print(f"❌ API Error: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
