import httpx
import json

try:
    res = httpx.get("http://127.0.0.1:8000/openapi.json")
    if res.status_code == 200:
        openapi = res.json()
        paths = list(openapi.get("paths", {}).keys())
        print("Registered paths on running server:")
        for path in sorted(paths):
            if "users" in path or "auth" in path:
                print(f" - {path}")
    else:
        print(f"Failed to fetch openapi.json: {res.status_code}")
except Exception as e:
    print("Error querying server:", e)
