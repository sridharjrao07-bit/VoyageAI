"""
Agent v2 — Full Demo (Direct Engine Layer)
Calls the engine directly (bypasses async wikidata/photo enrichment)
to cleanly demonstrate all 5 AI upgrades.
"""
import sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Boot the data layer
from engine import data_loader
data_loader.load_data()

from engine.sanitizer import sanitize_dataframes
from engine.tag_expander import expand_tags
from engine.hybrid import recommend
from engine.semantic_search import semantic_search
from engine.history import record_seen, get_seen, clear_seen

SEP = "\n" + "=" * 65

# ── DEMO 1: Semantic Search ──────────────────────────────────────
print(SEP)
print("DEMO 1 — SEMANTIC SEARCH  'peaceful hills'")
print("  (No destination is literally tagged 'peaceful' — AI infers meaning)")
results = semantic_search("peaceful hills", top_n=5)
if results:
    for d in results:
        print(f"  [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}")
        print(f"           tags: {d['tags']}")
else:
    print("  (model not loaded yet)")

print(SEP)
print("DEMO 1b — SEMANTIC SEARCH  'hidden jungle secret adventure'")
for d in semantic_search("hidden jungle secret adventure", top_n=5):
    print(f"  [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}")
    print(f"           tags: {d['tags']}")

# ── DEMO 2: Zero-Trust Sanitizer ─────────────────────────────────
print(SEP)
print("DEMO 2 — ZERO-TRUST SANITIZER  (on clean production data)")
df = data_loader.get_destinations()
ratings = data_loader.get_ratings()
_, _, report = sanitize_dataframes(df, ratings, max_age_days=30)
print(f"  Destinations scanned       : {report['total_destinations_before']}")
print(f"  Removed (test/fake names)  : {report['removed_placeholder_destinations']}")
print(f"  Removed (ghost coords 0,0) : {report['removed_invalid_coords']}")
print(f"  CLEAN destinations passed  : {report['total_destinations_after']}")
print(f"  Stale ratings purged (30d) : {report['removed_stale_ratings']}")

# ── DEMO 3: Semantic Intent Expansion + 40% Discovery ────────────
print(SEP)
print("DEMO 3 — SEMANTIC INTENT EXPANSION + 40% DISCOVERY QUOTA")
print("  User says: 'adventure'")
expanded = expand_tags(["adventure"])
print(f"  Agent expands to: {expanded}")
print()
results3 = recommend("demo_user", ["adventure"], 0, False, top_n=8)
discoveries = [r for r in results3 if r.get("is_discovery")]
regulars    = [r for r in results3 if not r.get("is_discovery")]
pct = round(len(discoveries) / len(results3) * 100) if results3 else 0
print(f"  Total: {len(results3)}  |  Discoveries: {len(discoveries)} ({pct}%)  |  Regular: {len(regulars)}")
print()
for rec in results3:
    disc = "[DISCOVERY]" if rec.get("is_discovery") else "           "
    print(f"  {disc} {rec['name']}, {rec['country']}  score={rec['score']:.3f}")
    print(f"              {rec['xai_snippet'][:90]}")

# ── DEMO 4: Anti-Repetition ───────────────────────────────────────
print(SEP)
print("DEMO 4 — ANTI-REPETITION  (two calls, zero overlap)")
clear_seen("antitest")
r_call1 = recommend("antitest", ["beach", "tropical"], 0, False, top_n=5)
ids1 = [r["id"] for r in r_call1]
names1 = [r["name"] for r in r_call1]
record_seen("antitest", ids1)   # server does this automatically in /recommend

print(f"  CALL 1 showed: {names1}")
r_call2 = recommend("antitest", ["beach", "tropical"], 0, False, top_n=5, seen_ids=get_seen("antitest"))
ids2 = [r["id"] for r in r_call2]
names2 = [r["name"] for r in r_call2]
print(f"  CALL 2 showed: {names2}")
overlap = set(ids1) & set(ids2)
print(f"  Overlap: {'ZERO — PASS!' if not overlap else overlap}")

# ── DEMO 5: Delta XAI — freshness explanation ─────────────────────
print(SEP)
print("DEMO 5 — DELTA XAI  (explains why each pick is fresh vs seen)")
print("  User has already seen: Bali (1), Santorini (3), Maldives (11)")
r5 = recommend("delta_user", ["nature", "peaceful"], 0, False, top_n=4,
               seen_ids=["1", "3", "11"])
for rec in r5:
    disc = "[DISCOVERY] " if rec.get("is_discovery") else "            "
    print(f"\n  {disc}{rec['name']}, {rec['country']}")
    print(f"  AI says: {rec['xai_snippet']}")

# ── DEMO 6: Ghost User + Tag Expansion transparency ───────────────
print(SEP)
print("DEMO 6 — EXPANDED TAGS USED (transparency field in each result)")
if results3:
    print(f"  {results3[0]['name']} was found using these expanded tags:")
    print(f"  {results3[0].get('expanded_tags_used', [])}")

print(SEP)
print("ALL DEMOS COMPLETE. Agent v2 is working.")
