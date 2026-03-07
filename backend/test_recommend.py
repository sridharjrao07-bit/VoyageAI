import sys
import os
import asyncio
import json

sys.path.append(os.path.dirname(__file__))

from main import recommend, RecommendRequest
from engine.data_loader import load_data
from engine.db import init_db
from engine.cache import recommendation_cache

async def test():
    init_db()
    load_data()
    
    # clear cache to force LLM generation
    recommendation_cache.clear()

    req = RecommendRequest(
        user_id="test_social_user",
        tags=["europe", "beach", "history", "nature"],
    )

    print("Requesting recommendations...")
    res = await recommend(req)
    
    print("\n" + "="*50)
    print("RESULTS:")
    
    recs = res.get("recommendations", [])
    
    # Print the IDs to see if Dest 1 is vetoed
    dest1_present = any(str(r["id"]) == "1" for r in recs)
    dest2_present = any(str(r["id"]) == "2" for r in recs)
    dest3_present = any(str(r["id"]) == "3" for r in recs)
    
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write(f"Dest 1 (Safety Risk) Present: {dest1_present} (Should be False)\n")
        f.write(f"Dest 2 (Good/Pro-Tip) Present: {dest2_present}\n")
        f.write(f"Dest 3 (Spam) Present: {dest3_present}\n")

        for r in recs:
            f.write(f"\nID: {r.get('id')} | Name: {r.get('name')}\n")
            f.write(f"Reasoning: {r.get('xai_snippet')}\n")

    
if __name__ == "__main__":
    asyncio.run(test())
