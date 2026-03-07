"""
OpenWeatherMap API Integration
Provides real-time and forecast weather data for destinations.
API: https://api.openweathermap.org/data/2.5/
API: https://api.openweathermap.org/data/2.5/
"""
import os
import httpx
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

OWM_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
OWM_BASE = "https://api.openweathermap.org/data/2.5"

# Weather icon URL helper
def icon_url(icon_code: str) -> str:
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


async def get_current_weather(lat: float, lon: float) -> Optional[dict]:
    """
    Fetch current weather for a lat/lon coordinate.
    Returns: temp_c, feels_like_c, humidity, wind_kph, description, icon_url, uv risk.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{OWM_BASE}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OWM_KEY,
                    "units": "metric",
                },
            )
            if resp.status_code != 200:
                return None

            d = resp.json()
            main = d.get("main", {})
            weather = d.get("weather", [{}])[0]
            wind = d.get("wind", {})

            return {
                "temp_c": round(main.get("temp", 0), 1),
                "feels_like_c": round(main.get("feels_like", 0), 1),
                "humidity_pct": main.get("humidity", 0),
                "wind_kph": round(wind.get("speed", 0) * 3.6, 1),
                "description": weather.get("description", "").capitalize(),
                "icon": weather.get("icon", "01d"),
                "icon_url": icon_url(weather.get("icon", "01d")),
                "visibility_km": round(d.get("visibility", 0) / 1000, 1),
                "city_name": d.get("name", ""),
            }
    except Exception as e:
        print(f"[OWM] Current weather error: {e}")
        return None


async def get_5day_forecast(lat: float, lon: float) -> list[dict]:
    """
    Fetch 5-day / 3-hour forecast.
    Returns one entry per day (noon snapshot): date, temp_c, description, icon_url.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{OWM_BASE}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OWM_KEY,
                    "units": "metric",
                    "cnt": 40,
                },
            )
            if resp.status_code != 200:
                return []

            items = resp.json().get("list", [])
            # Pick one entry per unique date (closest to noon)
            seen_dates = {}
            for item in items:
                dt_txt = item.get("dt_txt", "")
                date = dt_txt[:10]
                time = dt_txt[11:13]
                if date not in seen_dates or abs(int(time) - 12) < abs(int(seen_dates[date]["_hr"]) - 12):
                    seen_dates[date] = {
                        "date": date,
                        "temp_c": round(item["main"]["temp"], 1),
                        "temp_min_c": round(item["main"]["temp_min"], 1),
                        "temp_max_c": round(item["main"]["temp_max"], 1),
                        "description": item["weather"][0]["description"].capitalize(),
                        "icon_url": icon_url(item["weather"][0]["icon"]),
                        "humidity_pct": item["main"]["humidity"],
                        "_hr": time,
                    }

            return [
                {k: v for k, v in day.items() if not k.startswith("_")}
                for day in list(seen_dates.values())[:5]
            ]

    except Exception as e:
        print(f"[OWM] Forecast error: {e}")
        return []


async def get_destination_weather(lat: float, lon: float) -> dict:
    """Returns both current weather and 5-day forecast for a destination."""
    import asyncio
    current, forecast = await asyncio.gather(
        get_current_weather(lat, lon),
        get_5day_forecast(lat, lon),
    )
    return {
        "current": current,
        "forecast": forecast,
    }
