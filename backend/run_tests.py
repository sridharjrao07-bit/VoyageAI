"""
Full Demo & Test Suite — Smart Tourism Agent v2
Covers: Sanitizer, Semantic Search, Tag Expansion, 40% Discovery,
        Anti-Repetition, Delta XAI, Purge Script, Performance Timing
"""
import sys, time, json, asyncio
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    icon = "[OK] " if condition else "[!!] "
    print(f"  {icon}{label}" + (f"  |  {detail}" if detail else ""))

# ── boot engine ─────────────────────────────────────────────────
from engine import data_loader
data_loader.load_data()

# Ensure embeddings are computed in this process
from engine.semantic_search import precompute_embeddings as _precompute
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(_precompute(data_loader.get_destinations()))

from engine.sanitizer        import sanitize_dataframes
from engine.tag_expander     import expand_tags
from engine.hybrid           import recommend
from engine.semantic_search  import semantic_search
from engine.history          import record_seen, get_seen, clear_seen


SEP = "\n" + "-" * 62

# ══════════════════════════════════════════════════════════════
# TEST 1: DATA SANITIZATION
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("TEST 1 — DATA SANITIZATION (Zero-Trust)")
print("=" * 62)

df       = data_loader.get_destinations()
ratings  = data_loader.get_ratings()
_, _, rpt = sanitize_dataframes(df, ratings, max_age_days=30)

print(f"  Destinations before : {rpt['total_destinations_before']}")
print(f"  Removed (placeholders): {rpt['removed_placeholder_destinations']}")
print(f"  Removed (ghost 0,0)  : {rpt['removed_invalid_coords']}")
print(f"  Clean destinations   : {rpt['total_destinations_after']}")
print(f"  Stale ratings purged : {rpt['removed_stale_ratings']}")

check("All 100 destinations pass zero-trust filter",
      rpt["total_destinations_after"] == rpt["total_destinations_before"])
check("Ghost-coord (0,0) check is active",
      "removed_invalid_coords" in rpt)

# ══════════════════════════════════════════════════════════════
# TEST 2: SEMANTIC TAG EXPANSION
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 2 — SEMANTIC TAG EXPANSION")

exp_adventure = expand_tags(["adventure"])
exp_peaceful  = expand_tags(["peaceful"])
exp_spiritual = expand_tags(["spiritual"])
print(f"  'adventure'  -> {exp_adventure}")
print(f"  'peaceful'   -> {exp_peaceful}")
print(f"  'spiritual'  -> {exp_spiritual}")

check("'adventure' expands to include 'climbing'",   "climbing"  in exp_adventure)
check("'adventure' expands to include 'rafting'",    "rafting"   in exp_adventure)
check("'adventure' expands to include 'kayaking'",   "kayaking"  in exp_adventure)
check("'peaceful'  expands to include 'serene'",     "serene"    in exp_peaceful)
check("'spiritual' expands to include 'meditation'", "meditation" in exp_spiritual)
check("Original tag preserved in expansion",          "adventure" in exp_adventure)

# ══════════════════════════════════════════════════════════════
# TEST 3: SEMANTIC SEARCH
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 3 — SEMANTIC SEARCH (meaning over keywords)")

t0 = time.perf_counter()
sr1 = loop.run_until_complete(semantic_search("peaceful hills", top_n=5))
t_search = round((time.perf_counter() - t0) * 1000, 1)

if sr1:
    print(f"  Query: 'peaceful hills'  [{t_search}ms]")
    for d in sr1:
        print(f"    [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}")
    check("Semantic search returns results", len(sr1) > 0,
          f"{len(sr1)} results in {t_search}ms")
    check("Results have semantic_score field", "semantic_score" in sr1[0])
    check("Semantic search under 500ms", t_search < 500, f"{t_search}ms")
else:
    print("  (model not loaded)")
    check("Semantic search returns results", False, "model not loaded")

sr2 = loop.run_until_complete(semantic_search("hidden jungle adventure", top_n=5))
print(f"\n  Query: 'hidden jungle adventure'")
for d in sr2:
    print(f"    [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}")
check("Different queries return different results", set(d['name'] for d in sr1) != set(d['name'] for d in sr2))

# ══════════════════════════════════════════════════════════════
# TEST 4: 40% DISCOVERY QUOTA
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 4 — 40% DISCOVERY QUOTA")

clear_seen("quota_test")
t0 = time.perf_counter()
recs = recommend("quota_test", ["adventure"], 0, False, top_n=10)
t_rec = round((time.perf_counter() - t0) * 1000, 1)

discoveries = [r for r in recs if r.get("is_discovery")]
pct = round(len(discoveries) / len(recs) * 100) if recs else 0
print(f"  Results: {len(recs)} total  |  {len(discoveries)} discoveries ({pct}%)")
print(f"  Recommend() time: {t_rec}ms")
for r in recs:
    tag = "[DISC] " if r.get("is_discovery") else "       "
    print(f"  {tag} {r['name']}, {r['country']}  score={r['score']:.3f}")

check("40% discovery quota met (>=4/10)",        len(discoveries) >= 4,      f"{len(discoveries)}/10 discoveries")
check("Each result has 'is_discovery' field",    all("is_discovery" in r for r in recs))
check("Each result has 'xai_snippet'",           all(r.get("xai_snippet") for r in recs))
check("Each result has 'expanded_tags_used'",    all("expanded_tags_used" in r for r in recs))
check("Non-empty XAI delta explanations",        all(len(r.get("xai_snippet","")) > 20 for r in recs))
check("Recommend under 500ms",                   t_rec < 500,                f"{t_rec}ms")

# ══════════════════════════════════════════════════════════════
# TEST 5: ANTI-REPETITION (seen_ids)
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 5 — ANTI-REPETITION (seen_ids strict exclusion)")

clear_seen("rep_test")
call1 = recommend("rep_test", ["beach","tropical"], 0, False, top_n=5)
ids1  = [r["id"] for r in call1]
names1 = [r["name"] for r in call1]
record_seen("rep_test", ids1)

call2 = recommend("rep_test", ["beach","tropical"], 0, False, top_n=5, seen_ids=get_seen("rep_test"))
ids2  = [r["id"] for r in call2]
names2 = [r["name"] for r in call2]
overlap = set(ids1) & set(ids2)

print(f"  Call 1: {names1}")
print(f"  Call 2: {names2}")
print(f"  Overlap: {overlap if overlap else 'NONE'}")

check("Zero overlap between call 1 and call 2", not overlap, f"overlap={overlap}")
check("Call 2 returns 5 fresh results",          len(ids2) == 5,     f"{len(ids2)} results")

# ══════════════════════════════════════════════════════════════
# TEST 6: DELTA XAI FRESHNESS EXPLANATION
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 6 — DELTA XAI (why each pick is fresh)")

print("  User already saw: IDs 1, 3, 11 (Bali, Santorini, Maldives)")
xai_recs = recommend("xai_test", ["nature","peaceful"], 0, False, top_n=4, seen_ids=["1","3","11"])
for r in xai_recs:
    disc = "[DISC] " if r.get("is_discovery") else "       "
    print(f"\n  {disc}{r['name']}, {r['country']}")
    print(f"  AI: {r['xai_snippet']}")

check("XAI results don't include seen IDs",
      all(r["id"] not in ["1","3","11"] for r in xai_recs))
check("XAI snippets are non-empty",
      all(len(r.get("xai_snippet","")) > 15 for r in xai_recs))

# ══════════════════════════════════════════════════════════════
# TEST 7: PURGE SCRIPT DRY-RUN
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 7 — PURGE SCRIPT (dry run)")
import subprocess
result = subprocess.run(["python","purge_bad_data.py"], capture_output=True, text=True, cwd=".")
purge_out = result.stdout
print(purge_out)
check("Purge script exits cleanly", result.returncode == 0)
check("Purge reports 'Purge complete'", "Purge complete" in purge_out)

# ══════════════════════════════════════════════════════════════
# TEST 8: PERFORMANCE TIMING (HTTP endpoint via TestClient)
# ══════════════════════════════════════════════════════════════
print(SEP)
print("TEST 8 — PERFORMANCE TIMING ENDPOINT")
from fastapi.testclient import TestClient
from main import app as _app
with TestClient(_app) as tc:
    r = tc.get("/performance/timing")
    if r.status_code == 200:
        pt = r.json()
        if "global" in pt:
            g = pt["global"]
            print(f"  Total requests tracked : {pt['total_requests']}")
            print(f"  Avg response time      : {g['avg_ms']}ms")
            print(f"  Median                 : {g['median_ms']}ms")
            print(f"  P95                    : {g['p95_ms']}ms")
            print(f"  P99                    : {g['p99_ms']}ms")
            print(f"  Slow (>500ms)          : {pt['slow_requests_above_500ms']}")
            print(f"  % within 500ms target  : {pt['pct_within_target']}%")
            check("Performance endpoint returns 200",          True)
            check("Average response time < 500ms",             g["avg_ms"] < 500,   f"{g['avg_ms']}ms")
            check("More than 90% of requests within 500ms",   pt["pct_within_target"] > 90,
                  f"{pt['pct_within_target']}%")
        else:
            print(f"  Response: {pt}")
            check("Performance endpoint returns 200", True)
    else:
        check("Performance endpoint returns 200", False, f"got {r.status_code}")

# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
print("TEST SUMMARY")
print("=" * 62)
passed = sum(1 for s,_,_ in results if s == PASS)
failed = sum(1 for s,_,_ in results if s == FAIL)
for status, label, detail in results:
    icon = "[OK]" if status == PASS else "[!!]"
    line = f"  {icon}  {label}"
    if detail: line += f"  ({detail})"
    print(line)
print(f"\n  {passed}/{passed+failed} tests passed" + (" -- ALL GOOD!" if failed == 0 else f" -- {failed} FAILED"))
