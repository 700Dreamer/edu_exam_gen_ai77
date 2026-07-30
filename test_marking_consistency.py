import asyncio
import os
import sys

from core.worker_engine import normalize_q_key, question_sort_tuple, get_queue_metrics

def test_question_key_normalization():
    print("Running Question Key Normalization Tests...")
    test_cases = [
        ("Q1(a)", "1a"),
        ("Question 1 (b)", "1b"),
        ("1. a", "1a"),
        ("Q. 2 (c)", "2c"),
        ("3", "3"),
        ("Q10(d)", "10d"),
        ("", "0"),
        (None, "0"),
    ]
    for raw, expected in test_cases:
        res = normalize_q_key(raw)
        assert res == expected, f"Expected normalize_q_key('{raw}') to be '{expected}', got '{res}'"
        print(f"  ✓ normalize_q_key('{raw}') -> '{res}'")

def test_question_sorting():
    print("\nRunning Question Sorting Stability Tests...")
    questions = [
        {"q_number": "Q2(b)"},
        {"q_number": "1(a)"},
        {"q_number": "Q1(b)"},
        {"q_number": "10(a)"},
        {"q_number": "2(a)"},
    ]
    sorted_questions = sorted(questions, key=question_sort_tuple)
    sorted_keys = [q["q_number"] for q in sorted_questions]
    expected_keys = ["1(a)", "Q1(b)", "2(a)", "Q2(b)", "10(a)"]
    assert sorted_keys == expected_keys, f"Expected {expected_keys}, got {sorted_keys}"
    print(f"  ✓ Sorted keys: {sorted_keys}")

async def main():
    print("=" * 60)
    print("       EDULYTICS MARKING ENGINE RELIABILITY TEST        ")
    print("=" * 60)
    test_question_key_normalization()
    test_question_sorting()
    metrics = await get_queue_metrics()
    print(f"\nQueue engine health check: {metrics}")
    print("\nAll deterministic marking verification tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
