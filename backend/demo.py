"""
Live demo script — tests all 3 AI features against the running localhost server.
"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return json.loads(r.read())

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

SEP = "\n" + "-" * 60

# -- DEMO 1: Semantic Search ------------------------------------------
print(SEP)
print("DEMO 1 -- Semantic Search: 'peaceful hills'")
r1 = get("/search?q=peaceful+hills&top_n=5")
print(f"  {r1['total']} results (matched by MEANING, not keywords):")
for d in r1["results"]:
    print(f"  [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}  | tags: {d['tags']}")

print(SEP)
print("DEMO 1b -- Semantic Search: 'hidden jungle secret adventure'")
r1b = get("/search?q=hidden+jungle+secret+adventure&top_n=5")
for d in r1b["results"]:
    print(f"  [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}  | tags: {d['tags']}")

# -- DEMO 2: Data Sanitization ----------------------------------------
print(SEP)
print("DEMO 2 -- Data Sanitization Report")
san = get("/admin/sanitize")
s = san["startup_sanitization"]
print(f"  Destinations before : {s['total_destinations_before']}")
print(f"  Removed (fake names): {s['removed_placeholder_destinations']}")
print(f"  Removed (bad coords): {s['removed_invalid_coords']}")
print(f"  Clean destinations  : {s['total_destinations_after']}")
print(f"  Stale ratings purged: {s['removed_stale_ratings']}")

# -- DEMO 3: Anti-Repetition ------------------------------------------
print(SEP)
print("DEMO 3a -- First recommendation call (beach, tropical) for 'demo_user'")
r3a = post("/recommend", {
    "user_id": "demo_user", "tags": ["beach", "tropical"],
    "top_n": 5, "seen_ids": [], "include_photos": False
})
ids1 = [rec["id"] for rec in r3a["recommendations"]]
print(f"  Novelty injected: {r3a['novelty_count']} / 5")
for rec in r3a["recommendations"]:
    tag = "[NOVELTY]" if rec.get("is_novelty") else "         "
    print(f"  {tag} ID={rec['id']:>3}  {rec['name']}, {rec['country']}  score={rec['score']:.3f}")

print(SEP)
print("DEMO 3b -- Second call -- server memory auto-excludes call-1 destinations")
r3b = post("/recommend", {
    "user_id": "demo_user", "tags": ["beach", "tropical"],
    "top_n": 5, "seen_ids": [], "include_photos": False
})
ids2 = [rec["id"] for rec in r3b["recommendations"]]
overlap = set(ids1) & set(ids2)
print(f"  Novelty injected: {r3b['novelty_count']} / 5")
for rec in r3b["recommendations"]:
    tag = "[NOVELTY]" if rec.get("is_novelty") else "         "
    print(f"  {tag} ID={rec['id']:>3}  {rec['name']}, {rec['country']}  score={rec['score']:.3f}")

print(SEP)
if overlap:
    print(f"  FAIL - Repeated IDs found: {overlap}")
else:
    print(f"  PASS - Zero overlap between calls!")
    print(f"  Call 1 IDs: {ids1}")
    print(f"  Call 2 IDs: {ids2}")
    print("  Anti-repetition memory is working perfectly.")

# -- DEMO 4: History --------------------------------------------------
print(SEP)
print("DEMO 4 -- Server-side view history for 'demo_user'")
hist = get("/history/seen/demo_user")
print(f"  Accumulated {len(hist['seen_ids'])} seen IDs: {hist['seen_ids']}")
print(SEP)
print("Demo complete.")
