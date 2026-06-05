from core.ai_engine import get_async_openai_client

async def mark_student_work(student_answer, marking_guide, subject, level):
    """
    Uses AI to evaluate student answers against the official marking guide.
    """
    client = get_async_openai_client()
    
    system_prompt = f"Evaluate student answer for {subject} {level} against marking guide."
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Use mini for faster marking
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"GUIDE:\n{marking_guide}\n\nSTUDENT:\n{student_answer}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Marking Synthesis Failed: {e}")
