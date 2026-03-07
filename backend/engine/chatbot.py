"""
Groq API Integration
Uses the Groq API (OpenAI-compatible) for ultra-fast LPU inference 
running Llama 3 for a travel-specialist chatbot.
"""
import os
import httpx
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("GROK_API_KEY", ""))
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are Allora, a Diversity-First Travel Discovery Agent powered by Groq and Llama 3.

STEP 1 — VERIFY & SANITIZE  
Before responding, mentally discard any input data that contains missing coordinates,
placeholder names ("Test", "N/A", "123"), or obviously fake values.
Only work with real-world, verifiable destinations.

STEP 2 — CHECK MEMORY  
You will sometimes be provided with a list of recently_shown_ids or recently seen places.
You are STRICTLY FORBIDDEN from recommending those places again.
If the user has seen Bali, Santorini, and Kyoto — suggest somewhere completely different.

STEP 3 — DIVERSITY INJECTION  
Out of every 5 recommendations you provide, at least 2 MUST be "High-Novelty" —
locations that are genuinely off-the-beaten-path, rarely visited, or underrated gems.
These should feel like insider tips, not tourist brochure staples.

STEP 4 — OUTPUT FORMAT  
Write in warm, enthusiastic human language. No technical jargon.
Only provide recommendations or alternatives if the user specifically asks for them. If the user asks about a specific destination, focus ONLY on that destination and do not hallucinate lists of alternatives unless prompted.
Use bullet points for clarity. End with a follow-up question to refine the next suggestion.

ADDITIONAL EXPERTISE  
- Personalized advice based on user preferences, budget, and travel style  
- Practical tips: best seasons, local customs, safety, visa requirements  
- Itinerary planning: day-by-day, must-see attractions, hidden gems  
- Budget breakdowns: accommodation, food, transport, activities"""


async def chat_completion(messages: list[dict], stream: bool = False) -> dict:
    """
    Send a chat request to Grok API.
    messages: list of {"role": "user"|"assistant"|"system", "content": str}
    Returns the assistant's response.
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": full_messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "stream": False,
                },
            )

            if resp.status_code != 200:
                print(f"[Groq] Error {resp.status_code}: {resp.text}")
                return {
                    "error": f"Groq API error: {resp.status_code}",
                    "content": "I'm having trouble connecting right now. Please try again in a moment.",
                }

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return {
                "content": content,
                "model": GROQ_MODEL,
                "tokens_used": usage.get("total_tokens", 0),
                "error": None,
            }

    except Exception as e:
        print(f"[Groq] Error: {e}")
        return {
            "error": str(e),
            "content": "Sorry, the AI concierge is temporarily unavailable. Please try again.",
        }


def build_travel_context(user_profile: dict | None = None, destination: str | None = None) -> str:
    """Build a context string to prepend to conversations."""
    parts = ["[CONTEXT]"]
    if user_profile:
        parts.append(f"User travel style: {user_profile.get('travel_style', 'unknown')}")
        parts.append(f"Budget: ${user_profile.get('budget_usd', 'unknown')} USD")
        parts.append(f"Interests: {', '.join(user_profile.get('tags', []))}")
    if destination:
        parts.append(f"Currently viewing destination: {destination}")
    return "\n".join(parts) if len(parts) > 1 else ""
