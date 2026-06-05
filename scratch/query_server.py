import httpx
import sys

def main():
    url = "http://127.0.0.1:8000/api/syllabus/config"
    print(f"Querying running server at: {url}")
    try:
        res = httpx.get(url, timeout=5)
        print("Status Code:", res.status_code)
        print("Response Config keys:", list(res.json().keys()))
    except Exception as e:
        print("Failed to connect to the running server:", e)

if __name__ == "__main__":
    main()
