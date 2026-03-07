import urllib.request
import json

payload = {
    'user_id': 'new_user',
    'tags': ['adventure', 'nature'],
    'budget_usd': 180000,
    'accessibility_required': False,
    'top_n': 8,
    'travel_style': 'adventurer',
    'origin': 'DEL',
    'include_flights': True,
    'currency_preference': 'INR',
    'session_id': None,
    'include_photos': True,
    'surprise_mode': False,
    'liked_categories': []
}

req = urllib.request.Request(
    'http://localhost:8000/recommend',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print("Status Code:", response.getcode())
        print("Response Body:", response.read().decode('utf-8')[:1000])
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print("Body:", e.read().decode('utf-8'))
except Exception as e:
    print("Exception:", e)
