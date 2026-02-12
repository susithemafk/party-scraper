import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
model = "gemini-2.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"

data = {
    "contents": [{
        "parts": [{"text": "Hello"}]
    }]
}

headers = {'Content-Type': 'application/json'}

print(f"Sending request to {url}...", flush=True)

try:
    req = urllib.request.Request(url, data=json.dumps(
        data).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print("Success!", flush=True)
        print(result[:200], flush=True)
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}", flush=True)
    print(e.read().decode('utf-8'), flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

print("Test complete.", flush=True)
