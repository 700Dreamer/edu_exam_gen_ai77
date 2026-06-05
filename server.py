import os
import sys
import json, io, base64, re, asyncio
from typing import Optional, List

# ── Load .env securely ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip("'\"")

# ── Add project root to path so core/ is importable ──
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.ai_engine import generate_ai_content, analyze_pedagogy, chat_response, get_openai_client, generate_scenario_content, generate_illustration, stream_generate_ai_content, analyze_image_needs, generate_nursery_exam, generate_diagrams_for_questions
from core.db_engine import save_project, load_projects, init_db
from core.pdf_engine import save_pdf_background
from ui.document_builder import build_full_html
from ui.nursery_builder import build_nursery_html
from core.nursery_images import ensure_exam_images
from core.syllabus_master import ALL_SUBJECTS, ALL_LEVELS, get_master_topics
from core.ingestion_db import get_ingest_stats
from core.export_engine import generate_docx_stream
from core.marking_engine import mark_student_work

from contextlib import asynccontextmanager
from core.models import create_db_and_tables, User
from core.auth import fastapi_users, auth_backend, require_role, UserRead, UserCreate, UserUpdate, log_user_activity
from fastapi import Depends

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(title="EduQuest AI Engine", version="3.1.0", lifespan=lifespan)

# ── Authentication Routes ──
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/api/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["users"],
)



# Serve generated nursery images as static files
from pathlib import Path as _Path
_nursery_img_dir = _Path(BASE_DIR) / "static" / "nursery_imgs"
_nursery_img_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/nursery_imgs", StaticFiles(directory=str(_nursery_img_dir)), name="nursery_imgs")

# ── CORS — allow Next.js dev server ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ── Serve generated images ──
GENERATED_DIR = os.path.join(BASE_DIR, "frontend", "public", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)
app.mount("/api/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

class GenerateRequest(BaseModel):
    mode: str
    level: str
    subject: str
    term: str
    question_count: int
    duration: Optional[str] = "2 HR 30 MIN"
    paper_style: Optional[str] = "uneb_standard"
    view_mode: Optional[str] = "scroll"
    topic: Optional[str] = ""
    brand_name: Optional[str] = "EduQuest"
    ai_model: Optional[str] = "gpt-4o"
    content_override: Optional[str] = None
    pedagogy_hint: Optional[dict] = None
    force_images: Optional[bool] = False

class ScenarioRequest(BaseModel):
    subject: str
    level: str
    term: str
    theme: str
    topic: Optional[str] = ""
    difficulty: Optional[str] = "Standard"
    brand_name: Optional[str] = "EduQuest"
    ai_model: Optional[str] = "gpt-4o"
    force_images: Optional[bool] = False

@app.post("/api/scenario")
async def scenario_endpoint(
    req: ScenarioRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    try:
        raw_str = await generate_scenario_content(req.subject, req.level, req.theme, force_images=req.force_images)
        raw_data = json.loads(raw_str)
        title = f"{req.subject} {req.level} - Competency Test"
        
        # Render HTML
        html = build_full_html(
            mode="Exams", 
            exam_type="Competency Test",
            level=req.level,
            subject=req.subject,
            term_roman=req.term,
            exam_year="2026",
            duration="1 HR",
            school_name="EduQuest Central",
            brand_name=req.brand_name,
            question_count=len(raw_data.get("questions", [])),
            content_raw=raw_str,
            topic=req.theme
        )
        
        # Auto-save
        save_project(req.subject, req.level, req.term, raw_str, html, title)
        
        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "generate_scenario",
            {"subject": req.subject, "level": req.level, "theme": req.theme, "title": title}
        )
        
        return {"raw": raw_data, "html": html, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RefineRequest(BaseModel):
    html: str
    instruction: str
    subject: str
    level: str
    term: str

@app.post("/api/generate")
async def generate_endpoint(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    try:
        if req.content_override:
            raw = json.loads(req.content_override)
            raw_str = req.content_override
            title = f"{req.subject} {req.level} - Refined"
        else:
            raw, raw_str, title = await generate_ai_content(
                req.mode, req.level, req.subject, req.term, 
                req.question_count, "Balanced", req.ai_model, "Internal", 
                req.topic, req.pedagogy_hint, req.force_images
            )
        
        term_val = req.term
        term_roman = "I"
        if "Term 2" in term_val: term_roman = "II"
        elif "Term 3" in term_val: term_roman = "III"
        
        exam_type = "BEGINNING OF"
        if "(MOT)" in term_val or "MOT" in term_val: exam_type = "MIDDLE OF"
        elif "(EOT)" in term_val or "EOT" in term_val: exam_type = "END OF"
        
        # ── DIAGRAM GENERATION PASS ──────────────────────────────────────
        # For any question with a diagram_description, call gpt-image-1
        if req.mode == "Exams" and isinstance(raw, dict) and raw.get("questions"):
            questions_with_diagrams = await generate_diagrams_for_questions(
                raw["questions"], req.subject, req.level
            )
            raw["questions"] = questions_with_diagrams
            raw_str = json.dumps(raw)
        # ─────────────────────────────────────────────────────────────────

        # Render the actual HTML for the frontend
        html = build_full_html(
            mode=req.mode,
            exam_type=exam_type,
            level=req.level,
            subject=req.subject,
            term_roman=f"TERM {term_roman}",
            exam_year="2026",
            duration=req.duration,
            school_name="EduQuest Central",
            brand_name=req.brand_name,
            question_count=req.question_count,
            content_raw=raw_str,
            topic=req.topic,
            paper_style=req.paper_style,
            view_mode=req.view_mode
        )
        
        # Auto-save history
        save_project(req.subject, req.level, req.term, raw_str, html, title)
        
        # Dispatch background PDF generation
        background_tasks.add_task(save_pdf_background, html, raw_str, req.subject, req.level, title)
        
        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "generate_exam",
            {"subject": req.subject, "level": req.level, "term": req.term, "question_count": req.question_count, "title": title}
        )
        
        return {"raw": raw_str, "html": html, "title": title}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-stream")
async def generate_stream_endpoint(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    try:
        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "generate_exam_stream",
            {"subject": req.subject, "level": req.level, "term": req.term, "question_count": req.question_count}
        )

        # We wrap the generator to handle StreamingResponse
        async def event_generator():
            try:
                # We do not support content_override in stream mode currently
                if req.content_override:
                    yield f"data: {json.dumps({'error': 'Streaming not supported for overridden content'})}\n\n"
                    return
                
                async for chunk in stream_generate_ai_content(
                    req.mode, req.level, req.subject, req.term, 
                    req.question_count, "Balanced", req.ai_model, "Internal", 
                    req.topic, req.pedagogy_hint, req.force_images, req.duration, req.brand_name
                ):
                    yield chunk
            except Exception as e:
                import traceback; traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress")
async def progress_stream_endpoint():
    from core.telemetry import add_listener, remove_listener
    
    q = asyncio.Queue()
    add_listener(q)
    
    async def event_generator():
        try:
            while True:
                msg = await q.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            remove_listener(q)
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/analyze")
async def analyze_endpoint(data: dict):
    content = data.get("content")
    subject = data.get("subject", "General")
    level = data.get("level", "Standard")
    if not content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    try:
        analysis = await analyze_pedagogy(content, subject, level)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
async def generate_image_endpoint(
    data: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    """Manually generate an AI illustration for a single question on demand."""
    question_text = data.get("question_text", "")
    subject = data.get("subject", "General")
    level = data.get("level", "Primary 4")
    custom_prompt = data.get("custom_prompt", "")  # Optional teacher-supplied prompt
    style = data.get("style", "png")

    if not question_text and not custom_prompt:
        raise HTTPException(status_code=400, detail="question_text or custom_prompt is required")

    try:
        result = await generate_illustration(question_text, subject, level, custom_prompt, style)

        if not result:
            raise HTTPException(
                status_code=503,
                detail="Illustration generation returned no result. Check OPENAI_API_KEY / GOOGLE_API_KEY and API quota."
            )

        if result.strip().startswith("<svg") or result.strip().startswith("<script"):
            image_html = result
        else:
            image_html = f'<img src="{result}" style="width:100%; max-width:420px; display:block; margin:10px auto; border:1px solid #eee; border-radius:4px;"/>'

        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "generate_image",
            {"question_text": question_text, "subject": subject, "level": level, "custom_prompt": custom_prompt}
        )

        return {"image_html": image_html}

    except HTTPException:
        raise
    except ValueError as e:
        # Raised by get_async_openai_client() when OPENAI_API_KEY is missing
        raise HTTPException(status_code=422, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Illustration engine error: {str(e)}")


class QuestionRegenerateRequest(BaseModel):
    subject: str
    level: str
    topic: str = ""
    instruction: str = ""

@app.post("/api/regenerate-question")
async def regenerate_question_endpoint(req: QuestionRegenerateRequest):
    try:
        from core.ai_engine import regenerate_single_question
        new_q = await regenerate_single_question(
            subject=req.subject,
            level=req.level,
            topic=req.topic,
            instruction=req.instruction
        )
        if not new_q:
            raise HTTPException(status_code=500, detail="Failed to generate new question.")
        return {"question": new_q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ImageNeedsRequest(BaseModel):
    questions: list
    subject: Optional[str] = "General"
    level: Optional[str] = "Standard"

@app.post("/api/analyze-image-needs")
async def analyze_image_needs_endpoint(req: ImageNeedsRequest):
    """
    Image Needs Agent: Reads all generated questions and flags which ones
    need a visual aid (diagram, map, illustration, etc.).
    Returns a list of question numbers that should be marked for illustration.
    """
    if not req.questions:
        return {"needs_image": []}
    try:
        flagged = await analyze_image_needs(req.questions, req.subject, req.level)
        return {"needs_image": flagged}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class NurseryRequest(BaseModel):
    class_level: str = "Middle Class"          # Baby Class | Middle Class | Top Class
    learning_area: str = "LA4"                  # LA1 | LA2 | LA3 | LA4 | LA5
    term: str = "Term 1"                        # Term 1 | Term 2 | Term 3
    period: str = "EOT"                         # BOT | MOT | EOT
    school_name: Optional[str] = "EduQuest Academy"
    year: Optional[str] = "2025"

@app.post("/api/nursery-exam")
async def nursery_exam_endpoint(
    req: NurseryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    """Generate an authentic Ugandan nursery/ECD exam for Baby, Middle or Top class."""
    try:
        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "generate_nursery_exam",
            {"class_level": req.class_level, "learning_area": req.learning_area, "term": req.term, "period": req.period}
        )

        exam_data = await generate_nursery_exam(
            class_level=req.class_level,
            learning_area=req.learning_area,
            term=req.term,
            period=req.period,
            school_name=req.school_name,
            year=req.year
        )

        from core.ai_engine import get_async_openai_client, regenerate_single_nursery_question
        from core.integrity_agent import run_integrity_check
        
        img_client = get_async_openai_client()

        # ── Pre-Rendering Integrity Check ──
        integrity = await run_integrity_check(
            exam_data, client=img_client, ai_check=False
        )

        # ── Autonomous Self-Correction (Auto-Repair) Loop ──
        MAX_REPAIR_ATTEMPTS = 3
        repair_attempt = 0
        
        while integrity.get("overall_status") == "FAIL" and repair_attempt < MAX_REPAIR_ATTEMPTS:
            repair_attempt += 1
            print(f"\n[AUTO-CORRECTION] Attempt {repair_attempt} of {MAX_REPAIR_ATTEMPTS} to auto-repair failed questions.")
            
            questions = exam_data.get("questions", [])
            q_reports = integrity.get("questions", [])
            
            repaired_count = 0
            for idx, q_report in enumerate(q_reports):
                if q_report.get("final_status") == "FAIL" and idx < len(questions):
                    failed_q = questions[idx]
                    rule_issues = q_report.get("rule_check", {}).get("issues", [])
                    ai_issues = q_report.get("ai_check", {}).get("issues", []) if q_report.get("ai_check") else []
                    issues = rule_issues + ai_issues
                    
                    print(f"[AUTO-CORRECTION] Question {idx + 1} ({failed_q.get('type')}) failed integrity check with issues:")
                    for issue in issues:
                        print(f"  - {issue}")
                        
                    print(f"[AUTO-CORRECTION] Requesting AI repair for Question {idx + 1}...")
                    
                    # Call the AI auto-correct agent
                    repaired_q = await regenerate_single_nursery_question(
                        class_level=req.class_level,
                        learning_area=req.learning_area,
                        question_type=failed_q.get("type"),
                        failed_question=failed_q,
                        issues=issues
                    )
                    
                    # Update question in place
                    questions[idx] = repaired_q
                    repaired_count += 1
                    print(f"[AUTO-CORRECTION] Question {idx + 1} successfully replaced with repaired version.")
            
            if repaired_count == 0:
                break
                
            # Re-evaluate
            integrity = await run_integrity_check(
                exam_data, client=img_client, ai_check=False
            )
            print(f"[AUTO-CORRECTION] Re-evaluation overall status: {integrity.get('overall_status')}\n")

        # Generate real images and get their URLs (served as static files)
        image_b64s, failed_images = await ensure_exam_images(exam_data.get("questions", []), img_client)
        
        # 🚑 TIER 3 HEALING AGENT: If DALL-E failed any images, heal the exam and try one more time!
        if failed_images:
            from core.ai_engine import heal_exam_images
            exam_data = await heal_exam_images(exam_data, failed_images, img_client)
            # Re-run the image generator for the new healed words
            healed_b64s, still_failed = await ensure_exam_images(exam_data.get("questions", []), img_client)
            # Merge the new images into our dictionary
            image_b64s.update(healed_b64s)

        # Convert to Base64 Data URIs to ensure images render universally across all clients/iframes
        image_urls = {
            name: f"data:image/png;base64,{b64}"
            for name, b64 in image_b64s.items()
        }

        # Embed dynamic VLM Layout Auditor CSS patch in the generated exam data
        exam_data["layout_css_patch"] = integrity.get("layout_css_patch", "")
        
        # We still build HTML here strictly for the PDF background task until Phase 4 is fully complete
        from ui.nursery_builder import build_nursery_html
        html = build_nursery_html(exam_data, images=image_urls)
        
        raw_str = json.dumps(exam_data)
        title = f"{req.learning_area} - {req.class_level}"
        background_tasks.add_task(save_pdf_background, html, raw_str, req.learning_area, req.class_level, title)

        return {"html": html, "exam_data": exam_data, "integrity": integrity, "images": image_urls}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackRequest(BaseModel):
    class_level: str
    learning_area: str
    original_question: dict
    revised_question: dict
    action: str = "edit" # 'edit' or 'simplify'

@app.post("/api/feedback")
async def rlhf_feedback_endpoint(
    req: FeedbackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["teacher", "admin"]))
):
    """Phase 5: RLHF endpoint to store human corrections."""
    try:
        # Log activity
        background_tasks.add_task(
            log_user_activity,
            current_user.id,
            "rlhf_feedback",
            {"class_level": req.class_level, "learning_area": req.learning_area, "action": req.action}
        )
        import sqlite3
        import uuid
        import chromadb
        from chromadb.utils import embedding_functions

        # 1. Store in SQLite for audit/training
        db_path = os.path.join(BASE_DIR, "feedback.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS feedback
                     (id TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      class_level TEXT, learning_area TEXT, action TEXT,
                      original_json TEXT, revised_json TEXT)''')
        feedback_id = str(uuid.uuid4())
        c.execute("INSERT INTO feedback (id, class_level, learning_area, action, original_json, revised_json) VALUES (?, ?, ?, ?, ?, ?)",
                  (feedback_id, req.class_level, req.learning_area, req.action, 
                   json.dumps(req.original_question), json.dumps(req.revised_question)))
        conn.commit()
        conn.close()

        # 2. Vectorize the 'improved' question into ChromaDB
        chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        collection = chroma_client.get_or_create_collection(name="nursery_papers", embedding_function=openai_ef)
        
        # Turn the revised question JSON into a text chunk
        revised_text = f"Teacher Revised Question ({req.action}): {req.revised_question.get('instruction', '')} | Type: {req.revised_question.get('type')} | Content: {json.dumps(req.revised_question.get('content', {}))}"
        
        collection.add(
            documents=[revised_text],
            metadatas=[{"class_level": req.class_level, "learning_area": req.learning_area, "source": "rlhf"}],
            ids=[feedback_id]
        )

        return {"status": "success", "message": "Feedback integrated into RLHF loop"}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class IntegrityCheckRequest(BaseModel):
    exam_data: dict
    ai_check: bool = True      # set False for fast rule-only check
    ai_sample_size: int = 3    # how many questions to send to GPT-4o vision

@app.post("/api/integrity-check")
async def integrity_check_endpoint(req: IntegrityCheckRequest):
    """Run the QA integrity agent on a previously generated exam."""
    try:
        from core.ai_engine import get_async_openai_client
        from core.integrity_agent import run_integrity_check
        client = get_async_openai_client()
        report = await run_integrity_check(
            req.exam_data,
            client=client,
            ai_check=req.ai_check,
            ai_sample_size=req.ai_sample_size,
        )
        return report
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class ImageModelTestRequest(BaseModel):
    model: str = "chatgpt-image"        # only chatgpt-image
    prompt: str = "a red apple, simple illustration"
    size: str = "1024x1024"
    quality: str = "low"              # low | standard | hd
    n: int = 1

@app.post("/api/test-image-model")
async def test_image_model(req: ImageModelTestRequest):
    """Test the chatgpt-image generation model and return the result or a detailed error."""
    import base64, time
    from pathlib import Path
    start = time.time()

    from core.ai_engine import get_async_openai_client
    client = get_async_openai_client()
    try:
        # Internally map chatgpt-image to gpt-image-1
        model_id = "gpt-image-1"
        kwargs = dict(model=model_id, prompt=req.prompt, size=req.size, n=req.n)
        kwargs["quality"] = req.quality

        response = await client.images.generate(**kwargs)
        elapsed = round(time.time() - start, 2)
        img_data = response.data[0]

        b64 = None
        url = None
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            b64 = img_data.b64_json
            out_dir = Path(BASE_DIR) / "static" / "nursery_imgs"
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = f"_test_chatgpt_image.png"
            (out_dir / fname).write_bytes(base64.b64decode(b64))
            url = f"http://localhost:8000/static/nursery_imgs/{fname}"
        elif hasattr(img_data, "url") and img_data.url:
            url = img_data.url

        return {"success": True, "url": url, "elapsed": elapsed, "model": "chatgpt-image",
                "revised_prompt": getattr(img_data, "revised_prompt", None)}
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        return {"success": False, "error": str(e), "elapsed": elapsed, "model": "chatgpt-image"}

# ── Admin Audit Logs Endpoint ──
from sqlalchemy import select, desc
import uuid

@app.get("/api/admin/audit-logs", dependencies=[Depends(require_role(["admin"]))])
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    try:
        from core.models import async_session_maker, AuditLog, User
        async with async_session_maker() as session:
            query = select(AuditLog, User.email).outerjoin(User, AuditLog.user_id == User.id).order_by(desc(AuditLog.timestamp))
            if user_id:
                try:
                    uid = uuid.UUID(user_id)
                    query = query.where(AuditLog.user_id == uid)
                except ValueError:
                    pass
            if action:
                query = query.where(AuditLog.action == action)
            
            query = query.limit(limit).offset(offset)
            results = await session.execute(query)
            
            logs = []
            for row in results.all():
                log_item, email = row
                logs.append({
                    "id": str(log_item.id),
                    "user_id": str(log_item.user_id) if log_item.user_id else None,
                    "user_email": email or "Guest/System",
                    "action": log_item.action,
                    "timestamp": log_item.timestamp.isoformat(),
                    "details": log_item.details
                })
            return {"logs": logs}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/library")
def get_library():
    return load_projects()

@app.get("/api/syllabus/config")
def get_config():
    from core.syllabus_master import MASTER_SYLLABUS
    return {
        "subjects": ALL_SUBJECTS,
        "levels": ALL_LEVELS,
        "syllabus": MASTER_SYLLABUS
    }

@app.get("/api/analytics/global")
def global_analytics():
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    import chromadb
    client = chromadb.PersistentClient(path=DB_DIR)
    col = client.get_or_create_collection(name="exam_syllabus_collection")
    
    summary = {}
    for s in ALL_SUBJECTS:
        summary[s] = {}
        for l in ALL_LEVELS:
            master = get_master_topics(s, l)
            if not master: continue
            
            # Create naming variants to catch 'P7', 'Primary 7', etc.
            short_l = ""
            if "Primary" in l: short_l = f"P{l.split()[-1]}"
            elif "Senior" in l: short_l = f"S{l.split()[-1]}"
            
            variants = [l, short_l, l.upper(), l.lower(), short_l.lower()] if short_l else [l]
            variants = list(set([v for v in variants if v]))
            
            # Query targeted count and data for this bucket
            results = col.get(
                where={"$and": [
                    {"subject": {"$in": [s, s.lower(), s.upper()]}},
                    {"level": {"$in": variants}}
                ]},
                include=["documents", "metadatas"],
                limit=1000
            )
            
            docs = results["documents"] or []
            metas = results["metadatas"] or []
            
            found = set()
            found_sources = {}
            for doc, meta in zip(docs, metas):
                text = " ".join([meta.get("filename", ""), meta.get("topic", ""), (doc or "")[:200]]).lower()
                fname = meta.get("filename", "Unknown Source")
                for t in master:
                    if t.lower() in text:
                        found.add(t)
                        if t not in found_sources: found_sources[t] = []
                        if fname not in found_sources[t]: found_sources[t].append(fname)
            
            level_chunks = len(results["ids"])
            summary[s][l] = {
                "coverage": round((len(found) / len(master)) * 100, 1) if master else 0,
                "topics_found": len(found),
                "topics_total": len(master),
                "chunk_count": level_chunks,
                "found_list": list(found),
                "missing_list": [t for t in master if t not in found],
                "found_sources": found_sources
            }
    
    return summary

@app.get("/api/analytics/audit")
async def global_level_audit(subject: str, level: str):
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    import chromadb
    client = chromadb.PersistentClient(path=DB_DIR)
    col = client.get_or_create_collection(name="exam_syllabus_collection")
    
    # Matching variants
    short_l = ""
    if "Primary" in level: short_l = f"P{level.split()[-1]}"
    elif "Senior" in level: short_l = f"S{level.split()[-1]}"
    variants = list(set([v for v in [level, short_l, level.upper(), level.lower()] if v]))
    
    results = col.get(
        where={"$and": [
            {"subject": {"$in": [subject, subject.lower(), subject.upper()]}},
            {"level": {"$in": variants}}
        ]},
        include=["documents"],
        limit=100
    )
    
    combined_content = " ".join(results["documents"] or [])
    if not combined_content.strip():
        return {"error": f"No content found for {subject} {level} (Tried variants: {variants})"}
        
    analysis = await analyze_pedagogy(combined_content, subject, level)
    return analysis

@app.get("/api/ingestion/stats")
def ingestion_stats():
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    st_stats = get_ingest_stats()
    
    total_chunks = 0
    try:
        import chromadb
        client = chromadb.PersistentClient(path=DB_DIR)
        col = client.get_or_create_collection(name="exam_syllabus_collection")
        total_chunks = col.count()
    except Exception: pass

    return {
        "total_chunks": total_chunks,
        "total_files": st_stats["total_files"],
        "embedded_files": st_stats["embedded_files"],
        "error_count": st_stats["error_count"],
        "errors": st_stats["errors"]
    }

class ChatRequest(BaseModel):
    messages: List[dict]
    subject: Optional[str] = "General"
    level: Optional[str] = "Standard"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await chat_response(req.messages, req.subject, req.level)
        return {"response": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── INSIGHTS: Coverage heatmap ──
@app.get("/api/insights/coverage")
def insights_coverage(subject: str, level: str):
    """Returns per-topic chunk density for the Insights knowledge bank heatmap."""
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=DB_DIR)
        col = client.get_or_create_collection(name="exam_syllabus_collection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    master = get_master_topics(subject, level)
    if not master:
        return {"coverage_percent": 0, "found_count": 0, "total_count": 0, "topic_density": {}}

    # Build level variants
    short_l = ""
    if "Primary" in level: short_l = f"P{level.split()[-1]}"
    elif "Senior" in level: short_l = f"S{level.split()[-1]}"
    variants = list(set([v for v in [level, short_l, level.upper(), level.lower()] if v]))

    try:
        results = col.get(
            where={"$and": [
                {"subject": {"$in": [subject, subject.lower(), subject.upper()]}},
                {"level": {"$in": variants}}
            ]},
            include=["documents", "metadatas"],
            limit=2000
        )
    except Exception:
        results = {"documents": [], "metadatas": [], "ids": []}

    docs = results.get("documents") or []
    metas = results.get("metadatas") or []

    # Count how many chunks match each topic keyword
    topic_density = {}
    for t in master:
        count = 0
        for doc, meta in zip(docs, metas):
            text = " ".join([
                meta.get("filename", ""), meta.get("topic", ""), (doc or "")[:300]
            ]).lower()
            if t.lower() in text:
                count += 1
        topic_density[t] = count

    found_count = sum(1 for c in topic_density.values() if c > 0)
    total_count = len(master)
    coverage_percent = round((found_count / total_count) * 100, 1) if total_count else 0

    return {
        "coverage_percent": coverage_percent,
        "found_count": found_count,
        "total_count": total_count,
        "topic_density": topic_density
    }

# ── INSIGHTS: Drilldown — show raw fragments for a topic ──
@app.get("/api/knowledge/drilldown")
def knowledge_drilldown(topic: str, subject: str, level: str):
    """Returns raw knowledge-base fragments that match a given topic."""
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=DB_DIR)
        col = client.get_or_create_collection(name="exam_syllabus_collection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    short_l = ""
    if "Primary" in level: short_l = f"P{level.split()[-1]}"
    elif "Senior" in level: short_l = f"S{level.split()[-1]}"
    variants = list(set([v for v in [level, short_l, level.upper(), level.lower()] if v]))

    try:
        results = col.get(
            where={"$and": [
                {"subject": {"$in": [subject, subject.lower(), subject.upper()]}},
                {"level": {"$in": variants}}
            ]},
            include=["documents", "metadatas"],
            limit=500
        )
    except Exception:
        return {"topic": topic, "fragments": []}

    docs = results.get("documents") or []
    metas = results.get("metadatas") or []

    fragments = []
    for doc, meta in zip(docs, metas):
        if topic.lower() in (doc or "").lower():
            fragments.append({
                "content": (doc or "")[:400],
                "source": meta.get("filename", "Unknown"),
                "page": meta.get("page", "—")
            })
        if len(fragments) >= 10:
            break

    return {"topic": topic, "fragments": fragments}

@app.get("/api/syllabus/graph")
def get_syllabus_graph_endpoint():
    from core.syllabus_master import get_syllabus_graph
    pkg = get_syllabus_graph()
    
    # Format graph for front-end rendering
    nodes = []
    for (subj, lev, top), data in pkg.graph.items():
        nodes.append({
            "subject": subj,
            "level": lev,
            "topic": top,
            "complexity": data["complexity"],
            "skills": data["skills"],
            "prereqs": [{"subject": ps, "level": pl, "topic": pt} for ps, pl, pt in data["prereqs"]]
        })
    return {"nodes": nodes}

# ── INSIGHTS: Quick-Index ──
class QuickIndexRequest(BaseModel):
    topic: str
    subject: str
    level: str

@app.post("/api/knowledge/quick-index")
async def knowledge_quick_index(req: QuickIndexRequest):
    """Generates and stores an AI-synthesised summary for an un-indexed syllabus topic."""
    import chromadb, uuid
    DB_DIR = os.path.join(BASE_DIR, "chroma_db")
    client_ai = get_openai_client()

    prompt = f"""You are an expert curriculum author for {req.subject} {req.level}.
Write a concise, factual 3-paragraph knowledge summary for the topic: "{req.topic}".
Cover: key concepts, common exam question angles, and real-world applications.
Use clear academic language suitable for teachers preparing exam content."""

    try:
        resp = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        content = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI synthesis failed: {e}")

    # Store in ChromaDB
    try:
        client_db = chromadb.PersistentClient(path=DB_DIR)
        col = client_db.get_or_create_collection(name="exam_syllabus_collection")
        col.add(
            documents=[content],
            metadatas=[{
                "subject": req.subject,
                "level": req.level,
                "topic": req.topic,
                "filename": f"AI-Synthesised: {req.topic}",
                "page": "AI"
            }],
            ids=[str(uuid.uuid4())]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {e}")

    return {"preview": content[:200] + "…", "topic": req.topic, "status": "indexed"}


@app.post("/api/export/docx")
async def export_docx_endpoint(req: GenerateRequest):
    try:
        # Use content_override if present, otherwise we can't export (need the raw data)
        if not req.content_override:
            raise HTTPException(status_code=400, detail="Raw content data is required for export.")
            
        term_val = req.term
        term_roman = "I"
        if "Term 2" in term_val: term_roman = "II"
        elif "Term 3" in term_val: term_roman = "III"
        elif "BOT" in term_val or "MOT" in term_val or "EOT" in term_val:
             term_roman = term_val # Keep as is if it's just a period
        exam_type = "BEGINNING OF"
        if "(MOT)" in term_val or "MOT" in term_val: exam_type = "MIDDLE OF"
        elif "(EOT)" in term_val or "EOT" in term_val: exam_type = "END OF"

        config = {
            "brand_name": req.brand_name,
            "subject": req.subject,
            "level": req.level,
            "term": req.term,
            "term_roman": term_roman,
            "exam_type": exam_type,
            "exam_year": "2026",
            "duration": req.duration,
            "mode": req.mode
        }
        
        docx_stream = generate_docx_stream(req.content_override, config)
        
        filename = f"EduQuest_{req.subject.replace(' ', '_')}_{req.level.replace(' ', '_')}.docx"
        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mark")
async def mark_endpoint(data: dict):
    student_answer = data.get("student_answer")
    marking_guide = data.get("marking_guide")
    subject = data.get("subject", "General")
    level = data.get("level", "Standard")
    
    if not student_answer or not marking_guide:
        raise HTTPException(status_code=400, detail="Missing student answer or marking guide.")
        
    try:
        result = await mark_student_work(student_answer, marking_guide, subject, level)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import uuid
from pathlib import Path
from typing import List

@app.post("/api/assess/vision")
async def assess_vision_endpoint(
    files: List[UploadFile] = File(...),
    subject: str = Form(...),
    level: str = Form(...),
    strictness: int = Form(5)
):
    try:
        out_dir = Path(BASE_DIR) / "static" / "uploads"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        base64_images = []
        image_urls = []
        
        for file in files:
            file_bytes = await file.read()
            filename = f"scan_{uuid.uuid4().hex[:8]}.jpg"
            file_path = out_dir / filename
            with open(file_path, "wb") as f:
                f.write(file_bytes)
                
            image_urls.append(f"http://localhost:8000/static/uploads/{filename}")
            base64_images.append(base64.b64encode(file_bytes).decode('utf-8'))
            
        from core.ai_engine import get_async_openai_client
        client = get_async_openai_client()
        
        strictness_prompt = ""
        if strictness <= 3:
            strictness_prompt = "MARKING POLICY: Extremely Lenient. Give the student the benefit of the doubt. Ignore minor spelling, punctuation, or formatting errors. Award partial credit generously if the core concept is understood."
        elif strictness >= 8:
            strictness_prompt = "MARKING POLICY: Extremely Strict. Dock points for any spelling or grammatical errors. Answers must be precise. No partial credit unless explicitly warranted."
        else:
            strictness_prompt = "MARKING POLICY: Standard. Follow typical curriculum guidelines for fairness and accuracy."
        
        prompt = f"""
        You are an automated grading Vision AI for {subject} {level}.
        Analyze these uploaded pages of a student's exam paper or worksheet.
        Extract the student's name if present. Grade all the visible answers across all pages.
        
        {strictness_prompt}
        
        You must generate a detailed grading report. 
        Format your response beautifully in HTML, using <h2>, <h3>, <ul>, <li>, <b>, <i>, and HTML <table> for the score summary. Make sure to use Tailwind classes in the HTML for styling if possible, but basic HTML tags are fine.
        
        Structure it EXACTLY like this example:
        <p>Based on the visible portion of the {subject} {level} exam, here is the grading breakdown for [Student Name].</p>
        <p>Since questions X through Y are left blank...</p>
        
        <h2 style="font-size: 1.5em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em;"><i>Section A: Sub-section I</i></h2>
        <h3 style="font-size: 1.17em; font-weight: bold; margin-bottom: 0.5em;"><i>Questions 1-10: Fill the gaps with the correct form of the word given in brackets</i></h3>
        <ul style="list-style-type: disc; padding-left: 20px; margin-bottom: 1em;">
            <li style="margin-bottom: 0.5em;">
                <i>1. The soldiers are tried to save the flood victims. (try)</i>
                <ul style="list-style-type: circle; padding-left: 20px; margin-top: 0.25em;"><li>Incorrect. The continuous tense is required here: <i>trying</i> (are trying).</li></ul>
            </li>
        </ul>
        
        <h2 style="font-size: 1.5em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em;"><i>Score Summary</i></h2>
        <table style="width:100%; border-collapse: collapse; margin-bottom: 1em;" border="1">
            <thead><tr style="background-color: #f3f4f6;"><th style="padding: 8px; border: 1px solid #e5e7eb;">Section</th><th style="padding: 8px; border: 1px solid #e5e7eb;">Correct Answers</th><th style="padding: 8px; border: 1px solid #e5e7eb;">Total Questions</th><th style="padding: 8px; border: 1px solid #e5e7eb;">Score</th></tr></thead>
            <tbody><tr><td style="padding: 8px; border: 1px solid #e5e7eb;"><i>Questions 1-10</i></td><td style="padding: 8px; border: 1px solid #e5e7eb;">7</td><td style="padding: 8px; border: 1px solid #e5e7eb;">10</td><td style="padding: 8px; border: 1px solid #e5e7eb;">7 / 10</td></tr></tbody>
        </table>
        
        <p><i>Teacher's Note:</i> [Provide a highly detailed teacher's report. You MUST break this down into specific "Strengths" and "Weaknesses" based on the student's answers, offering actionable feedback for improvement.]</p>
        
        You MUST return ONLY the raw HTML string. Do NOT wrap it in JSON. Do NOT include markdown blocks like ```html. Just return the raw HTML code.
        """
        
        # Build multi-image content array
        content_array = [{"type": "text", "text": prompt}]
        for b64 in base64_images:
            content_array.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"
                }
            })
            
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": content_array
                }
            ],
            max_tokens=4000
        )
        
        result_json = {
            "report_html": response.choices[0].message.content,
            "imageUrls": image_urls
        }
        
        return result_json
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Mount static uploads
uploads_dir = Path(BASE_DIR) / "static" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
