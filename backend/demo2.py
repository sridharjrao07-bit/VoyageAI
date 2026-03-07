import json, urllib.request
BASE = "http://localhost:8000"

def get(p):
    return json.loads(urllib.request.urlopen(BASE + p, timeout=20).read())

def post(p, b):
    req = urllib.request.Request(
        BASE + p, json.dumps(b).encode(), {"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

print("=== DEMO 1: SEMANTIC SEARCH: peaceful hills ===")
r = get("/search?q=peaceful+hills&top_n=5")
if r["results"]:
    for d in r["results"]:
        print(f"  {d['semantic_score']:.3f} | {d['name']}, {d['country']} | {d['tags']}")
else:
    print("  (model not yet loaded)")

print("\n=== DEMO 1b: SEMANTIC SEARCH: hidden jungle adventure ===")
r = get("/search?q=hidden+jungle+adventure&top_n=5")
if r["results"]:
    for d in r["results"]:
        print(f"  {d['semantic_score']:.3f} | {d['name']}, {d['country']} | {d['tags']}")
else:
    print("  (model not yet loaded)")

print("\n=== DEMO 2: DATA SANITIZATION ===")
san = get("/admin/sanitize")["startup_sanitization"]
print(f"  Destinations before : {san['total_destinations_before']}")
print(f"  Removed placeholder : {san['removed_placeholder_destinations']}")
print(f"  Removed bad coords  : {san['removed_invalid_coords']}")
print(f"  Clean destinations  : {san['total_destinations_after']}")
print(f"  Stale ratings purged: {san['removed_stale_ratings']}")

print("\n=== DEMO 3a: FIRST RECOMMENDATION (beach/tropical) ===")
r1 = post("/recommend", {
    "user_id": "testuser99", "tags": ["beach", "tropical"],
    "top_n": 5, "seen_ids": [], "include_photos": False
})
ids1 = [x["id"] for x in r1["recommendations"]]
print(f"  Novelty injected: {r1['novelty_count']}/5")
for x in r1["recommendations"]:
    n = "[NOVELTY] " if x.get("is_novelty") else "           "
    print(f"  {n}ID={x['id']:>3}  {x['name']}, {x['country']}  score={x['score']:.3f}")

print("\n=== DEMO 3b: SECOND CALL - should be ALL NEW places ===")
r2 = post("/recommend", {
    "user_id": "testuser99", "tags": ["beach", "tropical"],
    "top_n": 5, "seen_ids": [], "include_photos": False
})
ids2 = [x["id"] for x in r2["recommendations"]]
print(f"  Novelty injected: {r2['novelty_count']}/5")
for x in r2["recommendations"]:
    n = "[NOVELTY] " if x.get("is_novelty") else "           "
    print(f"  {n}ID={x['id']:>3}  {x['name']}, {x['country']}  score={x['score']:.3f}")
overlap = set(ids1) & set(ids2)
print(f"\n  Call 1 IDs: {ids1}")
print(f"  Call 2 IDs: {ids2}")
print(f"  Overlap   : {'NONE - PASS! Anti-repetition working.' if not overlap else overlap}")

print("\n=== DEMO 4: HISTORY (auto-accumulated by server) ===")
h = get("/history/seen/testuser99")
print(f"  User has seen {len(h['seen_ids'])} destinations: {h['seen_ids']}")
print("\nDemo complete.")
