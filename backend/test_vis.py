"""
Test visual search with better error reporting + precompute CLIP embeddings if missing.
"""
import requests
import json

# First test health
r = requests.get("http://localhost:8000/health")
print(f"Health: {r.json()}")

# Test visual search
url = "http://localhost:8000/search/visual"
img_path = r'C:\Users\sridh\.gemini\antigravity\brain\952c4de4-9ce2-4504-96bd-cc4976ca8849\test_landscape_1774801162116.png'

with open(img_path, 'rb') as f:
    files = {'file': ('test_landscape.png', f, 'image/png')}
    response = requests.post(url, files=files, params={'top_n': 5})

print(f"\nStatus: {response.status_code}")
if response.status_code == 200:
    results = response.json()
    print(f"Visual Search matched {results['total']} destinations:\n")
    for res in results['results']:
        print(f"  [{res['visual_similarity']:.4f}] {res['name']}, {res['country']}")
        print(f"           {res['description'][:100]}...")
        print()
else:
    print(f"Error body:\n{response.text[:2000]}")
