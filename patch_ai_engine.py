import re
import os

with open("core/ai_engine.py", "r") as f:
    content = f.read()

# 1. Fix line 21
content = re.sub(
    r'BASE_DIR = os.path.dirname\(os.path.dirname\(os.path.abspath\(__filclass UnifiedImageGenerator:',
    r'BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n\nclass UnifiedImageGenerator:',
    content
)

# 2. Fix generate_illustration syntax
content = re.sub(
    r'return await UnifiedImageGenerator.generate\(question_text, subject, level, custom_prompt, style\)\): \{e\}"\)\n        return None',
    r'return await UnifiedImageGenerator.generate(question_text, subject, level, custom_prompt, style)',
    content
)

# 3. Add SVG fallback to _generate_raster_png
old_png_except = r"""        except Exception as e:
            print\(f"UnifiedImageGenerator error \(DALL-E 3\): \{e\}"\)
            return None"""
new_png_except = r"""        except Exception as e:
            print(f"UnifiedImageGenerator error (DALL-E 3): {e}")
            print(f"DEBUG: Falling back to SVG generation via GPT-4o for: {drawing_desc[:30]}...")
            return await UnifiedImageGenerator._generate_vector_svg(drawing_desc)"""
content = re.sub(old_png_except, new_png_except, content)

# 4. Vibrant colors in SVG generator
old_svg_prompt = r"""Create a clean, professional black-and-white SVG illustration based on this description: "\{prompt\}"
RULES:
1\. Output ONLY raw <svg> code — no markdown, no explanation\.
2\. Use viewBox="0 0 500 350"\.
3\. Black strokes only \(stroke="#000"\), max stroke-width="2", white background\.
4\. Keep it simple, clear, and appropriate for a printed exam paper\.
5\. All text labels must use font-family="Arial, sans-serif" font-size="11"\.
6\. Do NOT include any colour fills except very light grey \(#f5f5f5\) for backgrounds\."""
new_svg_prompt = r"""Create a clean, colorful, and highly engaging SVG illustration based on this description: "{prompt}"
RULES:
1. Output ONLY raw <svg> code — no markdown, no explanation.
2. Use viewBox="0 0 500 350".
3. Use vibrant, child-friendly colors for all elements. Use clean lines and flat colors (no complex gradients).
4. Keep it visually engaging, clear, and appropriate for modern educational materials.
5. All text labels must use font-family="Arial, sans-serif" font-size="12" with excellent contrast.
6. Make sure key educational elements stand out brightly."""
content = re.sub(old_svg_prompt, new_svg_prompt, content)

# 5. Add Semaphore to generate_scenario_content
old_scenario_loop = r"""            if draw_tasks:
                async def refine_q\(q\):
                    result = await generate_illustration\(q\["text"\], subject, level, style="png"\)"""
new_scenario_loop = r"""            if draw_tasks:
                sem = asyncio.Semaphore(2)
                async def refine_q(q):
                    async with sem:
                        result = await generate_illustration(q["text"], subject, level, style="png")"""
content = re.sub(old_scenario_loop, new_scenario_loop, content)

# 6. Append stream_generate_ai_content
stream_func = r"""
async def stream_generate_ai_content(mode, level, subject, term, num_questions, difficulty="Balanced", ai_model="gpt-4o", internal="Internal", topic="", pedagogy_hint=None, force_images=False, duration="2 HR", brand_name="EDUMERC"):
    from ui.document_builder import build_header_html, build_question_html, build_answer_row_html, build_footer_html
    import json
    import asyncio
    
    client = get_async_openai_client()
    syllabus_rows = retrieve_syllabus_context(subject, level, term, topic)
    year = "2026"

    ps = get_paper_structure(subject, level)
    official_total = get_total_questions(subject, level)
    num_questions = official_total if official_total > 0 else num_questions

    math_subjects = ["Math", "Physics", "Science"]
    is_math = any(s in subject for s in math_subjects)
    tikz_rule = "- TikZ (Construction): For Maths/Physics, use precise coordinates for geometry." if is_math else ""
    is_preprimary = any(k in level for k in ["Baby", "Middle", "Top", "Primary 1", "Primary 2", "Primary 3", "Nursery", "Kindergarten", "P1", "P2", "P3"])

    age_profile = "General Audience"
    if "Baby" in level or "Middle" in level or "Top" in level: age_profile = "Ages 3-5"
    elif "Primary 1" in level or "Primary 2" in level or "Primary 3" in level: age_profile = "Ages 6-8"
    elif "Primary 4" in level or "Primary 5" in level: age_profile = "Ages 9-11"
    elif "Primary 6" in level or "Primary 7" in level: age_profile = "Ages 12-13"
    elif "Senior 1" in level or "Senior 2" in level: age_profile = "Ages 14-15"
    elif "Senior 3" in level or "Senior 4" in level: age_profile = "Ages 16-17"
    elif "Senior 5" in level or "Senior 6" in level: age_profile = "Ages 18+"

    authorized_topics = []
    from core.syllabus_master import MASTER_SYLLABUS
    if subject in MASTER_SYLLABUS and level in MASTER_SYLLABUS[subject]:
        authorized_topics = MASTER_SYLLABUS[subject][level]
    authorized_topics_str = ", ".join(authorized_topics) if authorized_topics else "General Subject Knowledge"

    term_roman = "I"
    if "Term 2" in term: term_roman = "II"
    elif "Term 3" in term: term_roman = "III"
    exam_type = "BEGINNING OF"
    if "(MOT)" in term or "MOT" in term: exam_type = "MIDDLE OF"
    elif "(EOT)" in term or "EOT" in term: exam_type = "END OF"

    header_html = build_header_html(
        mode=mode, exam_type=exam_type, level=level, subject=subject,
        term_roman=f"TERM {term_roman}", exam_year=year, duration=duration,
        school_name="EduQuest Central", brand_name=brand_name, question_count=num_questions, topic=topic
    )
    yield json.dumps({"type": "header", "html": header_html}) + "\\n\\n"

    async def _generate_chunk(chunk_size: int, start_num: int):
        prep_req = "\\n5. PRE-PRIMARY VISUAL REQUIREMENT: ALMOST EVERY question MUST be visually driven. Include an explicit image placeholder like '[Picture of 3 big red apples]' for every single question!" if is_preprimary else ""
        prompt = f\"\"\"### NATIONAL EXAM PROTOCOL - {subject.upper()} | {level} | {term}
You are an expert curriculum designer.
Topic Focus: {topic or 'Full Syllabus'}
Syllabus Context (RAG): {syllabus_rows}

### PEDAGOGICAL & COGNITIVE CONSTRAINTS:
1. TARGET AUDIENCE: {age_profile}.
2. STRICT COGNITIVE CEILING: The authorized topics are: [{authorized_topics_str}]. Do not exceed these.
3. BLOOM'S TAXONOMY: 40% Knowledge, 40% Application, 20% Synthesis/Evaluation.
4. ITEM RIGOR: Language must be formal.{prep_req}

### FORMATTING PROTOCOL:
- Return ONLY a valid JSON object.
{tikz_rule}
- STUDENT DRAWING SPACE: If it requires the student to draw, sketch, plot, or construct, set "needs_student_drawing": true and "tikz_code": null.

Generate {chunk_size} unique questions. Start numbering exactly from {start_num}.
Output JSON structure:
{{
  "questions": [
    {{
      "number": {start_num},
      "topic": "Topic Name",
      "text": "Question text...",
      "marks": 1,
      "answer": "Correct answer...",
      "tikz_code": null,
      "needs_student_drawing": false
    }}
  ]
}}
\"\"\"
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a professional examiner. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content).get("questions", [])
        except Exception as e:
            print(f"Chunk generation error: {e}")
            return []

    chunk_size = 5
    tasks = []
    for i in range(0, num_questions, chunk_size):
        size = min(chunk_size, num_questions - i)
        tasks.append(_generate_chunk(size, i + 1))
    
    all_questions = []
    answer_key_rows = ""
    
    sem = asyncio.Semaphore(2)
    
    for task in tasks:
        # Await sequentially to preserve question ordering 1..N
        chunk = await task
        if not chunk: continue
        
        async def process_question(q):
            text = q.get("text", "")
            tikz = q.get("tikz_code")
            draw_keywords = ["draw", "construct", "sketch", "graph", "plot"]
            if any(k in text.lower() for k in draw_keywords) and tikz and "<img" not in str(tikz).lower():
                ans = q.get("answer", "")
                q["answer"] = f"{ans}\\n\\n**Expected Construction:**\\n{process_tikz_safeguard(tikz)}"
                q["tikz_code"] = None
            elif tikz and "<img" not in str(tikz).lower():
                q["tikz_code"] = process_tikz_safeguard(tikz)

            is_organic = any(s in subject for s in ["Science", "Biology", "Social", "Geography", "SST"])
            has_visual_keywords = any(k in text.lower() for k in ["diagram", "picture", "shape", "figure", "map", "illustration", "below"])
            
            if force_images or (is_organic and has_visual_keywords):
                desc = q.get("visual_prompt") or f"A clean worksheet illustration for this {subject} question: {text}"
                async with sem:
                    res_url = await UnifiedImageGenerator.generate(text, subject, level, custom_prompt=desc, style="svg")
                    if res_url:
                        if res_url.strip().startswith("<svg") or res_url.strip().startswith("<script"):
                            q["tikz_code"] = res_url
                        else:
                            q["tikz_code"] = f'<img src="{res_url}" style="width:100%; max-width:420px; display:block; margin:15px auto; border:1px solid #eee; border-radius:4px;"/>'
            return q

        processed_chunk = await asyncio.gather(*(process_question(q) for q in chunk))
        all_questions.extend(processed_chunk)
        
        for q in processed_chunk:
            q_html = build_question_html(mode, q, subject, level)
            ans_html = build_answer_row_html(q)
            answer_key_rows += ans_html
            yield json.dumps({"type": "question", "html": q_html, "raw_q": q}) + "\\n\\n"

    footer_html = build_footer_html(answer_key_rows)
    # The frontend can use all_questions to save the raw JSON at the end
    yield json.dumps({"type": "footer", "html": footer_html, "all_questions": all_questions}) + "\\n\\n"
"""

content += stream_func

with open("core/ai_engine.py", "w") as f:
    f.write(content)
