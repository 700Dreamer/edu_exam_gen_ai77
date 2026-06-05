import asyncio
import os
import httpx
from core.ai_engine import generate_ai_content

async def main():
    raw, raw_str, title = await generate_ai_content(
        mode="Exams",
        level="Primary 7",
        subject="Mathematics",
        term="Term 1",
        num_questions=1,
        topic="",
    )
    print(raw_str)

asyncio.run(main())
