import os
import re
import json, asyncio
from openai import OpenAI, AsyncOpenAI
from core.db_engine import retrieve_syllabus_context

def get_openai_client():
    """Retrieves API Key from environment to instantiate OpenAI client safely."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the .env file in the root directory.")
    return OpenAI(api_key=api_key)

def get_async_openai_client():
    """Retrieves API Key from environment to instantiate AsyncOpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing.")
    return AsyncOpenAI(api_key=api_key)

def process_tikz_safeguard(raw_text):
    """Ensures that any generated TikZ code is safely wrapped for TikZJax engine."""
    clean_text = re.sub(r'```(?:tikz|latex)?\s*(\\begin\{tikzpicture\})', r'\1', raw_text)
    clean_text = re.sub(r'(\\end\{tikzpicture\})\s*```', r'\1', clean_text)
    clean_text = re.sub(r'<script type="text/tikz">\s*(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\s*</script>', r'\1', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', r'<script type="text/tikz">\n\1\n</script>', clean_text, flags=re.DOTALL)
    return clean_text


async def generate_ai_content(mode, level, subject, term, question_count, diff, ai_model, exam_type, topic="", pedagogy=None):
    """Optimized AI Engine using Parallel Async Generation for Exams."""
    client = get_async_openai_client()
    context = retrieve_syllabus_context(level, subject, term, topic)
    pedagogy = pedagogy or {}

    tone_str = pedagogy.get("tone", "Academic and traditional")
    rules_str = f"- TONE: {tone_str}\n"
    if pedagogy.get("inc_mcq"):
        rules_str += "- MCQS: Include logically distributed multi-choice options with (A)(B)(C)(D).\n"
    if pedagogy.get("inc_essay"):
        rules_str += "- ESSAYS: Include structural questions requiring critical reasoning or long-form answers.\n"

    # ── SHARED PROMPT LOGIC ──
    base_constraints = f"""
### PERSONA:
You are the CHIEF EXAMINER.
Expertise: Curriculum Standards ({subject} {level}), Bloom's Taxonomy.

### GOAL:
Generate a {mode} document for {subject} {level} (Term: {term}).
Context Reference: {context}

### PEDAGOGICAL CONSTRAINTS:
{rules_str}
- LaTeX: ALWAYS wrap math in single $ signs. 
- TikZ (Question): If a diagram is part of the question (for the student to see), put it in "tikz_code".
- TikZ (Answer): If the student is asked to DRAW a diagram, leave "tikz_code" empty. Put the sample solution TikZ code INSIDE the "answer" field, wrapped in <script type="text/tikz">...</script>.
"""

    if mode != "Exams":
        # Keep sequential for Notes/Schemes as they are narrative
        system_prompt = f"{base_constraints}\n### TASK:\nGenerate the full {mode} JSON package.\n"
        response = await client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Topic: {topic or 'General'}"}],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        data = json.loads(response.choices[0].message.content)
        raw_str = response.choices[0].message.content
    else:
        # ── PHASE 1: BLUEPRINT ──
        blueprint_prompt = f"{base_constraints}\n### TASK:\nGenerate a BLUEPRINT for a {question_count}-question exam. Identify topics and sub-topics.\nOutput JSON: {{ \"blueprint_note\": \"...\", \"topics\": [\"topic1\", \"topic2\"] }}\n"
        bp_resp = await client.chat.completions.create(
            model="gpt-4o-mini", # Use mini for blueprint
            messages=[{"role": "system", "content": blueprint_prompt}],
            response_format={"type": "json_object"}
        )
        bp_data = json.loads(bp_resp.choices[0].message.content)
        topics = bp_data.get("topics", [topic or "General Concepts"])

        # ── PHASE 2: PARALLEL QUESTION GENERATION ──
        # Generate in batches of 5
        batch_size = 5
        batches = []
        for i in range(0, question_count, batch_size):
            count = min(batch_size, question_count - i)
            start_num = i + 1
            batches.append((start_num, count))

        async def gen_batch(start, count):
            q_prompt = f"{base_constraints}\n### TASK:\nGenerate {count} questions starting from Q{start}. \nTopics to cover: {topics}\nIMPORTANT: Use 'tikz_code' ONLY for diagrams students must study. If the student must DRAW a diagram, put the solution TikZ in the 'answer' field instead.\nOutput JSON: {{ \"questions\": [{{ \"number\": {start}, \"text\": \"...\", \"marks\": 2, \"tikz_code\": \"...\", \"answer\": \"...\" }}] }}\n"
            resp = await client.chat.completions.create(
                model=ai_model,
                messages=[{"role": "system", "content": q_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            return json.loads(resp.choices[0].message.content).get("questions", [])

        # Execute parallel calls
        results = await asyncio.gather(*(gen_batch(s, c) for s, c in batches))
        
        # ── PHASE 3: ASSEMBLY ──
        all_questions = []
        for batch in results:
            all_questions.extend(batch)
        
        data = {
            "blueprint_note": bp_data.get("blueprint_note", "Parallel synthesis complete."),
            "questions": all_questions
        }
        raw_str = json.dumps(data)

    # Post-Process TikZ & Migration Safety Net
    if "questions" in data:
        for q in data["questions"]:
            text = q.get("text", "").lower()
            tikz = q.get("tikz_code")
            draw_keywords = ["draw", "construct", "sketch", "graph", "plot"]
            
            # Safety Net: If AI put a diagram in a "Draw" question, move it to the Marking Guide
            if any(k in text for k in draw_keywords) and tikz:
                ans = q.get("answer", "")
                if "<script type=\"text/tikz\">" not in ans:
                    q["answer"] = f"{ans}\n\n**Expected Construction:**\n{process_tikz_safeguard(tikz)}"
                q["tikz_code"] = None 
            
            if q.get("tikz_code"):
                q["tikz_code"] = process_tikz_safeguard(str(q["tikz_code"]))
    elif "sections" in data:
        for s in data["sections"]:
            if s.get("tikz_code"):
                s["tikz_code"] = process_tikz_safeguard(str(s["tikz_code"]))
    
    safe_output = json.dumps(data)
    title = f"{subject} {level} - {mode}"
    return data, safe_output, title

async def refine_content(text, instruction, subject, level, term):
    """Selective refinement of curriculum content based on user instruction."""
    client = get_async_openai_client()
    
    system_prompt = f"""### PERSONA:
You are the CHIEF EXAMINER.
Expertise: Curriculum Standards ({subject} {level}), Bloom's Taxonomy.

### GOAL:
Refine or rewrite the PROVIDED fragment of curriculum content.
Original Snippet: "{text}"

### INSTRUCTION:
{instruction}

### CONSTRAINTS:
1. Return ONLY the refined content. NO conversational filler.
2. Maintain the pedagogical standards of {subject} {level} for {term}.
3. If LaTeX is used, wrap it in single $ signs.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Refine: {text}"}
            ],
            temperature=0.4
        )
        refined = response.choices[0].message.content.strip()
        return process_tikz_safeguard(refined)
    except Exception as e:
        raise RuntimeError(f"Holographic Refinement Failed: {e}")

async def chat_response(messages, subject, level):
    """Conversational AI response for the Studio Chat."""
    client = get_async_openai_client()
    
    system_prompt = f"""### PERSONA:
You are the EDUQUEST AI ASSISTANT.
Expertise: Curriculum Standards ({subject} {level}), Lesson Planning.

### STYLE:
- Professional, supportive, and pedagogically sound.
- Use markdown and $...$ for LaTeX math.
"""
    
    formatted_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        formatted_messages.append(msg)
        
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=formatted_messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Neural Chat Sync Failed: {e}")

async def analyze_pedagogy(content, subject, level):
    """Deep pedagogical audit for Bloom's Taxonomy."""
    from core.syllabus_master import get_master_topics
    master_topics = get_master_topics(subject, level)
    client = get_async_openai_client()
    
    topics_str = ", ".join(master_topics) if master_topics else "General Standards"
    
    system_prompt = f"Analyze curriculum for Bloom's and topics: {topics_str}"
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # Return fallback data if AI fails
        return {
            "bloom": {"recall": 20, "comprehension": 20, "application": 20, "analysis": 20, "evaluation": 20},
            "difficulty_distribution": [50, 50, 50, 50, 50],
            "readability": 50,
            "time_estimate": 60,
            "summary": "Analytics sync currently in recovery mode.",
            "topic_saturation": {t: 0 for t in master_topics[:3]},
            "missing_critical_topics": master_topics[:2]
        }

async def generate_flow_step(topic, subject, level, bloom, difficulty="Medium"):
    """Focused generator for a single node in a Neural Flow chain."""
    client = get_async_openai_client()
    
    prompt = f"Generate 1 {bloom} question for {topic} ({subject} {level}). JSON: {{ \"question\": \"...\", \"options\": [], \"answer\": \"...\", \"explanation\": \"...\" }}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

async def generate_scenario_content(theme, level, subject, term, topic="", difficulty="Standard", ai_model="gpt-4o"):
    """Generates a real-world scenario narrative followed by application-based questions."""
    client = get_async_openai_client()
    context = retrieve_syllabus_context(level, subject, term, topic or theme)

    complexity_hint = "Standard application-based rigour."
    system_prompt = f"Generate scenario-based test for {subject} {level}. Topic: {topic or theme}. Context: {context}"

    try:
        response = await client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        data = json.loads(response.choices[0].message.content)
        if "questions" in data:
            for q in data["questions"]:
                if q.get("tikz_code"):
                    q["tikz_code"] = process_tikz_safeguard(str(q["tikz_code"]))
        safe_output = json.dumps(data)
        return data, safe_output, f"Scenario: {topic or theme}"
    except Exception as e:
        raise RuntimeError(f"Scenario Synthesis Failed: {e}")
