import sys
import httpx
import json

def test_recommend_endpoint():
    print("Testing /recommend via the Agentic Pipeline with SQLite history...")
    url = "http://localhost:8000/recommend"
    test_user_id = "test_agent_user_1"
    
    # 1. Clear database history for this user via direct db call (for clean test)
    try:
        from engine.db import clear_user_history
        clear_user_history(test_user_id)
        print("Cleared old history for test user.")
    except Exception as e:
        print(f"Note: Could not clear history directly: {e}")

    # First Call
    print("\n--- FIRST CALL ---")
    payload1 = {
        "user_id": test_user_id,
        "tags": ["adventure", "mountains"],
        "budget_usd": 1500,
        "accessibility_required": False,
        "top_n": 5, # The new agent limits to 5 anyway
        "include_photos": False,
        "weather_aware": False 
    }
    
    try:
        resp = httpx.post(url, json=payload1, timeout=60.0)
        resp.raise_for_status()
        data1 = resp.json()
        print(f"Total returned: {data1.get('total')}")
        for r in data1.get("recommendations", []):
            print(f"- {r['name']} ({r['country']})")
            print(f"  Reasoning: {r.get('xai_snippet')}")
        
    except Exception as e:
        print(f"Error on first call: {e}")
        return

    # Second Call
    print("\n--- SECOND CALL (Testing Diversity & Memory) ---")
    payload2 = {
        "user_id": test_user_id,
        "tags": ["adventure", "mountains"],
        "budget_usd": 1500,
        "accessibility_required": False,
        "top_n": 5,
        "include_photos": False,
        "weather_aware": False 
    }
    
    try:
        resp2 = httpx.post(url, json=payload2, timeout=60.0)
        resp2.raise_for_status()
        data2 = resp2.json()
        print(f"Total returned: {data2.get('total')}")
        
        # Verify no overlap
        names1 = set(r['name'] for r in data1.get("recommendations", []))
        names2 = set(r['name'] for r in data2.get("recommendations", []))
        overlap = names1.intersection(names2)
        
        for r in data2.get("recommendations", []):
            print(f"- {r['name']} ({r['country']})")
            print(f"  Reasoning: {r.get('xai_snippet')}")
            
        print("\n--- RESULTS ---")
        if overlap:
            print(f"❌ FAIL: Repetition detected! Overlapping destinations: {overlap}")
        else:
            print(f"✅ PASS: No repetition. History feature works!")
            
    except Exception as e:
        print(f"Error on second call: {e}")

if __name__ == "__main__":
    test_recommend_endpoint()
