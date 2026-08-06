import os
import re
import json, asyncio, uuid
import base64
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI, AsyncOpenAI
from google import genai
from core.db_engine import retrieve_syllabus_context, retrieve_exam_rubric
from core.map_library import get_best_map
from core.paper_structure import get_paper_structure, get_total_questions
from core.syllabus_master import MASTER_SYLLABUS
import requests
import uuid

# ── Gemini Draftsman Initialization ──
google_key = os.environ.get("GOOGLE_API_KEY")
if google_key:
    genai_client = genai.Client(api_key=google_key)
else:
    genai_client = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def generate_ai_image(prompt, subject="Geography", level=""):
    """Library-first map generation: SVG library → chatgpt-image fallback."""
    # ── STEP 1: Check curated SVG library for known maps ──
    svg = get_best_map(prompt)
    if svg:
        print(f"DEBUG: SVG Library match found for [{subject}]")
        return svg  # Return raw SVG string directly

    # ── STEP 2: chatgpt-image fallback for unknown map requests ──
    client = get_async_openai_client()
    filename = f"map_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Enriched prompt for better accuracy depending on age group
    if "Class" in level:
        full_prompt = (
            f"A simple, bold black-and-white line drawing for an ECD/nursery worksheet: {prompt}. "
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
        print(f"DEBUG: chatgpt-image (gpt-image-1) fallback for [{subject}]...")
        response = await client.images.generate(
            model="gpt-image-1",
            prompt=full_prompt,
            n=1,
            size="1024x1024",
        )
        img_data = response.data[0]
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            image_bytes = base64.b64decode(img_data.b64_json)
        elif hasattr(img_data, "url") and img_data.url:
            import urllib.request
            with urllib.request.urlopen(img_data.url) as resp:
                image_bytes = resp.read()
        else:
            print("DEBUG: chatgpt-image returned no images.")
            return None

        with open(save_path, "wb") as f:
            f.write(image_bytes)
        print(f"DEBUG: chatgpt-image Success -> {filename}")
        return f"/api/generated/{filename}"
    except Exception as e:
        print(f"DEBUG: chatgpt-image Error: {e}")

    return None

async def generate_gemini_drawing(question_prompt, context_hint=""):
    """Uses Gemini 1.5 Pro to design a fresh, high-fidelity SVG/TikZ diagram based on the question prompt."""
    if not genai_client:
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
        # Use the global genai_client with async support
        response = await genai_client.aio.models.generate_content(
            model='gemini-3.5-flash',
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
    """
    General-purpose illustration generator using OpenAI models based on style.
    Incorporates MD5 caching to save time and API quota for both SVG code and PNG files.
    """
    if custom_prompt.strip():
        drawing_desc = custom_prompt.strip()
    else:
        drawing_desc = f"An educational illustration for this {subject} question: {question_text}"

    import hashlib
    # Compute unique cache key for manual drawings
    cache_key_src = f"{question_text}|{subject}|{level}|{custom_prompt}|{style}"
    cache_hash = hashlib.md5(cache_key_src.encode("utf-8")).hexdigest()
    
    cache_file = os.path.join(BASE_DIR, "frontend", "public", "generated", "illustration_cache.json")
    cache_data = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}
            
    if cache_hash in cache_data:
        cached_val = cache_data[cache_hash]
        if style == "svg":
            print(f"DEBUG: [ILLUSTRATION CACHE HIT] Reusing cached SVG string.")
            return cached_val
        else:
            cached_path = os.path.join(BASE_DIR, "frontend", "public", "generated", cached_val)
            if os.path.exists(cached_path):
                print(f"DEBUG: [ILLUSTRATION CACHE HIT] Reusing cached image: {cached_val}")
                return f"/api/generated/{cached_val}"

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
            
            # Save SVG in cache
            cache_data[cache_hash] = svg
            try:
                with open(cache_file, "w") as f:
                    json.dump(cache_data, f, indent=2)
            except Exception as ce:
                print(f"Failed to write illustration cache index: {ce}")

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
            f"A precise, educational academic diagram/illustration for a {level} {subject} exam question.\n\n"
            f"EXAM QUESTION: \"{question_text}\"\n"
            f"DESCRIPTION HINT: {drawing_desc}\n\n"
            "STRICT DESIGN & PEDAGOGICAL RULES:\n"
            "1. The illustration MUST be drawn specifically to enable the student/learner to answer the exam question correctly. It must visually show the setup, parameters, or objects mentioned in the question.\n"
            "2. PEDAGOGICAL PROTECTION: The diagram MUST NOT show the final solved answer to the question. It must only depict the initial problem setup, shape variables, or unknown parameters (e.g. if the question asks to find the hypotenuse, label that side as 'x' or '?', never label it with the resolved final value). The student must do the actual cognitive work to solve the question.\n"
            f"3. {style_prompt}\n"
            "4. Render clean black lines on a pure white background. Keep all text labels in standard horizontal Arial/Helvetica font and 100% legible. No stylized/distorted letters, no watermarks, no decorative frames.\n"
            "5. CRITICAL TEXT BAN: DO NOT write or include the actual exam question text inside the image. Only include short, necessary labels (like names of parts, numbers, or short words directly relevant to the illustration)."
        )

    filename = f"img_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        print(f"DEBUG: Calling chatgpt-image (gpt-image-1) for: {drawing_desc[:30]}...")
        res = await client.images.generate(
            model="gpt-image-1",
            prompt=full_prompt,
            n=1,
            size="1024x1024",
        )
        img_data = res.data[0]
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            image_bytes = base64.b64decode(img_data.b64_json)
        elif hasattr(img_data, "url") and img_data.url:
            import urllib.request
            with urllib.request.urlopen(img_data.url) as resp:
                image_bytes = resp.read()
        else:
            return None

        with open(save_path, "wb") as f:
            f.write(image_bytes)
            
        # Update cache index
        cache_data[cache_hash] = filename
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as ce:
            print(f"Failed to write illustration cache index: {ce}")
            
        print(f"DEBUG: chatgpt-image Success & cached -> {filename}")
        return f"/api/generated/{filename}"
    except Exception as e:
        print(f"generate_illustration error (chatgpt-image): {e}")
        return None

async def generate_exam_diagram(diagram_description: str, subject: str, level: str, question_text: str = "", answer_text: str = ""):
    """
    Calls gpt-image-1 to produce a clean, black-and-white UNEB-style exam diagram.
    Uses the question and answer context to ensure the diagram is mathematically and educationally accurate.
    Incorporates MD5 caching to prevent duplicate generation cost and latency.
    """
    import hashlib
    # Compute unique cache key
    cache_key_src = f"{diagram_description}|{question_text}|{answer_text}|{subject}|{level}"
    cache_hash = hashlib.md5(cache_key_src.encode("utf-8")).hexdigest()
    
    cache_file = os.path.join(BASE_DIR, "frontend", "public", "generated", "diagram_cache.json")
    cache_data = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}
            
    if cache_hash in cache_data:
        cached_filename = cache_data[cache_hash]
        cached_path = os.path.join(BASE_DIR, "frontend", "public", "generated", cached_filename)
        if os.path.exists(cached_path):
            print(f"DEBUG: [DIAGRAM CACHE HIT] Reusing diagram: {cached_filename}")
            return f"/api/generated/{cached_filename}"

    client = get_async_openai_client()

    question_text = question_text or ""
    answer_text = answer_text or ""

    prompt = (
        f"A precise, mathematically accurate, clean black-and-white academic diagram/illustration for a {level} {subject} exam question.\n\n"
        f"EXAM QUESTION TEXT: \"{question_text}\"\n"
        f"CORRECT ANSWER: \"{answer_text}\"\n"
        f"DIAGRAM DESCRIPTION: {diagram_description}\n\n"
        "STRICT DESIGN & ACCURACY RULES:\n"
        "1. The diagram MUST accurately depict the values, lines, boundaries, and variables mentioned in the question so the student can use this diagram to find the correct answer.\n"
        "2. The diagram MUST be geometrically perfect (e.g. if the question mentions a right angle, show a clear right-angled shape; if it is a Venn diagram, draw clean, perfect overlapping circles).\n"
        "3. Style: clean textbook outline line-art only, pure white background, sharp black lines (no colour, no grey gradients, no artistic shadows/shading).\n"
        "4. Text Labels: Any labels (like A, B, 5cm, 90°) must be written in a simple standard sans-serif font (like Arial/Helvetica) and must be perfectly horizontal and 100% readable. No handwriting, no cursive, no distorted letters.\n"
        "5. No decorative borders, no watermarks, no external explanations.\n"
        "6. PEDAGOGICAL SAFETY (CRITICAL): The diagram MUST NOT reveal or label the final correct answer (\"{answer_text}\") anywhere in the visual. The diagram should only show the setup, question boundaries, and unknown variables (e.g. if the question asks to find side 'x', that side MUST be labeled in the drawing as 'x' or '?', NOT as its resolved final numerical value). The student must do the actual math to solve it.\n"
        "7. CRITICAL TEXT BAN: DO NOT write or include the actual exam question text inside the image. Only include mathematical/diagram labels (like A, B, 5cm, 90°) directly relevant to the drawing."
    )

    filename = f"diag_{uuid.uuid4().hex[:10]}.png"
    save_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        print(f"DEBUG: gpt-image-1 diagram with question context for Q: {question_text[:50]}...")
        res = await client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        if not res or not res.data:
            print("DEBUG: gpt-image-1 returned no data for diagram.")
            return None
        img_data = res.data[0]
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            image_bytes = base64.b64decode(img_data.b64_json)
        elif hasattr(img_data, "url") and img_data.url:
            import urllib.request
            with urllib.request.urlopen(img_data.url) as resp:
                image_bytes = resp.read()
        else:
            print("DEBUG: gpt-image-1 returned no data for diagram.")
            return None

        with open(save_path, "wb") as f:
            f.write(image_bytes)

        # Update cache index
        cache_data[cache_hash] = filename
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as ce:
            print(f"Failed to write diagram cache index: {ce}")

        print(f"DEBUG: Diagram saved & cached -> {filename}")
        return f"/api/generated/{filename}"
    except Exception as e:
        print(f"generate_exam_diagram error: {e}")
        return None

async def _fix_question_integrity(client, question, feedback):
    """Asks the model to fix a specific question based on integrity feedback."""
    prompt = f"""You are an Exam Integrity Auto-Corrector.
The following generated question failed our integrity checks:
{feedback}

Original Question JSON:
{json.dumps(question, indent=2)}

Please fix the issues and output ONLY the completely corrected question JSON object. Keep all other fields intact.
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a JSON fixer. Output ONLY valid JSON representing the corrected question."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Fix loop error: {e}")
        return None

async def generate_diagrams_for_questions(questions: list, subject: str, level: str) -> list:
    """
    Post-generation pass: for any question with a non-null diagram_description,
    call gpt-image-1 and inject the returned URL as diagram_url.
    Runs all diagram calls concurrently with asyncio.gather.
    Staggers any non-cached API requests to avoid rate limit locks.
    """
    import asyncio

    async def process_one(q, delay: float = 0.0):
        desc = q.get("diagram_description")
        qtext = q.get("text", "")
        qans = q.get("answer", "")
        if desc and isinstance(desc, str) and desc.strip():
            from core.telemetry import emit_progress
            emit_progress("DIAGRAM AGENT", f"Drafting illustration for Q{q.get('number', '?')}...")
            if delay > 0:
                await asyncio.sleep(delay)
            
            from core.integrity_agent import check_tier3_vision
            client = get_async_openai_client()
            
            # Allow 1 retry for images
            url = await generate_exam_diagram(desc.strip(), subject, level, qtext, qans)
            if url:
                # Calculate absolute path for vision check
                filename = url.split("/")[-1]
                abs_path = os.path.join(BASE_DIR, "frontend", "public", "generated", filename)
                
                # Tier 3 Audit
                emit_progress("VISION AUDIT", f"Auditing diagram for Q{q.get('number', '?')} with GPT-4o...")
                t3_pass, t3_feedback = await check_tier3_vision(client, abs_path, qtext)
                if not t3_pass:
                    print(f"Q{q.get('number', '?')} Image failed Tier 3 Vision Audit: {t3_feedback}")
                    emit_progress("VISION FAILED", f"Redrawing Q{q.get('number', '?')} diagram. Reason: {t3_feedback}")
                    # Try to regenerate once with the feedback appended
                    refined_desc = f"{desc.strip()}\nCRITICAL CORRECTION TO PREVIOUS ATTEMPT: {t3_feedback}"
                    new_url = await generate_exam_diagram(refined_desc, subject, level, qtext, qans)
                    if new_url:
                        url = new_url
                        print(f"Q{q.get('number', '?')} Image auto-fixed via Vision Audit!")
                        emit_progress("VISION PASSED", f"Q{q.get('number', '?')} diagram auto-repaired successfully.")
                else:
                    emit_progress("VISION PASSED", f"Q{q.get('number', '?')} diagram passed strict audit.")
                
                q["diagram_url"] = url
                print(f"  ✓ Q{q.get('number')} diagram: {url}")
            else:
                q["diagram_url"] = None
        return q

    # Only apply stagger delay to questions that actually require diagram generation
    tasks = []
    stagger_count = 0
    for q in questions:
        desc = q.get("diagram_description")
        if desc and isinstance(desc, str) and desc.strip():
            tasks.append(process_one(q, delay=stagger_count * 0.5))
            stagger_count += 1
        else:
            tasks.append(process_one(q, delay=0.0))

    results = await asyncio.gather(*tasks)
    return list(results)

def get_openai_client():
    """Retrieves API Key from environment to instantiate OpenAI client safely."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        load_dotenv(override=True)
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the .env file in the root directory.")
    return OpenAI(api_key=api_key)

def get_async_openai_client():
    """Retrieves API Key from environment to instantiate Async OpenAI client safely."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        load_dotenv(override=True)
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the .env file in the root directory.")
    import httpx
    return AsyncOpenAI(
        api_key=api_key,
        timeout=httpx.Timeout(120.0),
        http_client=httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=50, keepalive_expiry=30.0),
            timeout=httpx.Timeout(120.0)
        )
    )

def process_tikz_safeguard(raw_text):
    """Ensures that any generated TikZ code is safely wrapped for TikZJax engine."""
    if not raw_text:
        return raw_text
    
    if "\\begin{tikzpicture}" not in raw_text:
        if any(cmd in raw_text for cmd in ["\\draw", "\\node", "\\fill", "\\path", "\\coordinate"]):
            clean_text = re.sub(r'```(?:tikz|latex)?(.*?)```', r'\1', raw_text, flags=re.DOTALL)
            raw_text = f"\\begin{{tikzpicture}}\n{clean_text.strip()}\n\\end{{tikzpicture}}"

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
    rubric_context = retrieve_exam_rubric(subject, level, topic)
    year = "2026"

    # ── OVERRIDE WITH OFFICIAL UNEB PAPER STRUCTURE ──
    ps = get_paper_structure(subject, level)
    official_total = get_total_questions(subject, level)
    sec_a_count = ps.get("sec_a_count", 0)
    # Use official count unless caller specifically requested more (e.g. for practice)
    num_questions = official_total if official_total > 0 else num_questions

    math_subjects = ["Math", "Physics", "Science"]
    is_math = any(s in subject for s in math_subjects)
    is_ecd = any(k in level for k in ["Baby", "Middle", "Top", "Primary 1", "Primary 2", "Primary 3", "Nursery", "Kindergarten", "P1", "P2", "P3", "ECD"])

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
    from core.syllabus_master import MASTER_SYLLABUS, get_syllabus_graph
    if subject in MASTER_SYLLABUS and level in MASTER_SYLLABUS[subject]:
        authorized_topics = MASTER_SYLLABUS[subject][level]
    authorized_topics_str = ", ".join(authorized_topics) if authorized_topics else "General Subject Knowledge"

    # ── EXAM BLUEPRINT GENERATION ──
    from core.exam_blueprint import generate_exam_blueprint
    exam_blueprint = generate_exam_blueprint(subject, level, term, num_questions, topic)

    # ── PEDAGOGICAL KNOWLEDGE GRAPH (PKG) ENRICHMENT ──
    pkg = get_syllabus_graph()
    pkg_skills = []
    pkg_prereqs = []
    active_topics = [topic] if (topic and topic in authorized_topics) else authorized_topics
    for t in active_topics:
        node = pkg.get_node(subject, level, t)
        if node:
            if node.get("skills"):
                pkg_skills.extend(node["skills"])
            prereq_list = pkg.get_prerequisites_recursive(subject, level, t)
            for ps_s, pl_s, pt_s in prereq_list:
                pkg_prereqs.append(f"{pt_s} (from {pl_s} {ps_s})")

    pkg_skills_str = ", ".join(pkg_skills) if pkg_skills else "General curriculum skill mastery"
    pkg_prereqs_str = ", ".join(list(set(pkg_prereqs))) if pkg_prereqs else "None"

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

    async def _generate_chunk(chunk_size: int, start_num: int, stagger_delay: float = 0.0, target_level: str = None, target_syllabus_rows: str = None):
        _level = target_level or level
        _syllabus_rows = target_syllabus_rows or syllabus_rows
        # Generate a perfectly aligned blueprint for this specific class level chunk
        from core.exam_blueprint import generate_exam_blueprint
        chunk_blueprint = generate_exam_blueprint(subject, _level, term, chunk_size, topic)
        chunk_mapping = "\n".join([f"Q{start_num + i}: {chunk_blueprint.get(f'Q{i+1}', 'General Knowledge')}" for i in range(chunk_size)])
        
        if stagger_delay > 0:
            import asyncio
            await asyncio.sleep(stagger_delay)
        import re
        is_lower_primary = False
        is_foundation = False
        is_transitional = False
        if "Primary" in level:
            m = re.search(r'\d+', level)
            if m:
                level_num = int(m.group())
                if level_num <= 4:
                    is_lower_primary = True
                    if level_num <= 2:
                        is_foundation = True
                    else:
                        is_transitional = True
        elif any(x in level for x in ["Nursery", "ECD", "Baby", "Middle", "Top"]):
            is_lower_primary = True
            is_foundation = True
                
        if is_foundation:
            layout_instruction = f"CRITICAL REQUIREMENT: For this Foundation class (P1-P2/Nursery), you MUST heavily generate a mix of 'fill_blank', 'matching', and 'vertical_math' types. DO NOT use 'type': 'mcq' or 'structured' under any circumstances! Keep it extremely simple.\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif is_transitional:
            layout_instruction = f"CRITICAL REQUIREMENT: For this Transitional class (P3-P4), you MUST generate a mix of 'vertical_math' and 1-sentence 'short_answer' questions. You may also introduce very simple 'structured' questions (max 2 parts, e.g., a, b). DO NOT use 'type': 'mcq' under any circumstances!\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif "Primary" in level:
            # Authentic Primary (P4-P7) exams do NOT use multiple choice. Section A is short answer.
            if start_num <= sec_a_count:
                layout_instruction = f"CRITICAL REQUIREMENT: Authentic {level} exams strictly prohibit Multiple Choice Questions. DO NOT use 'type': 'mcq' under any circumstances! For Section A (Q1 to {sec_a_count}), you MUST ONLY generate 'short_answer' questions. Section A questions must be single-part short-answer ONLY. DO NOT generate sub-questions (a, b, c) unless generating for Section B.\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            else:
                layout_instruction = f"CRITICAL REQUIREMENT: You are generating SECTION B. You MUST indicate this by generating 'structured' questions with multiple sub-parts (e.g. a, b, c) following the structure of the original papers. DO NOT use 'type': 'mcq' under any circumstances!\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif "Senior 4" in level and subject in ["Physics", "Chemistry", "Biology", "Agriculture"]:
            # UCE Sciences use Multiple Choice for Section A
            layout_instruction = f"IMPORTANT: Authentic UCE Science exams use Multiple Choice for Section A. You MUST generate 'mcq' for Q1 to {sec_a_count}, and 'structured' for Section B.\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            mcq_routing_rule = '- If generating a Multiple Choice Question, set "type": "mcq" and provide exactly 4 options in "options": ["Option 1", "Option 2", "Option 3", "Option 4"] (Do not include A, B, C, D in the text).'
        else:
            layout_instruction = f"Generate 'short_answer' for Section A (Q1 to {sec_a_count}) and 'structured' for Section B.\n\nSTRICT TOPIC MAPPING FOR THIS CHUNK:\nYou MUST strictly follow this exact topic sequence for each question number:\n{chunk_mapping}"
            mcq_routing_rule = '- If generating a Multiple Choice Question, set "type": "mcq" and provide exactly 4 options in "options": ["Option 1", "Option 2", "Option 3", "Option 4"] (Do not include A, B, C, D in the text).'

        # ── ENGLISH SPECIFIC FORMATTING RULES ──
        if subject.lower() == "english":
            authoritative_commands_rule = '- ENGLISH GRAMMAR PERSONA: You MUST NOT use "Authoritative Commands" like "Convert this". INSTEAD, you MUST generate gap-filling exercises with a blank line "________" and put the root word in brackets. Example: "The Guest-of-Honour will get an ________ letter soon. (invite)".'
            if start_num <= sec_a_count:
                layout_instruction += "\n- ENGLISH GRAMMAR FORMAT (SECTION A): Follow the English Grammar Persona. You MUST group every 5-10 grammar questions under a shared instruction header. Set 'instruction_group' to exactly the same text (e.g. 'In questions 1-10, use the correct form of the word in brackets...') for all questions in that group."
            else:
                layout_instruction += "\n- ENGLISH COMPREHENSION FORMAT (SECTION B): For Section B, you MUST generate an authentic passage (a story, poem, dialogue, notice, table, or jumbled sentences) in the question `text`. This MUST be followed by EXACTLY 10 `sub_questions` (a, b, c, d, e, f, g, h, i, j) testing comprehension of that passage. This is critical for matching the real paper's length."
        else:
            authoritative_commands_rule = '- AUTHORITATIVE COMMANDS: Never ask open-ended questions like "What is...". You MUST use imperative commands: "Name any one...", "Give any two...", "State...", "Outline...", "Work out:".'
        # ── DIAGRAM DENSITY & COMPOSITION RULES ──
        if subject.lower() in ["mathematics", "math", "maths", "numeracy", "geography", "social studies", "science", "integrated science"]:
            layout_instruction += "\n- DIAGRAM DENSITY REQUIREMENT: You MUST include diagrams for at least 25% of the questions in this batch. For any such question, provide a detailed visual description in the 'diagram_description' field."
            layout_instruction += "\n- DIAGRAM PREAMBLE RULE: If a question requires a diagram, the question `text` MUST begin with a formal UNEB preamble (e.g., 'Study the diagram of the [object] below and use it to answer the question.')."
            layout_instruction += "\n- NO SHARED DIAGRAMS: Every question MUST be 100% self-contained. Do not write 'Use the diagram to answer questions 4 and 5'. Instead, attach the diagram to question 4, and if question 5 needs a diagram, describe a new one or make it independent."


        if is_ecd or is_lower_primary:
            prep_req = "\n5. EXTREME SIMPLICITY & VISUAL REQUIREMENT: You MUST use extremely basic vocabulary (e.g., 'Write', 'Draw', 'Count', 'Match'). Sentences MUST be under 7 words! ALMOST EVERY question MUST be visually driven. Include an explicit image placeholder like '[Picture of 3 big red mangoes]' directly in the 'text' field for the Image Agent to process!"
        else:
            prep_req = "\n5. ITEM RIGOR: Language must be direct, simple, and formal. Avoid wordy setups. Get straight to the point (e.g., \"Why does Mary eat food every day?\")."

        import yaml
        import os
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "exam_generator.yaml")
        with open(prompt_path, 'r') as f:
            prompt_template = yaml.safe_load(f)["template"]

        prompt = prompt_template.format(
            subject=subject.upper(),
            level=_level,
            term=term,
            topic=topic or 'Full Syllabus',
            syllabus_rows=_syllabus_rows,
            rubric_context=rubric_context,
            pkg_skills_str=pkg_skills_str,
            pkg_prereqs_str=pkg_prereqs_str,
            age_profile=age_profile,
            authorized_topics_str=authorized_topics_str,
            prep_req=prep_req,
            chunk_size=chunk_size,
            start_num=start_num,
            layout_instruction=layout_instruction,
            mcq_routing_rule=mcq_routing_rule,
            authoritative_commands_rule=authoritative_commands_rule
        )
        try:
            from core.telemetry import emit_progress
            emit_progress("GENERATOR AGENT", f"Drafting chunk {start_num}-{start_num+chunk_size-1}...")
            response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a professional examiner. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            questions = json.loads(response.choices[0].message.content).get("questions", [])
            
            # --- INTEGRITY AGENT: TWO-TIER VALIDATION LOOP ---
            from core.integrity_agent import check_tier1_heuristics, check_tier2_pedagogical
            
            validated_questions = []
            for q in questions:
                # Tier 1: Fast Heuristics
                emit_progress("TIER 1 CHECK", f"Running rule-based heuristic checks for Q{q.get('number', start_num)}...")
                t1_pass, t1_feedback = check_tier1_heuristics(q)
                if not t1_pass:
                    print(f"Q{q.get('number', '?')} failed Tier 1: {t1_feedback}")
                    emit_progress("TIER 1 FAILED", f"Q{q.get('number', '?')} failed heuristics. Reason: {t1_feedback}")
                    # Attempt 1 fix
                    fixed_q = await _fix_question_integrity(client, q, t1_feedback)
                    if fixed_q:
                        q = fixed_q
                        print(f"Q{q.get('number', '?')} Tier 1 auto-fixed!")
                        emit_progress("TIER 1 PASSED", f"Q{q.get('number', '?')} automatically repaired!")
                
                # Tier 2: LLM Critic
                emit_progress("TIER 2 CHECK", f"Running deep pedagogical audit on Q{q.get('number', '?')}...")
                t2_pass, t2_feedback = await check_tier2_pedagogical(client, q, subject, level)
                if not t2_pass:
                    print(f"Q{q.get('number', '?')} failed Tier 2: {t2_feedback}")
                    emit_progress("TIER 2 FAILED", f"Q{q.get('number', '?')} failed pedagogy audit. Reason: {t2_feedback}")
                    # Attempt 1 fix
                    fixed_q = await _fix_question_integrity(client, q, t2_feedback)
                    if fixed_q:
                        q = fixed_q
                        print(f"Q{q.get('number', '?')} Tier 2 auto-fixed!")
                        emit_progress("TIER 2 PASSED", f"Q{q.get('number', '?')} successfully repaired!")
                
                validated_questions.append(q)
                
            return validated_questions

        except Exception as e:
            print(f"Chunk generation error: {e}")
            return []

    # ── 3. PARALLEL CHUNKING WITH EDUMERC POLICY ──
    try:
        from core.syllabus_rules import get_edumerc_policy
        from core.db_engine import retrieve_syllabus_context
        
        policy_ratios = get_edumerc_policy(level)
        
        class_allocations = {}
        remaining_questions = num_questions
        classes_list = list(policy_ratios.items())
        
        for idx, (cls, ratio) in enumerate(classes_list):
            if idx == len(classes_list) - 1:
                alloc = remaining_questions
            else:
                alloc = int(round(num_questions * ratio))
                remaining_questions -= alloc
            if alloc > 0:
                class_allocations[cls] = alloc

        tasks = []
        current_q_num = 1
        stagger = 0.0
        
        for cls, alloc in class_allocations.items():
            cls_syllabus = retrieve_syllabus_context(subject, cls, term, topic)
            chunk_size = 10
            for i in range(0, alloc, chunk_size):
                size = min(chunk_size, alloc - i)
                tasks.append(_generate_chunk(
                    chunk_size=size,
                    start_num=current_q_num,
                    stagger_delay=stagger * 0.25,
                    target_level=cls,
                    target_syllabus_rows=cls_syllabus
                ))
                current_q_num += size
                stagger += 1
        
        chunk_results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_questions = []
        for chunk in chunk_results:
            all_questions.extend(chunk)
            
        # Re-number just to be safe
        for i, q in enumerate(all_questions):
            q["number"] = i + 1

        # ── 4. POST-PROCESS ANTI-MCQ BAN ──
        for q in all_questions:
            # Force remove MCQs if it's Primary
            if "Primary" in level and q.get("type") == "mcq":
                q["type"] = "short_answer"
                q["options"] = []

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

async def analyze_pedagogy(content_raw, subject="General", level="Standard"):
    """Deep audit of syllabus coverage and Bloom's depth."""
    client = get_async_openai_client()
    prompt = f"""
    Analyze this exam for curriculum alignment and pedagogical depth for {subject} {level}.
    Return a STRICT JSON object with the following schema:
    {{
      "summary": "Overall verdict on the exam quality...",
      "readability": 85, // Percentage score
      "time_estimate": 120, // Minutes
      "bloom": [
        {{ "subject": "Remember", "A": 40, "fullMark": 100 }},
        {{ "subject": "Understand", "A": 30, "fullMark": 100 }},
        {{ "subject": "Apply", "A": 20, "fullMark": 100 }},
        {{ "subject": "Analyze", "A": 10, "fullMark": 100 }},
        {{ "subject": "Evaluate", "A": 0, "fullMark": 100 }},
        {{ "subject": "Create", "A": 0, "fullMark": 100 }}
      ],
      "difficulty_distribution": [30, 40, 50, 70, 80, 40, 30], // Array of difficulty percentages per question
      "topic_saturation": {{
         "Topic Name": 2, // Count of questions for this topic
         "Another Topic": 1
      }},
      "missing_critical_topics": ["Topic A", "Topic B"]
    }}
    CONTENT TO ANALYZE: {content_raw}
    """
    try:
        res = await client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role":"user","content":prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"Pedagogical Audit Failure: {e}")
        return {
            "summary": "Audit service temporarily unavailable.",
            "readability": 0,
            "time_estimate": 0,
            "bloom": [],
            "difficulty_distribution": [],
            "topic_saturation": {},
            "missing_critical_topics": []
        }

from core.schema import get_nursery_schema, get_critic_schema

async def generate_nursery_exam(
    class_level: str = "Middle Class",
    learning_area: str = "LA4",
    term: str = "Term 1",
    period: str = "EOT",
    school_name: str = "EduQuest Academy",
    year: str = "2025"
) -> dict:
    """
    Generates an authentic Ugandan nursery/ECD exam matching real nursery exam style.
    class_level: 'Baby Class' | 'Middle Class' | 'Top Class'
    learning_area: 'LA1' (Relating with Others) | 'LA2' (My Environment) | 'LA3' (Taking Care of Myself) | 'LA4' (Mathematical Concepts) | 'LA5' (Language Development)
    period: 'BOT' | 'MOT' | 'EOT'
    """
    client = get_async_openai_client()

    # Import context extractor
    import random as _random
    try:
        from core.nursery_context import get_nursery_context
    except ImportError:
        get_nursery_context = lambda *a, **k: ""

    age_map = {"Baby Class": "3 – 4", "Middle Class": "4 – 5", "Top Class": "5 – 6"}
    age_range = age_map.get(class_level, "4 – 5")

    la_map = {
        "LA1": "RELATING WITH OTHERS",
        "LA2": "MY ENVIRONMENT",
        "LA3": "TAKING CARE OF MYSELF",
        "LA4": "MATHEMATICAL CONCEPTS",
        "LA5": "LANGUAGE DEVELOPMENT"
    }
    la_name = la_map.get(learning_area, "MATHEMATICAL CONCEPTS")

    period_map = {"BOT": "BEGINNING OF TERM", "MOT": "MID TERM", "EOT": "END OF TERM"}
    period_full = period_map.get(period, "END OF TERM")
    term_roman = {"Term 1": "I", "Term 2": "II", "Term 3": "III"}.get(term, "I")

    # Question type pool by class and LA
    from core.schema import load_curriculum_config
    config = load_curriculum_config()
    class_config = config["classes"].get(class_level, config["classes"]["Middle Class"])
    
    if learning_area == "LA4":
        q_types = class_config["allowed_math_types"]
    elif learning_area == "LA5":
        q_types = class_config["allowed_language_types"]
    else:
        q_types = class_config["allowed_social_types"]
    
    _random.shuffle(q_types)

    # Pull real exam content from nursery PDFs for this class+LA
    real_context = get_nursery_context(class_level, learning_area, n_samples=3)

    # Random seed phrase to force GPT to vary its output
    seed_words = ["apple","ball","chair","mango","fish","egg","cow","bird",
                  "flower","book","pen","tree","pot","tin","stool","sweet"]
    seed_objects = ", ".join(_random.sample(seed_words, 4))

    prompt = f"""You are an expert ECD (Early Childhood Development) exam writer for Ugandan nursery schools.

{real_context}
Generate a FRESH, VARIED nursery exam — different from any previous generation.
Focus your counting/drawing objects on: {seed_objects} (and similar everyday objects).

EXAM DETAILS:
- Class: {class_level} ({age_range} YEARS)
- Learning Area: {learning_area} – {la_name}
- Period: {period_full} {term_roman} EXAMINATION {year}
- School: {school_name}

STRICT FORMAT RULES (match real Ugandan nursery exams exactly):
1. Generate exactly 8 questions (numbered 1 to 8)
2. Use SIMPLE child-friendly language — short instruction, large concept
3. Each question must be one of these types appropriate for the level: {', '.join(q_types)}
4. Questions must be doable on paper: children write, draw, circle, or match
5. SUBJECT SEGREGATION:
   - If Learning Area is LA1 (Relating with Others), focus ONLY on social roles, people at home/school (family, teachers), good/bad behaviors, and community. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA2 (My Environment), focus ONLY on the physical environment, garden tools, animals, weather, and transport. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA3 (Taking Care of Myself), focus ONLY on body parts, personal hygiene, health, and things used to clean the body. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA4 (Maths), you MUST NOT generate any letter, spelling, sentence copy, or reading questions. Only focus on numbers, shapes, counting, addition, and sets.
   - If Learning Area is LA5 (Language Development), you MUST NOT generate any math, counting, shapes, or digit-based questions. Only focus on letters, phonics, reading, tracing, sounds, and word formation.
6. COGNITIVE APPROPRIATENESS:
   - Baby Class (Age 3-4): Under no circumstances should the child be asked to write or spell full words from memory. Limit writing tasks strictly to tracing single letters or digits.
   - Middle Class (Age 4-5): Under no circumstances should the child be asked to write full multi-syllable words from memory or do complex category-classification tasks using words. Odd-one-out questions must be row of pictures, not words. Writing tasks are strictly limited to filling in missing single letters (e.g., c_t) or single digits.
7. SEQUENCE FORMAT:
   - For sequences, you MUST ONLY use the list structure: "sequences": [ {{"given": [integers], "blank_at": integer, "after": [integers]}} ]. DO NOT use "sequence_str".
8. CURRICULUM-ALIGNED VOCABULARY:
   - You MUST generate pedagogically accurate and highly specific objects for each question. For example, if testing 'Health Habits', use 'soap', 'comb', 'toothbrush'. If testing 'Social Development', use 'mother', 'teacher', 'policeman'. DO NOT use generic filler objects unless it's a generic counting question.
9. NO EMOJIS:
   - YOU MUST NOT under any circumstances output emojis in the JSON. If a question requires a "picture", simply use the exact text string of the object name (e.g., "apple", "toothbrush") and the backend engine will automatically draw the picture.
10. NO sub-parts — each question is ONE clear task
11. THEMATIC COHESION (CRITICAL): Choose a specific "Sub-Theme" based on the Learning Area (e.g., "A day at the farm", "Our classroom"). ALL 8 questions MUST logically revolve around this single theme to tell a connected story.
12. VOCABULARY DIVERSITY: While adhering to the theme, you MUST use a diverse set of vocabulary. DO NOT hyper-fixate on a single object (e.g., do not make every question about a 'cow'). Use at least 6 different focal objects related to the theme across the exam.
13. TASK UNIQUENESS: You MUST use exactly 8 UNIQUE question types. Do not repeat any question type (e.g., do not use `name_picture` twice).
14. LOGICAL CONSISTENCY: The objects, words, or pictures generated MUST logically match the question instruction. If the question says "Circle the transport we use", the options MUST include at least one mode of transport.
15. DISTRACTOR QUALITY: For multiple-choice questions (e.g., `circle_correct`), the incorrect options (distractors) MUST belong to the same broad conceptual category as the correct answer. For example, if identifying a farm animal, the distractors must be OTHER animals (e.g., 'lion', 'whale'), NOT random objects like 'car' or 'chair'. This forces the child to actually think.
16. INSTRUCTION REDUNDANCY: DO NOT repeat specific question data in the instruction string. For example, if the statement is "Is a comb used to brush teeth?", the instruction MUST just be "Write yes or no." (NOT "Write yes or no. Is a comb used to brush teeth?").
17. FUNCTIONAL MATCHING (HIGHER-ORDER): For `match_words` or `match_pictures`, you MUST NOT match identical objects. You MUST match concepts functionally (e.g., 'Farmer' -> 'Hoe', 'Cow' -> 'Milk', 'Eyes' -> 'See').
18. HIGHER-ORDER YES/NO: For `write_yes_no` or `oral_questions`, DO NOT ask tautological or extremely basic questions (e.g. "Is a cow an animal?"). Ask functional or practical questions (e.g. "Does a cow give us milk?").
19. FILL MISSING WORD RULES: `fill_missing_word` is strictly a spelling exercise for a SINGLE word (e.g., "towel"). DO NOT generate full "fill-in-the-blank" sentences in the instruction field. Make sure to populate the `words` array!
20. DRAW COLOUR RULES: `draw_colour` generates exactly ONE picture on the page. The instruction MUST NOT imply a multiple-choice selection. The instruction MUST NOT tell the child to "Draw". The instruction MUST be simple: "Colour the boy washing hands." IMPORTANT: For the actual `picture` field in the JSON, DO NOT just output an isolated object (e.g. "soap"). You MUST output a rich, active scene (e.g. "a boy washing his hands with soap").
21. THE COGNITIVE CURVE (BLOOM'S TAXONOMY): You MUST order the 8 questions by ascending cognitive difficulty to naturally warm the child's brain up:
    - Questions 1-2 (Recall / Knowledge): E.g., `name_picture`, `trace_letter`, `trace_number`.
    - Questions 3-4 (Comprehension / Basic Logic): E.g., `match_words`, `match_pictures`, `circle_correct`, `draw_colour`.
    - Questions 5-6 (Application / Processing): E.g., `odd_one_out`, `fill_missing_word`, `fill_missing_letter`, `count_write`.
    - Questions 7-8 (Synthesis / Creation / Advanced Logic): E.g., `make_sentence`, `sequence_numbers`, `write_yes_no`.
22. Keep vocabulary strictly to everyday objects children know at age {age_range}, ensuring they fit the chosen theme.
Return a JSON object in this EXACT format:
{{
  "questions": [
    {{
      "number": 1,
      "instruction": "Count and write.",
      "type": "count_write",
      "content": {{
        "items": [
          {{"picture": "apples", "count": 3}},
          {{"picture": "balls", "count": 5}},
          {{"picture": "chairs", "count": 2}},
          {{"picture": "cups", "count": 4}}
        ]
      }}
    }},
    {{
      "number": 2,
      "instruction": "Write the next number.",
      "type": "sequence",
      "content": {{
        "sequences": [
          {{"given": [1, 2], "blank_at": 3, "after": [4]}},
          {{"given": [5, 6], "blank_at": 7, "after": [8]}}
        ]
      }}
    }}
  ]
}}


For "content", use the most appropriate structure for the question type as defined in the schema.

Output strictly according to the required schema. No markdown, no explanation."""

    try:
        Schema = get_nursery_schema(class_level, learning_area)
        
        # --- AGENT 1: DRAFT AGENT ---
        draft_res = await client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are the Draft Agent for Ugandan ECD exams. Output strictly according to the schema."},
                {"role": "user", "content": prompt}
            ],
            response_format=Schema,
            temperature=0.92
        )
        drafted_exam_json = draft_res.choices[0].message.parsed.model_dump_json(indent=2)
        
        # --- AGENT 2: PEDAGOGY CRITIC AGENT ---
        CriticSchema = get_critic_schema(class_level, learning_area)
        cognitive_rules = "\n".join(f"- {rule}" for rule in class_config.get("cognitive_constraints", []))
        
        critic_prompt = f"""
        You are the Head Teacher (Pedagogy Critic).
        Review the following drafted exam for {class_level} ({age_range} years old).
        
        STRICT COGNITIVE RULES FOR THIS CLASS:
        {cognitive_rules}
        
        DRAFTED EXAM JSON:
        {drafted_exam_json}
        
        Evaluate the instruction text, vocabulary, and cognitive load of each question.
        Also, evaluate the LOGICAL CONSISTENCY between the question text and the pictures/objects.
        If the question says "Circle the animal", the options MUST contain animals. If it says "Colour the transport", the picture MUST be a vehicle. If they mismatch, it is a violation.
        
        CRITICAL REVIEWS:
        1. THEMATIC COHESION & VOCABULARY DIVERSITY: Ensure all questions belong to a single connected "Sub-Theme". However, reject exams that hyper-fixate on a single object (e.g. if 'cow' is used in more than 2 questions, it is a SEVERE violation).
        2. TASK UNIQUENESS: The exam MUST have 8 UNIQUE question types. If any question type (e.g., `name_picture` or `circle_correct`) is used more than once, it is a SEVERE violation.
        3. INSTRUCTION REDUNDANCY: The instruction must NOT repeat the exact statement (e.g. "Write yes or no. Is a cow big?" is bad. It should just be "Write yes or no.").
        4. CONCEPTUAL MATCHING: Matching questions MUST have direct, functional relationships (e.g., eyes->see, farmer->hoe). Matching identical objects (hoe->hoe) is a SEVERE violation.
        5. HIGHER-ORDER YES/NO: Yes/no questions must be functional (e.g., "Do we use a hoe to sweep?"). Tautological questions (e.g., "Is a cow an animal?") are a SEVERE violation.
        6. DISTRACTOR QUALITY: For multiple choice, distractors MUST belong to the same category as the answer (e.g. if answer is a farm animal, distractors must be OTHER animals, not cars/chairs).
        7. FILL MISSING WORD: The instruction MUST NOT contain a full sentence with a blank.
        8. DRAW COLOUR: The instruction MUST NOT imply a multiple-choice choice. The `picture` field MUST be an active scene, not an isolated object.
        
        If the exam violates ANY rule (e.g. asking a Baby Class student to write or spell words, instructions are too complex, or pictures/objects do not make logical sense for the instruction), 
        set `passed` to False, explain the issue in `feedback`, and output the completely corrected exam in `revised_exam`.
        If it's perfect, set `passed` to True, say "Perfect" in `feedback`, and output the original exam in `revised_exam`.
        """
        
        print("🤖 Running Pedagogy Critic Agent...")
        critic_res = await client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are the Head Teacher (Pedagogy Critic). Enforce curriculum constraints ruthlessly."},
                {"role": "user", "content": critic_prompt}
            ],
            response_format=CriticSchema,
            temperature=0.2  # Low temperature for analytical review
        )
        
        critic_review = critic_res.choices[0].message.parsed
        print(f"🧐 Critic Passed: {critic_review.passed} | Feedback: {critic_review.feedback}")
        
        data = critic_review.revised_exam.model_dump(mode='json')
        return {
            "class_level": class_level,
            "learning_area": learning_area,
            "la_name": la_name,
            "term": term,
            "term_roman": term_roman,
            "period": period,
            "period_full": period_full,
            "school_name": school_name,
            "year": year,
            "age_range": age_range,
            "questions": data.get("questions", [])
        }
    except Exception as e:
        print(f"generate_nursery_exam error: {e}")
        raise

async def heal_exam_images(exam_data: dict, failed_objects: list, client) -> dict:
    """
    Healing Agent: If DALL-E fails to generate certain objects (due to timeouts or safety filters),
    this agent rewrites the JSON exam to replace the failed objects with simpler, safe alternatives.
    """
    if not failed_objects:
        return exam_data
        
    print(f"🚑 Healing Agent Activated! DALL-E failed to generate: {failed_objects}")
    
    prompt = f"""
    The following JSON exam was generated for an Early Childhood (Nursery) class.
    However, the image generation engine (DALL-E) FAILED to generate the following objects/scenes:
    FAILED OBJECTS: {failed_objects}
    
    This usually happens if the word is too abstract, violates a safety filter, or is overly complex.
    Your task is to scan the JSON exam and replace EVERY instance of these failed objects with a SIMPLER, safer, everyday object (e.g., 'cup', 'ball', 'tree', 'sun', 'cat', 'dog').
    Make sure the new object still makes sense in the context of the question!
    
    Current Exam JSON:
    {json.dumps(exam_data.get('questions', []), indent=2)}
    """
    
    try:
        from core.schema import ExamSchema
        res = await client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are the Exam Healing Agent. Replace failed vocabulary with simpler words."},
                {"role": "user", "content": prompt}
            ],
            response_format=ExamSchema,
            temperature=0.3
        )
        healed_data = res.choices[0].message.parsed.model_dump(mode='json')
        exam_data["questions"] = healed_data.get("questions", [])
        print("🚑 Healing complete! Exam patched with safe vocabulary.")
        return exam_data
    except Exception as e:
        print(f"Healing Agent failed: {e}")
        return exam_data

async def analyze_image_needs(questions: list, subject: str = "General", level: str = "Standard") -> list:
    """
    Image Needs Agent: Reads every question and decides whether it pedagogically
    benefits from a visual aid (diagram, map, chart, illustration).
    Returns a list of question numbers (1-indexed) that need an image.
    """
    try:
        client = get_async_openai_client()

        # Build a compact question list for the prompt
        q_summary = ""
        for q in questions:
            if not isinstance(q, dict):
                continue
            num = q.get("number", "?")
            text = q.get("text", "")[:200]  # truncate for token efficiency
            q_summary += f"Q{num}: {text}\n"

        prompt = f"""### IMAGE NEEDS ASSESSMENT AGENT

You are a senior educational content designer reviewing a {subject} exam for {level} students.

For each question below, decide if adding a visual aid (diagram, map, chart, illustration, picture, or graph) would:
- Clarify the question meaningfully for the student, OR
- Be pedagogically necessary for the student to answer the question correctly.

IMPORTANT CRITERIA for needing an image:
- Questions about maps, locations, or geographic features → YES
- Questions about shapes, geometry, measurements, or spatial reasoning → YES  
- Questions about scientific diagrams (body parts, plants, cycles, apparatus) → YES
- Questions about charts, graphs, or data interpretation → YES
- Questions asking students to "use the diagram/figure below" or "refer to the picture" → YES
- Questions that describe a visual scenario (e.g. "a farmer has a rectangular field") → MAYBE
- Simple recall or definition questions → NO
- Pure calculation questions → NO
- Reading comprehension / English grammar questions → NO

QUESTIONS:
{q_summary}

Return ONLY a valid JSON object in this exact format:
{{
  "needs_image": [1, 3, 7, 12]  // List of question NUMBERS that need an image. Empty list [] if none.
}}
"""

        res = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert educational content designer. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        data = json.loads(res.choices[0].message.content)
        needs = data.get("needs_image", [])
        # Validate: ensure all entries are integers and within range
        q_nums = {q.get("number") for q in questions if isinstance(q, dict)}
        validated = [n for n in needs if isinstance(n, int) and n in q_nums]
        print(f"DEBUG Image Agent: {len(validated)}/{len(questions)} questions flagged as needing images: {validated}")
        return validated
    except Exception as e:
        print(f"analyze_image_needs error: {e}")
        return []



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

async def stream_generate_ai_content(mode, level, subject, term, num_questions, difficulty="Balanced", ai_model="gpt-4o", internal="Internal", topic="", pedagogy_hint=None, force_images=False, duration="2 HR", brand_name="EDUMERC"):
    from ui.document_builder import build_header_html, build_question_html, build_answer_row_html, build_footer_html
    import json
    import asyncio
    
    client = get_async_openai_client()
    syllabus_rows = retrieve_syllabus_context(subject, level, term, topic)
    rubric_context = retrieve_exam_rubric(subject, level, topic)
    year = "2026"

    ps = get_paper_structure(subject, level)
    official_total = get_total_questions(subject, level)
    sec_a_count = ps.get("sec_a_count", 0)
    num_questions = official_total if official_total > 0 else num_questions

    math_subjects = ["Math", "Physics", "Science"]
    is_math = any(s in subject for s in math_subjects)
    is_ecd = any(k in level for k in ["Baby", "Middle", "Top", "Primary 1", "Primary 2", "Primary 3", "Nursery", "Kindergarten", "P1", "P2", "P3", "ECD"])

    age_profile = "General Audience"
    if "Baby" in level or "Middle" in level or "Top" in level: age_profile = "Ages 3-5"
    elif "Primary 1" in level or "Primary 2" in level or "Primary 3" in level: age_profile = "Ages 6-8"
    elif "Primary 4" in level or "Primary 5" in level: age_profile = "Ages 9-11"
    elif "Primary 6" in level or "Primary 7" in level: age_profile = "Ages 12-13"
    elif "Senior 1" in level or "Senior 2" in level: age_profile = "Ages 14-15"
    elif "Senior 3" in level or "Senior 4" in level: age_profile = "Ages 16-17"
    elif "Senior 5" in level or "Senior 6" in level: age_profile = "Ages 18+"

    authorized_topics = []
    from core.syllabus_master import MASTER_SYLLABUS, get_syllabus_graph
    if subject in MASTER_SYLLABUS and level in MASTER_SYLLABUS[subject]:
        authorized_topics = MASTER_SYLLABUS[subject][level]
    authorized_topics_str = ", ".join(authorized_topics) if authorized_topics else "General Subject Knowledge"

    # ── PEDAGOGICAL KNOWLEDGE GRAPH (PKG) ENRICHMENT ──
    pkg = get_syllabus_graph()
    pkg_skills = []
    pkg_prereqs = []
    
    # Identify relevant topics for graph lookups
    active_topics = [topic] if (topic and topic in authorized_topics) else authorized_topics
    for t in active_topics:
        node = pkg.get_node(subject, level, t)
        if node:
            if node.get("skills"):
                pkg_skills.extend(node["skills"])
            prereq_list = pkg.get_prerequisites_recursive(subject, level, t)
            for ps, pl, pt in prereq_list:
                pkg_prereqs.append(f"{pt} (from {pl} {ps})")
                
    pkg_skills_str = ", ".join(pkg_skills) if pkg_skills else "General curriculum skill mastery"
    pkg_prereqs_str = ", ".join(list(set(pkg_prereqs))) if pkg_prereqs else "None"

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
    payload = json.dumps({"type": "header", "html": header_html})
    padding = " " * max(0, 4096 - len(payload))
    yield f"data: {payload}{padding}\n\n"

    async def _generate_chunk(chunk_size: int, start_num: int):
        import re
        is_lower_primary = False
        is_foundation = False
        is_transitional = False
        if "Primary" in level:
            m = re.search(r'\d+', level)
            if m:
                level_num = int(m.group())
                if level_num <= 4:
                    is_lower_primary = True
                    if level_num <= 2:
                        is_foundation = True
                    else:
                        is_transitional = True
        elif any(x in level for x in ["Nursery", "ECD", "Baby", "Middle", "Top"]):
            is_lower_primary = True
            is_foundation = True
                
        if is_foundation:
            layout_instruction = "CRITICAL REQUIREMENT: For this Foundation class (P1-P2/Nursery), you MUST heavily generate a mix of 'fill_blank', 'matching', and 'vertical_math' types. DO NOT use 'type': 'mcq' or 'structured' under any circumstances! Keep it extremely simple."
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif is_transitional:
            layout_instruction = "CRITICAL REQUIREMENT: For this Transitional class (P3-P4), you MUST generate a mix of 'vertical_math' and 1-sentence 'short_answer' questions. You may also introduce very simple 'structured' questions (max 2 parts, e.g., a, b). DO NOT use 'type': 'mcq' under any circumstances!"
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif "Primary" in level:
            # Authentic Primary (P4-P7) exams do NOT use multiple choice. Section A is short answer.
            if start_num <= sec_a_count:
                layout_instruction = f"CRITICAL REQUIREMENT: Authentic {level} exams strictly prohibit Multiple Choice Questions. DO NOT use 'type': 'mcq' under any circumstances! For Section A (Q1 to {sec_a_count}), you MUST ONLY generate 'short_answer' questions. Section A questions must be single-part short-answer ONLY. DO NOT generate sub-questions (a, b, c) unless generating for Section B."
            else:
                layout_instruction = f"CRITICAL REQUIREMENT: You are generating SECTION B. You MUST indicate this by generating 'structured' questions with multiple sub-parts (e.g. a, b, c) following the structure of the original papers. DO NOT use 'type': 'mcq' under any circumstances!"
            mcq_routing_rule = "- NEVER generate Multiple Choice Questions (type: mcq). It is forbidden."
        elif "Senior 4" in level and subject in ["Physics", "Chemistry", "Biology", "Agriculture"]:
            # UCE Sciences use Multiple Choice for Section A
            layout_instruction = f"IMPORTANT: Authentic UCE Science exams use Multiple Choice for Section A. You MUST generate 'mcq' for Q1 to {sec_a_count}, and 'structured' for Section B."
            mcq_routing_rule = '- If generating a Multiple Choice Question, set "type": "mcq" and provide exactly 4 options in "options": ["Option 1", "Option 2", "Option 3", "Option 4"] (Do not include A, B, C, D in the text).'
        else:
            layout_instruction = f"Generate 'short_answer' for Section A (Q1 to {sec_a_count}) and 'structured' for Section B."
            mcq_routing_rule = '- If generating a Multiple Choice Question, set "type": "mcq" and provide exactly 4 options in "options": ["Option 1", "Option 2", "Option 3", "Option 4"] (Do not include A, B, C, D in the text).'

        # ── ENGLISH SPECIFIC FORMATTING RULES ──
        if subject.lower() == "english":
            authoritative_commands_rule = '- ENGLISH GRAMMAR PERSONA: You MUST NOT use "Authoritative Commands" like "Convert this". INSTEAD, you MUST generate gap-filling exercises with a blank line "________" and put the root word in brackets. Example: "The Guest-of-Honour will get an ________ letter soon. (invite)".'
            if start_num <= sec_a_count:
                layout_instruction += "\n- ENGLISH GRAMMAR FORMAT (SECTION A): Follow the English Grammar Persona. You MUST group every 5-10 grammar questions under a shared instruction header. Set 'instruction_group' to exactly the same text (e.g. 'In questions 1-10, use the correct form of the word in brackets...') for all questions in that group."
            else:
                layout_instruction += "\n- ENGLISH COMPREHENSION FORMAT (SECTION B): For Section B, you MUST generate an authentic passage (a story, poem, dialogue, notice, table, or jumbled sentences) in the question `text`. This MUST be followed by EXACTLY 10 `sub_questions` (a, b, c, d, e, f, g, h, i, j) testing comprehension of that passage. This is critical for matching the real paper's length."
        else:
            authoritative_commands_rule = '- AUTHORITATIVE COMMANDS: Never ask open-ended questions like "What is...". You MUST use imperative commands: "Name any one...", "Give any two...", "State...", "Outline...", "Work out:".'

        # ── DIAGRAM DENSITY & COMPOSITION RULES ──
        if subject.lower() in ["mathematics", "math", "maths", "numeracy", "geography", "social studies", "science", "integrated science"]:
            layout_instruction += "\n- DIAGRAM DENSITY REQUIREMENT: You MUST include diagrams for at least 25% of the questions in this batch. For any such question, provide a detailed visual description in the 'diagram_description' field."
            layout_instruction += "\n- DIAGRAM PREAMBLE RULE: If a question requires a diagram, the question `text` MUST begin with a formal UNEB preamble (e.g., 'Study the diagram of the [object] below and use it to answer the question.')."
            layout_instruction += "\n- NO SHARED DIAGRAMS: Every question MUST be 100% self-contained. Do not write 'Use the diagram to answer questions 4 and 5'. Instead, attach the diagram to question 4, and if question 5 needs a diagram, describe a new one or make it independent."
        if is_ecd or is_foundation:
            prep_req = "\n5. EXTREME SIMPLICITY & VISUAL REQUIREMENT: You MUST use extremely basic vocabulary (e.g., 'Write', 'Draw', 'Count', 'Match'). Sentences MUST be under 7 words! ALMOST EVERY question MUST be visually driven. Include an explicit image placeholder like '[Picture of 3 big red mangoes]' directly in the 'text' field for the Image Agent to process!"
        else:
            prep_req = ""

        import yaml
        import os
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "exam_generator.yaml")
        with open(prompt_path, 'r') as f:
            prompt_template = yaml.safe_load(f)["template"]

        prompt = prompt_template.format(
            subject=subject.upper(),
            level=level,
            term=term,
            topic=topic or 'Full Syllabus',
            syllabus_rows=syllabus_rows,
            rubric_context=rubric_context,
            pkg_skills_str=pkg_skills_str,
            pkg_prereqs_str=pkg_prereqs_str,
            age_profile=age_profile,
            authorized_topics_str=authorized_topics_str,
            prep_req=prep_req,
            chunk_size=chunk_size,
            start_num=start_num,
            layout_instruction=layout_instruction,
            mcq_routing_rule=mcq_routing_rule,
            authoritative_commands_rule=authoritative_commands_rule
        )
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a professional examiner. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            draft_content = response.choices[0].message.content

            # --- PASS 2: Senior Chief Examiner Critique & Self-Correction Audit Pass ---
            critique_prompt = f"""### NATIONAL EXAMINER AUDIT & CRITIQUE PROTOCOL
You are the Senior Chief Examiner of the National Examinations Board.
Your mission is to audit and elevate the quality of draft exam questions.

---
### INPUT DRAFT QUESTIONS (JSON):
{draft_content}

---
### AUDIT CHECKLIST:
1. **Curriculum Alignment**: Do these questions strictly match the targeted skills [{pkg_skills_str}]?
2. **Cognitive Ceiling**: Ensure no question violates the authorized cognitive boundary: [{authorized_topics_str}].
3. **Ugandan Local Realism**: Replace any generic Western items/names with high-fidelity local equivalents (e.g. use "maize", "cassava", "matooke", "mangoes" instead of "apples"/"peaches"; use "Kato", "Mukasa", "Namubiru", "Babirye" instead of "John"/"Bob"; use "UGX" shillings instead of dollars).
4. **Pedagogical Integrity**: Ensure phrasing is clear, age-appropriate ({age_profile}), structurally sound, and matching UNEB standard conventions.
5. **No Redundancy**: Eliminate any question pattern duplicates or highly repetitive templates within the chunk.

---
### REPAIR ACTIONS:
Review every question in the draft. If any question fails the checklist, repair it. If it passes, keep it.
Return the final, fully corrected and highest-integrity list of questions.
Output format: ONLY a valid JSON object matching the exact original structure:
{{
  "questions": [
    ...
  ]
}}
"""
            refine_response = await client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": "You are a Senior Chief Examiner. Review, self-correct, and return ONLY a high-integrity repaired JSON of the questions."},
                    {"role": "user", "content": critique_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(refine_response.choices[0].message.content).get("questions", [])
        except Exception as e:
            print(f"Chunk generation error: {e}")
            return []

    chunk_size = 5
    tasks = []
    for i in range(0, num_questions, chunk_size):
        size = min(chunk_size, num_questions - i)
        # Schedule the chunk generation in the background immediately to run concurrently
        tasks.append(asyncio.create_task(_generate_chunk(size, i + 1)))
    
    all_questions = []
    answer_key_rows = ""
    sem = asyncio.Semaphore(2)

    # Process and yield chunks in sequential order to guarantee correct question ordering (1..N),
    # while benefitting from concurrent background execution!
    for task in tasks:
        chunk = await task
        if not chunk:
            continue

        async def process_question(q):
            # Strict Post-Process Anti-MCQ Ban for Primary
            if "Primary" in level and q.get("type") == "mcq":
                q["type"] = "short_answer"
                q["options"] = []

            text = q.get("text") or ""
            is_organic = any(s in subject for s in ["Science", "Biology", "Social", "Geography", "SST"])
            has_visual_keywords = any(k in text.lower() for k in ["diagram", "picture", "shape", "figure", "map", "illustration", "below"])

            if force_images or (is_organic and has_visual_keywords):
                desc = q.get("visual_prompt") or f"A clean worksheet illustration for this {subject} question: {text}"
                async with sem:
                    res_url = await generate_illustration(text, subject, level, custom_prompt=desc, style="svg")
                    if res_url:
                        if res_url.strip().startswith("<svg") or res_url.strip().startswith("<script"):
                            q["tikz_code"] = res_url
                        else:
                            q["tikz_code"] = f'<img src="{res_url}" style="width:100%; max-width:420px; display:block; margin:15px auto;"/>'
            return q

        processed_chunk = await asyncio.gather(*(process_question(q) for q in chunk))
        all_questions.extend(processed_chunk)

        for q in processed_chunk:
            q_html = build_question_html(mode, q, subject, level)
            ans_html = build_answer_row_html(q)
            answer_key_rows += ans_html
            # Pad to 4KB to force HTTP chunked-transfer buffer flush
            payload = json.dumps({"type": "question", "html": q_html, "raw_q": q})
            padding = " " * max(0, 4096 - len(payload))
            yield f"data: {payload}{padding}\n\n"

    footer_html = build_footer_html(answer_key_rows)
    payload = json.dumps({"type": "footer", "html": footer_html, "all_questions": all_questions})
    padding = " " * max(0, 4096 - len(payload))
    yield f"data: {payload}{padding}\n\n"


async def regenerate_single_nursery_question(
    class_level: str,
    learning_area: str,
    question_type: str,
    failed_question: dict,
    issues: list
) -> dict:
    """
    AI Agent that takes a failed nursery question, a list of issues found by the Integrity Agent,
    and returns a corrected and compliant version of the question.
    """
    client = get_async_openai_client()
    
    age_map = {"Baby Class": "3 – 4", "Middle Class": "4 – 5", "Top Class": "5 – 6"}
    age_range = age_map.get(class_level, "4 – 5")
    
    permitted_objects = "ball, apple, chair, cup, book, pencil, tree, flower, star, egg, tin, mango, banana, pot, stool, sweet, house, stick"
    
    issues_str = "\n".join(f"- {issue}" for issue in issues)
    failed_json_str = json.dumps(failed_question, indent=2)
    q_num = failed_question.get("number", 1)
    
    prompt = """You are the Nursery Exam Auto-Correction Agent.
Your job is to repair a failed nursery/ECD exam question.

CONTEXT:
- Class Level: {class_level} (Age {age_range})
- Learning Area: {learning_area}
- Question Type: {question_type}

FAILED QUESTION JSON:
{failed_json_str}

INTEGRITY AGENT ISSUES LOG:
{issues_str}

STRICT RULES TO RESPECT:
1. AGE APPROPRIATENESS:
   - Baby Class: Numbers MUST be between 1 and 5 only.
   - Middle Class: Numbers MUST be between 1 and 10 only.
   - Top Class: Numbers MUST be between 1 and 20 only.
2. NO PLACEHOLDERS: Do not use placeholders like "TODO", "...", "N/A", etc.
3. SUBJECT SEGREGATION:
   - If Learning Area is LA1 (Relating with Others), focus ONLY on social roles, people at home/school (family, teachers), good/bad behaviors, and community. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA2 (My Environment), focus ONLY on the physical environment, garden tools, animals, weather, and transport. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA3 (Taking Care of Myself), focus ONLY on body parts, personal hygiene, health, and things used to clean the body. YOU MUST NOT generate any math, counting, or spelling questions.
   - If Learning Area is LA4 (Maths), you MUST NOT generate any letter, spelling, sentence copy, or reading questions. Only focus on numbers, shapes, counting, addition, and sets.
   - If Learning Area is LA5 (Language Development), you MUST NOT generate any math, counting, shapes, or digit-based questions. Only focus on letters, phonics, reading, tracing, sounds, and word formation.
4. COGNITIVE APPROPRIATENESS:
   - Baby Class (Age 3-4): Under no circumstances should the child be asked to write or spell full words from memory. Limit writing tasks strictly to tracing single letters or digits.
   - Middle Class (Age 4-5): Under no circumstances should the child be asked to write full multi-syllable words from memory or do complex category-classification tasks using words. Odd-one-out questions must be row of pictures, not words. Writing tasks are strictly limited to filling in missing single letters (e.g., c_t) or single digits.
5. REQUIRED CONTENT FIELDS:
   - count_write -> content MUST have "items": [{"picture": "string", "count": integer}]
   - count_circle -> content MUST have "items": [{"picture": "string", "count": integer, "options": [integers]}]
   - sequence -> content MUST have "sequences": [{"given": [integers], "blank_at": integer, "after": [integers]}] (DO NOT use sequence_str)
   - add_numbers -> content MUST have "problems" or "sums": [{"a": integer, "b": integer}]
   - match_words or match_numbers or match_pictures -> content MUST have "left": [strings/digits], "right": [strings/digits]
   - shade_for_number -> content MUST have "items": [integers]
   - draw_for_number -> content MUST have "numbers": [integers]
   - name_shapes -> content MUST have "shapes": [strings]
   - name_sets -> content MUST have "sets": [{"count_word": "string", "object": "string", "hint": "string"}]
6. ASSET COMPLIANCE:
   - For picture-based questions (count_write, count_circle, draw_for_number, match_pictures, name_sets), you MUST ONLY use objects from this list: [{permitted_objects}]. Any other object will fail the image cache check. DO NOT use generic categories like "food" or "fruits".

Return ONLY a valid JSON representing the corrected single question. Use the exact same structure as the failed question but make it fully compliant and corrected.

Output JSON structure:
{
  "number": {q_num},
  "instruction": "Instruction text...",
  "type": "{question_type}",
  "content": {}
}
"""

    prompt = (
        prompt.replace("{class_level}", class_level)
        .replace("{age_range}", age_range)
        .replace("{learning_area}", learning_area)
        .replace("{question_type}", question_type)
        .replace("{failed_json_str}", failed_json_str)
        .replace("{issues_str}", issues_str)
        .replace("{permitted_objects}", permitted_objects)
        .replace("{q_num}", str(q_num))
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional ECD examiner. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in auto-correcting single question: {e}")
        return failed_question
