import httpx
import sys

def main():
    url = "http://127.0.0.1:8000/api/auth/register"
    payload = {
        "email": "staff_test@eduquest.com",
        "password": "SecurePassword123!",
        "role": "staff"
    }
    print(f"Registering user on running server: {url}")
    try:
        res = httpx.post(url, json=payload, timeout=10)
        print("Status Code:", res.status_code)
        print("Response:", res.text)
    except Exception as e:
        print("Failed to register user:", e)

if __name__ == "__main__":
    main()
