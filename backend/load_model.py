"""Trigger semantic model download and verify it works."""
import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from engine import data_loader
data_loader.load_data()
from engine.semantic_search import semantic_search, precompute_embeddings

print("Triggering model download + embedding pre-computation...")
precompute_embeddings(data_loader.get_destinations())
print("Done! Testing search...")

r = semantic_search("peaceful hills", top_n=5)
print(f"Results ({len(r)}):")
for d in r:
    print(f"  [{d['semantic_score']:.3f}]  {d['name']}, {d['country']}")
