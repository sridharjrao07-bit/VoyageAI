"""
State-Aware Recommendation Agent built with xAI Grok.

Responsible for taking a pre-filtered list of destination candidates,
scrubbing them, removing previously seen locations, expanding semantic search,
and applying diversity/safety logic.

v2 upgrades:
  - Weather Pivot (Incident Response): agent swaps unsafe destinations with
    indoor/cultural alternatives and sets pivot_applied + pivot_reason.
  - Preference Bias from liked_categories (Feedback Loop RL).
  - Surprise Mode instruction override.
"""
import os
import json
import httpx  # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]
from typing import Any
from collections import Counter

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("GROK_API_KEY", ""))
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"

_BASE_SYSTEM_PROMPT = """You are the Social Intelligence Agent for the Allora travel system.
Your primary responsibility is to use community feedback to validate or veto travel recommendations.
You also serve as a Financial Intelligence Agent.

You will receive User Context, Recently Seen IDs, and a list of Raw Destination Data (JSON), which includes 'user_comments'.

Your Process Loop:
1. Data Scrubbing: Discard any input data that contains missing coordinates, placeholder names, or obviously fake values.
2. Memory Check (Anti-Repetition): You are STRICTLY FORBIDDEN from recommending any ID found in the Recently Seen IDs list.
3. Variety Quota: Ensure that your final 5 recommendations represent a mix of "Popular Verified" and "Hidden Gem" (low-rating count) destinations.
4. Semantic Expansion: Look for deeper meaning in preferences, not just keywords.
5. Financial Accuracy Protocol:
   - Standard Conversion: Use a fixed exchange rate of $1 = ₹90 for all calculations.
   - AviationStack Integration: You will be provided with 'flight_data' inside each destination. Locate the price or fare field.
   - If 'include_flights' is true: Calculate Total = (Ground_Cost_USD * 90) + (Flight_Cost_USD * 90).
   - If 'include_flights' is false: Show only ground costs and explicitly state: "Flight costs excluded from this total."
   - Always display the final values in the user's preferred currency.
   - You MUST format all prices as whole integers with comma separators (e.g. ₹280,000). DO NOT use decimal points (e.g. no ₹280080.0).
6. Social Intelligence Protocol:
   - Consensus Over Individualism: Do not simply repeat individual comments. Identify the prevailing sentiment from 'user_comments'. If multiple users mention an issue like "overcrowded", it must become a focal point of your reasoning.
   - The Veto Rule: If recent comments (within the last 7 days) indicate a critical safety or accessibility issue (e.g., "Bridge washed out", "Road closed"), discard that destination from the final 5 recommendations, even if mathematically it scores high.
   - Social Weighting: Destinations with high "Verified Visit" comments should be prioritized over those with no community feedback.
   - Data Quality Control (Spam Detection): If a comment looks like "Test", "Fake", or gibberish, ignore it. Do not let "Trash Data" influence your "Social Proof" score.
7. Validation & Weather Pivot: If `weather_alert: true`, replace it and set `pivot_applied` and `pivot_reason`.

Output Format:
Return exactly 5 recommendations in pure JSON matching this schema:
{
  "recommendations": [
    {
      "id": "string",
      "reasoning": "string",
      "pivot_applied": false,
      "pivot_reason": ""
    }
  ]
}

Human-Centric Output (XAI Snippet):
For each recommendation, provide a 3-sentence "reasoning" paragraph that mentions:
- Why this matches their budget.
- A "Community Insight" segment (e.g., "While the hybrid engine ranks this highly for trekking, local users recently noted that the summit path is currently very muddy; I suggest bringing waterproof gear.").
- You MUST conclude with a specific "User Pro-Tip" gleaned from the comment text (e.g., "Pro-Tip: Users recommend the north-side trail for better sunrise views").
Return NOTHING BUT THE VALID JSON STRING. Do not add markdown blocks.
"""

_SURPRISE_MODE_ADDENDUM = """
!! SURPRISE MODE ACTIVE !!
Override all preference-based rules. Ignore the user's stated tags completely.
Your ONLY job is to pick the 5 most unexpected, off-the-beaten-path hidden gems.
Explain each pick as if revealing a secret, while still adhering to the Financial Accuracy and Social Validation protocols.
"""



def _build_system_prompt(surprise_mode: bool = False) -> str:
    prompt = _BASE_SYSTEM_PROMPT
    if surprise_mode:
        prompt += _SURPRISE_MODE_ADDENDUM
    return prompt


def _build_preference_context(
    user_tags: list[str],
    liked_categories: list[str],
    user_profile: dict[str, Any] | None,
    surprise_mode: bool,
    include_flights: bool = False,
    currency_preference: str = "INR"
) -> str:
    """Build the user-context section of the LLM prompt."""
    if surprise_mode:
        return "Mode: SURPRISE ME — ignore all preferences, find the most unexpected picks."

    lines = [f"User Preferences: {', '.join(user_tags)}"]

    if user_profile and "budget_usd" in user_profile and user_profile["budget_usd"] > 0:
        lines.append(f"Budget: ${user_profile['budget_usd']}")
        
    lines.append(f"Include Flights in Calculation: {include_flights}")
    lines.append(f"Currency Preference: {currency_preference}")

    if liked_categories:
        # Rank by frequency to surface top preferences
        counter = Counter(liked_categories)
        top = [cat for cat, _ in counter.most_common(5)]
        lines.append(
            f"Reinforcement Bias — User's Top Liked Categories: {', '.join(top)}. "
            "Prioritize these categories when choosing, but maintain geographic diversity."
        )

    return " | ".join(lines)


async def generate_agent_recommendations(
    user_tags: list[str],
    history_ids: list[str],
    raw_data: list[dict[str, Any]],
    user_profile: dict[str, Any] | None = None,
    liked_categories: list[str] | None = None,
    surprise_mode: bool = False,
    include_flights: bool = False,
    currency_preference: str = "INR"
) -> list[dict[str, Any]]:
    """
    Pass the context to Grok to filter and reason about the top 5 picks.

    Returns a list of dicts: [{id, reasoning, pivot_applied, pivot_reason}, ...]
    """
    context_str = _build_preference_context(
        user_tags, liked_categories or [], user_profile, surprise_mode,
        include_flights=include_flights, currency_preference=currency_preference
    )

    prompt = f"""
{context_str}
Recently Seen IDs: {history_ids}
Raw Data: {json.dumps(raw_data, ensure_ascii=False)}
"""

    system_prompt = _build_system_prompt(surprise_mode)

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
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()

            content = resp.json()["choices"][0]["message"]["content"]

            # Clean up potential markdown formatting from the response
            # Note: Groq with response_format="json_object" guarantees JSON.
            # We enforce returning {"recommendations": [...]} to satisfy json_object constraints.
            # We'll extract the array from the object if needed.
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            try:
                parsed = json.loads(content.strip())
                # If Groq wrapped it in a dict because of json_object mode
                if isinstance(parsed, dict) and "recommendations" in parsed:
                    parsed = parsed["recommendations"]
                elif isinstance(parsed, dict) and len(parsed.keys()) == 1:
                    # Generic unwrapper
                    key = list(parsed.keys())[0]
                    if isinstance(parsed[key], list):
                        parsed = parsed[key]
            except json.JSONDecodeError as e:
                print(f"[Agent] JSON parse error: {e}\nContent was: {content}")
                return []

            # Ensure every entry has the pivot fields (backfill for safety)
            for item in parsed:
                item.setdefault("pivot_applied", False)
                item.setdefault("pivot_reason", "")

            return parsed

    except httpx.HTTPStatusError as e:
        print(f"[Groq Agent] HTTPStatusError {e.response.status_code}: {e.response.text}")
        return []
    except Exception as e:
        print(f"[Groq Agent] Error generating recommendations: {e}")
        return []
