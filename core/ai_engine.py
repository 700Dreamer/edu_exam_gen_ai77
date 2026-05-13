import os
import re
import json, asyncio, uuid
import base64
from typing import Optional
from openai import OpenAI, AsyncOpenAI
from google import genai
from core.db_engine import retrieve_syllabus_context
from core.map_library import get_best_map
from core.paper_structure import get_paper_structure, get_total_questions
from core.syllabus_master import MASTER_SYLLABUS
import requests
import uuid

# ── Gemini Client Initialization ──
google_key = os.environ.get("GOOGLE_API_KEY")
if google_key:
    gemini_client = genai.Client(api_key=google_key)
else:
    gemini_client = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def generate_ai_image(prompt, subject="Geography", level=""):
    """Library-first map generation: SVG library → Imagen 4 fallback."""
    # ── STEP 1: Check curated SVG library for known maps ──
    svg = get_best_map(prompt)
    if svg:
        print(f"DEBUG: SVG Library match found for [{subject}]")
        return svg  # Return raw SVG string directly

    # ── STEP 2: Imagen 4 fallback for unknown map requests ──
    google_key = os.environ.get("GOOGLE_API_KEY")
    if not google_key:
        return None

    filename = f"map_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Enriched prompt for better Imagen 4 accuracy depending on age group
    if "Class" in level:
        full_prompt = (
            f"A simple, bold black-and-white line drawing for a kindergarten/pre-primary worksheet: {prompt}. "
            "Style: clean, thick black outlines, pure white background, no shading, no text. "
            "Very easy for 4-5 year old children to identify or color."
        )
    else:
        full_prompt = (
            f"A professional black-and-white academic map/diagram for a {subject} exam: {prompt}. "
            "Style: clean cartography textbook illustration. Show correct geographic borders, "
            "clearly labeled country names, capital cities marked with a star, major lakes in light grey, "
            "compass rose in corner, scale bar at bottom. Sharp lines, white background, no color fills."
        )

    try:
        print(f"DEBUG: Imagen 4 fallback for [{subject}]...")
        response = gemini_client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=full_prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
            ),
        )
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            print(f"DEBUG: Imagen 4 Success -> {filename}")
            return f"/generated/{filename}"
        else:
            print("DEBUG: Imagen 4 returned no images.")
    except Exception as e:
        print(f"DEBUG: Imagen 4 Error: {e}")

    return None

async def generate_gemini_drawing(question_prompt, context_hint=""):
    """Uses Gemini 1.5 Pro to design a fresh, high-fidelity SVG/TikZ diagram based on the question prompt."""
    if not gemini_client:
        return None
    
    full_prompt = f"""### TASK:
    Design a professional educational diagram/map for a national exam question.
    QUESTION PROMPT: "{question_prompt}"
    CONTEXT: {context_hint}
    
    ### DESIGN CONSTRAINTS:
    ### MASTER CARTOGRAPHER REQUIREMENTS (SVG):
    1. Generate RAW HTML <svg> code with `viewBox="0 0 600 400"` and `width="100%"`.
    2. Use `fill="#f1f5f9"` for land and `fill="#e2e8f0"` for water bodies (Lakes/Oceans).
    3. Use `stroke="#000" stroke-width="1.5"` for international borders.
    4. Include a professional Compass Rose and a Scale Bar in the corner.
    5. Place labels using `<text>` nodes with `font-family="serif"` and `font-size="12"`.
    6. If a specific region is mentioned (e.g., 'K'), mark it with a distinct hatching pattern or a bold label.
    7. Ensure the map looks like a page from a professional geography atlas.
    
    RETURN ONLY the <svg> code. NO conversational text.
    """
    
    try:
        response = await gemini_client.aio.models.generate_content(
            model='gemini-1.5-flash',
            contents=full_prompt
        )
        drawing_code = response.text.strip()
        # Clean up markdown
        drawing_code = re.sub(r'```(?:tikz|latex|html|svg)?\s*', '', drawing_code)
        drawing_code = re.sub(r'\s*```', '', drawing_code)
        return drawing_code
    except Exception as e:
        print(f"Gemini Drawing Sync Failed: {e}")
        return None

async def generate_illustration(question_text: str, subject: str = "General", level: str = "Primary 4", custom_prompt: str = "", style: str = "png"):
    """General-purpose illustration generator using OpenAI models based on style."""
    if custom_prompt.strip():
        drawing_desc = custom_prompt.strip()
    else:
        drawing_desc = f"An educational illustration for this {subject} question: {question_text}"

    client = get_async_openai_client()

    if style == "svg":
        prompt = f"""You are an expert educational illustrator for African primary and secondary school exams.

Create a clean, professional black-and-white SVG illustration based on this description:
"{drawing_desc}"

RULES:
1. Output ONLY raw <svg> code — no markdown, no explanation, no backticks.
2. Use viewBox="0 0 500 350" (do NOT include width or height attributes, they will be handled by CSS).
3. Black strokes only (stroke="#000"), max stroke-width="2", white background.
4. Keep it simple, clear, and appropriate for a printed exam paper.
5. All text labels must use font-family="Arial, sans-serif" font-size="11".
6. Do NOT include any colour fills except very light grey (#f5f5f5) for backgrounds.

Output the SVG code now:"""
        try:
            print(f"DEBUG: Calling GPT-4o for SVG: {drawing_desc[:30]}...")
            res = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            svg = res.choices[0].message.content.strip()
            svg = re.sub(r'^```(?:svg|html|xml)?\s*', '', svg)
            svg = re.sub(r'\s*```$', '', svg)
            if not svg.strip().startswith('<svg'):
                return None
            
            # Strip rogue width/height attributes that break responsive scaling
            svg = re.sub(r'(<svg[^>]*?)\s+width=["\'][^"\']*["\']', r'\1', svg, count=1)
            svg = re.sub(r'(<svg[^>]*?)\s+height=["\'][^"\']*["\']', r'\1', svg, count=1)
            # Inject strict dimensional limits
            svg = re.sub(r'<svg', r'<svg width="100%" height="250" style="max-width:500px; max-height:250px; display:block; margin:15px auto;"', svg, count=1)
            
            return svg
        except Exception as e:
            print(f"generate_illustration error (SVG): {e}")
            return None

    if style == "raw":
        full_prompt = drawing_desc
    else:
        style_modifiers = {
            "png": "Style: clean black-and-white textbook illustration, pure white background, sharp black outlines, no shading. Highly accurate, educational.",
            "sketch": "Style: rough hand-drawn pencil sketch, educational outline on white paper, no color.",
            "realistic": "Style: hyper-realistic high-resolution photograph, well-lit, academic textbook style.",
            "3d": "Style: 3D render, isometric projection, clean soft lighting, educational and professional.",
        }
        style_prompt = style_modifiers.get(style, style_modifiers["png"])
        full_prompt = (
            f"A professional academic diagram for a {level} exam. "
            f"Description: {drawing_desc}. "
            f"{style_prompt}"
        )

    filename = f"img_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        print(f"DEBUG: Calling DALL-E ({style}) for: {drawing_desc[:30]}...")
        # First attempt with DALL-E 3
        try:
            res = await client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
        except Exception as de:
            # Check if it's a "model not found" error
            if "model" in str(de).lower() and "exist" in str(de).lower():
                print("DEBUG: DALL-E 3 not available on this key. Falling back to DALL-E 2...")
                res = await client.images.generate(
                    model="dall-e-2",
                    prompt=full_prompt,
                    n=1,
                    size="1024x1024",
                    response_format="b64_json"
                )
            else:
                raise de

        image_b64 = res.data[0].b64_json
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
            
        print(f"DEBUG: DALL-E Success -> {filename}")
        return f"/generated/{filename}"
    except Exception as e:
        print(f"generate_illustration error (DALL-E): {e}")
        print("DEBUG: Falling back to Pollinations AI (Free API)...")
        import urllib.parse
        try:
            encoded_prompt = urllib.parse.quote(full_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            # Use a shorter timeout for the free fallback
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"DEBUG: Pollinations Fallback Success -> {filename}")
                return f"/generated/{filename}"
            else:
                print(f"DEBUG: Pollinations returned status code {response.status_code}")
        except Exception as ge:
            print(f"DEBUG: Pollinations Fallback Error: {ge}")
        return None

def get_openai_client():
    """Retrieves API Key from environment to instantiate OpenAI client safely."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the .env file in the root directory.")
    return OpenAI(api_key=api_key)

def get_async_openai_client():
    """Retrieves API Key from environment to instantiate Async OpenAI client safely."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the .env file in the root directory.")
    import httpx
    return AsyncOpenAI(api_key=api_key, timeout=httpx.Timeout(120.0))

def process_tikz_safeguard(raw_text):
    """Ensures that any generated TikZ code is safely wrapped for TikZJax engine."""
    clean_text = re.sub(r'```(?:tikz|latex)?\s*(\\begin\{tikzpicture\})', r'\1', raw_text)
    clean_text = re.sub(r'(\\end\{tikzpicture\})\s*```', r'\1', clean_text)
    clean_text = re.sub(r'<script type="text/tikz">\s*(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\s*</script>', r'\1', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', r'<script type="text/tikz">\n\1\n</script>', clean_text, flags=re.DOTALL)
    return clean_text

async def generate_ai_content(mode, level, subject, term, num_questions, difficulty="Balanced", ai_model="gpt-4o", internal="Internal", topic="", pedagogy_hint=None, force_images=False):
    """
    Parallel question generation with pedagogical alignment.
    """
    client = get_async_openai_client()
    syllabus_rows = retrieve_syllabus_context(subject, level, term, topic)
    year = "2026"

    # ── OVERRIDE WITH OFFICIAL UNEB PAPER STRUCTURE ──
    ps = get_paper_structure(subject, level)
    official_total = get_total_questions(subject, level)
    # Use official count unless caller specifically requested more (e.g. for practice)
    num_questions = official_total if official_total > 0 else num_questions

    math_subjects = ["Math", "Physics", "Science"]
    is_math = any(s in subject for s in math_subjects)
    tikz_rule = "- TikZ (Construction): For Maths/Physics, use precise coordinates for geometry." if is_math else ""

    # ── 1. COGNITIVE AGE PROFILING ──
    age_profile = "General Audience"
    if "Baby" in level or "Middle" in level or "Top" in level:
        age_profile = "Ages 3-5 (Pre-operational stage, extremely simple visual tasks)"
    elif "Primary 1" in level or "Primary 2" in level or "Primary 3" in level:
        age_profile = "Ages 6-8 (Early concrete operational, foundational literacy/numeracy)"
    elif "Primary 4" in level or "Primary 5" in level:
        age_profile = "Ages 9-11 (Concrete operational, basic application and reasoning)"
    elif "Primary 6" in level or "Primary 7" in level:
        age_profile = "Ages 12-13 (Late concrete operational, preparation for national exams)"
    elif "Senior 1" in level or "Senior 2" in level:
        age_profile = "Ages 14-15 (Early formal operational, abstract reasoning begins)"
    elif "Senior 3" in level or "Senior 4" in level:
        age_profile = "Ages 16-17 (Formal operational, complex analysis, O-Level standards)"
    elif "Senior 5" in level or "Senior 6" in level:
        age_profile = "Ages 18+ (Advanced formal operational, university-prep A-Level standards)"

    # ── 2. AUTHORIZED TOPICS ENFORCEMENT ──
    authorized_topics = []
    from core.syllabus_master import MASTER_SYLLABUS
    if subject in MASTER_SYLLABUS and level in MASTER_SYLLABUS[subject]:
        authorized_topics = MASTER_SYLLABUS[subject][level]
    authorized_topics_str = ", ".join(authorized_topics) if authorized_topics else "General Subject Knowledge"

    if mode == "Lesson Notes":
        prompt = f"""### LESSON NOTES PROTOCOL - {subject.upper()} | {level} | {term}
You are an expert master teacher and curriculum designer.
Topic Focus: {topic or 'A key topic from the syllabus'}
Syllabus Context (RAG): {syllabus_rows}

### PEDAGOGICAL CONSTRAINTS:
1. TARGET AUDIENCE: {age_profile}. Ensure the tone and depth perfectly match this cognitive stage.
2. FORMAT: Generate comprehensive, engaging, step-by-step Lesson Notes for the teacher to deliver in class.

### FORMATTING PROTOCOL:
- Return ONLY a valid JSON object.
- Include a list of 'sections', where each section represents a phase of the lesson (e.g., Objectives, Introduction, Main Content, Examples, Conclusion, Evaluation).

Output JSON structure:
{{
  "title": "{topic or 'Lesson Notes'}",
  "sections": [
    {{
      "heading": "Lesson Objectives",
      "content": "By the end of this lesson, learners should be able to... (use HTML <ul> for lists)"
    }},
    {{
      "heading": "Introduction",
      "content": "Rich instructional content formatted in HTML (use <b>, <i>, <ul>, etc.)"
    }}
  ]
}}
"""
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a professional master teacher. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            if "sections" not in data:
                data["sections"] = [{"heading": "Lesson Content", "content": str(data)}]
            return data, json.dumps(data), f"{subject} {level} - Lesson Notes"
        except Exception as e:
            print(f"Lesson Notes generation error: {e}")
            fallback = {"sections": [{"heading": "Error", "content": "Failed to generate lesson notes."}]}
            return fallback, json.dumps(fallback), "Error"

    elif mode == "Schemes of Work":
        prompt = f"""### SCHEME OF WORK PROTOCOL - {subject.upper()} | {level} | {term}
You are an expert master teacher and Head of Department.
Syllabus Context (RAG): {syllabus_rows}

### PEDAGOGICAL CONSTRAINTS:
1. TARGET AUDIENCE: {age_profile}.
2. FORMAT: Generate a comprehensive, 4-week Scheme of Work (as an example timeframe) for the selected topic or general term syllabus.

### FORMATTING PROTOCOL:
- Return ONLY a valid JSON object.
- Include a list of 'weeks', where each week has a 'week_number', 'topic', 'objectives', 'activities', and 'resources'.

Output JSON structure:
{{
  "title": "Scheme of Work - {subject} ({term})",
  "weeks": [
    {{
      "week_number": "Week 1",
      "topic": "Subtopic Name",
      "objectives": "Learners should be able to... (HTML format)",
      "activities": "Teacher will... Learners will... (HTML format)",
      "resources": "Textbooks, charts, etc. (HTML format)"
    }}
  ]
}}
"""
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a Head of Department. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            if "weeks" not in data:
                data["weeks"] = [{"week_number": "Error", "topic": "N/A", "objectives": "N/A", "activities": str(data), "resources": "N/A"}]
            return data, json.dumps(data), f"{subject} {level} - Scheme of Work"
        except Exception as e:
            print(f"Scheme of Work generation error: {e}")
            fallback = {"weeks": [{"week_number": "Error", "topic": "N/A", "objectives": "Failed to generate", "activities": "", "resources": ""}]}
            return fallback, json.dumps(fallback), "Error"

    async def _generate_chunk(chunk_size: int, start_num: int):
        prompt = f"""### NATIONAL EXAM PROTOCOL - {subject.upper()} | {level} | {term}
You are an expert curriculum designer for the National Examinations Board.
Topic Focus: {topic or 'Full Syllabus'}
Syllabus Context (RAG): {syllabus_rows}

### PEDAGOGICAL & COGNITIVE CONSTRAINTS:
1. TARGET AUDIENCE: {age_profile}. You MUST write questions that perfectly match this cognitive development stage.
2. STRICT COGNITIVE CEILING: The authorized topics for {level} {subject} are: [{authorized_topics_str}]. You MUST NOT generate any question, concept, or vocabulary outside of these topics. If a topic is not listed here, it is too advanced and is strictly forbidden.
3. BLOOM'S TAXONOMY: 40% Knowledge, 40% Application, 20% Synthesis/Evaluation.
4. ITEM RIGOR: Language must be formal, precise, and accessible strictly to the {level} level.

### FORMATTING PROTOCOL:
- Return ONLY a valid JSON object.
- DO NOT use placeholders like '[Map here]'.
{tikz_rule}
- TikZ (Question): If a diagram is part of the question for the student to look at, put it in "tikz_code".
- STUDENT DRAWING SPACE: Semantically assess the question. If it explicitly requires the student to draw, sketch, plot, or construct something on the paper, set "needs_student_drawing": true and "tikz_code": null. Otherwise, set it to false.
- TikZ (Answer): If the student must DRAW a diagram, put the AI-generated solution drawing in the 'answer' field for the Teacher's marking guide.

Generate {chunk_size} unique, high-fidelity exam questions. Start numbering exactly from {start_num}.
Output JSON structure:
{{
  "questions": [
    {{
      "number": {start_num},
      "topic": "Topic Name",
      "text": "Question text...",
      "marks": 1,
      "answer": "Correct answer with marking steps...",
      "tikz_code": null,
      "needs_student_drawing": false
    }}
  ]
}}
"""
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

    # ── 3. PARALLEL CHUNKING ──
    try:
        chunk_size = 10
        tasks = []
        for i in range(0, num_questions, chunk_size):
            size = min(chunk_size, num_questions - i)
            tasks.append(_generate_chunk(size, i + 1))
        
        chunk_results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_questions = []
        for chunk in chunk_results:
            all_questions.extend(chunk)
            
        # Re-number just to be safe
        for i, q in enumerate(all_questions):
            q["number"] = i + 1

        # ── 4. POST-PROCESS TikZ SAFETY NET ──
        for q in all_questions:
            text = q.get("text", "").lower()
            tikz = q.get("tikz_code")
            draw_keywords = ["draw", "construct", "sketch", "graph", "plot"]
            
            if any(k in text for k in draw_keywords) and tikz and "<img" not in str(tikz).lower():
                ans = q.get("answer", "")
                q["answer"] = f"{ans}\n\n**Expected Construction:**\n{process_tikz_safeguard(tikz)}"
                q["tikz_code"] = None
            elif tikz and "<img" not in str(tikz).lower():
                q["tikz_code"] = process_tikz_safeguard(tikz)

        data = {"questions": all_questions[:num_questions]}
        raw_str = json.dumps(data)
        title = f"{subject} {level} - {term} {year}"
        return data, raw_str, title
        
    except Exception as e:
        print(f"Generation Engine Failure: {e}")
        import traceback; traceback.print_exc()
        raise

async def regenerate_single_question(subject: str, level: str, topic: str = "", instruction: str = ""):
    """Regenerates a single question based on teacher instructions or specific topic."""
    client = get_async_openai_client()
    
    # 1. Get Authorized Topics
    from core.syllabus_master import MASTER_SYLLABUS
    authorized_topics = []
    if subject in MASTER_SYLLABUS and level in MASTER_SYLLABUS[subject]:
        authorized_topics = MASTER_SYLLABUS[subject][level]
    authorized_topics_str = ", ".join(authorized_topics) if authorized_topics else "General Subject Knowledge"

    # 2. Build the instruction prompt
    refine_instruction = ""
    if instruction.strip():
        refine_instruction = f"TEACHER INSTRUCTION: {instruction}\n"
    if topic.strip():
        refine_instruction += f"MANDATORY TOPIC FOCUS: {topic}\n"

    prompt = f"""### NATIONAL EXAM PROTOCOL - REGENERATE SINGLE QUESTION
You are an expert curriculum designer for the National Examinations Board.
Subject: {subject}
Level: {level}
Authorized Topics for {level}: [{authorized_topics_str}] (DO NOT EXCEED THESE)

{refine_instruction}
Your task is to generate exactly ONE high-quality question that fits the parameters above.

### FORMATTING PROTOCOL:
- Return ONLY a valid JSON object.
- DO NOT use placeholders like '[Map here]'.

Output JSON structure:
{{
  "question": {{
    "number": 1,
    "topic": "Topic Name",
    "text": "Question text...",
    "marks": 2,
    "answer": "Correct answer with marking steps...",
    "tikz_code": null,
    "needs_student_drawing": false
  }}
}}
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional examiner. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        return data.get("question", None)
    except Exception as e:
        print(f"regenerate_single_question error: {e}")
        import traceback; traceback.print_exc()
        return None

async def analyze_pedagogy(content_raw):
    """Deep audit of syllabus coverage and Bloom's depth."""
    client = get_async_openai_client()
    prompt = f"Analyze this exam for curriculum alignment and Bloom's Taxonomy. Return a brief summary and a percentage score for 'Syllabus Saturation'. CONTENT: {content_raw}"
    try:
        res = await client.chat.completions.create(model="gpt-4o", messages=[{{"role":"user","content":prompt}}])
        return res.choices[0].message.content
    except:
        return "Audit service unavailable."

async def generate_flow_step(step_idx, context, subject):
    """Predictive generation of the next logical step in an exam structure."""
    client = get_async_openai_client()
    prompt = f"Given context: {context}. Generate the next exam question (Question {step_idx}) for {subject}. Output JSON format."
    try:
        res = await client.chat.completions.create(
            model="gpt-4o", 
            messages=[{{"role":"user","content":prompt}}],
            response_format={{"type": "json_object"}}
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {{"text": "Failed to predict next step."}}

async def chat_response(message, history):
    """Chat-based pedagogical assistant."""
    client = get_async_openai_client()
    messages = [{{ "role": "system", "content": "You are the EduQuest Pedagogical Assistant. Help the teacher refine their exam." }}]
    for h in history:
        messages.append({{ "role": h["role"], "content": h["content"] }})
    messages.append({{ "role": "user", "content": message }})
    
    try:
        res = await client.chat.completions.create(model="gpt-4o", messages=messages)
        return res.choices[0].message.content
    except Exception as e:
        return f"Chat Error: {e}"

async def generate_scenario_content(subject, level, theme, force_images=False):
    """
    Generates a competency-based exam rooted in a specific real-world scenario.
    """
    client = get_async_openai_client()
    
    prompt = f"""
### COMPETENCY-BASED EXAMINATION (CBE) - {subject.upper()}
LEVEL: {level}
REAL-WORLD SCENARIO: {theme}

### INSTRUCTIONS:
1. First, write a detailed 'Scenario Narrative' (2-3 paragraphs) describing a real-world situation related to {theme}.
2. Then, generate 5 higher-order questions that require the student to solve problems BASED ON the narrative.
3. Incorporate Blooms Taxonomy (Analysis and Application).

Output JSON:
{{
  "scenario_text": "...",
  "questions": [
    {{ "number": 1, "text": "...", "marks": 5, "answer": "...", "tikz_code": "..." }}
  ]
}}
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        # ── AI ILLUSTRATION REFINEMENT ──
        is_organic = any(s in subject for s in ["Geography", "Social Studies", "Biology", "SST"])
        if "questions" in data:
            if force_images:
                draw_tasks = data["questions"]
            elif is_organic:
                draw_tasks = [q for q in data["questions"] if any(k in q.get("text", "").lower() for k in ["map", "diagram", "sketch", "outline"])]
            else:
                draw_tasks = []

            if draw_tasks:
                async def refine_q(q):
                    result = await generate_ai_image(q["text"], subject, level)
                    if result:
                        if result.strip().startswith("<svg"):
                            q["tikz_code"] = result
                        else:
                            q["tikz_code"] = f'<img src="{result}" style="width:100%; max-width:550px; display:block; margin:15px auto;"/>'

                await asyncio.gather(*(refine_q(q) for q in draw_tasks))

        if "questions" in data:
            for q in data["questions"]:
                tikz = q.get("tikz_code")
                if tikz:
                    q["tikz_code"] = process_tikz_safeguard(tikz)

        return json.dumps(data)
    except Exception as e:
        print(f"Scenario Engine Failure: {e}")
        return json.dumps({{"error": str(e)}})
