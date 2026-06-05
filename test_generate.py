import asyncio
import httpx
import json

async def main():
    payload = {
        "mode": "Exams",
        "subject": "Mathematics",
        "level": "Primary 7",
        "term": "Term 1",
        "question_count": 5,
        "ai_model": "gpt-4o",
        "topic": ""
    }
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post("http://127.0.0.1:8000/api/generate", json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)

asyncio.run(main())
