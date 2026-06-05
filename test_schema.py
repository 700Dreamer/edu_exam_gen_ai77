import asyncio
from core.ai_engine import generate_nursery_exam

async def test():
    print("Testing Baby Class LA4...")
    exam = await generate_nursery_exam("Baby Class", "LA4", term="Term 1")
    for q in exam["questions"]:
        print(f"Q{q['number']}: {q['type']} - {q['instruction']}")
        
if __name__ == "__main__":
    asyncio.run(test())
