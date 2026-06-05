import asyncio
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Load env variables
load_dotenv(Path(__file__).parent.parent / ".env")

async def test_agent():
    print("Initializing test for upgraded Integrity Agent...")
    
    from core.ai_engine import get_async_openai_client
    from core.integrity_agent import run_integrity_check

    # Mock nursery exam data structure
    mock_exam = {
        "class_level": "Primary 1",
        "subject": "Mathematics",
        "level": "Primary 1",
        "learning_area": "LA4",
        "topic": "Addition",
        "questions": [
            {
                "number": 1,
                "type": "add_numbers",
                "instruction": "Add these numbers.",
                "content": {
                    "sums": [
                        {"a": 4, "b": 3}
                    ]
                }
            }
        ]
    }

    client = get_async_openai_client()
    print("Running 3-tier integrity audit (Rules + VLM Visual Layout Auditor + PKG Safeguards)...")
    
    # Run the integrity check (with ai_check=True so it does both deep checking and layout audit)
    report = await run_integrity_check(mock_exam, client=client, ai_check=True, ai_sample_size=1)
    
    print("\n--- INTEGRITY REPORT RESULTS ---")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Overall Score: {report['overall_score']}/100")
    print(f"Summary: {report['summary']}")
    
    print(f"\nPKG Warnings ({len(report['pkg_warnings'])}):")
    for w in report['pkg_warnings']:
        print(f"  - {w}")
        
    print(f"\nLayout Status: {report['layout_status']}")
    print(f"Layout Warnings ({len(report['layout_warnings'])}):")
    for lw in report['layout_warnings']:
        print(f"  - {lw}")
        
    print(f"\nLayout CSS Patch Length: {len(report['layout_css_patch'])} characters")
    if report['layout_css_patch']:
        print("CSS Sample:")
        print(report['layout_css_patch'][:300] + "...")

if __name__ == "__main__":
    asyncio.run(test_agent())
