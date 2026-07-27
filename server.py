import os
import sys
import json
import base64
import uuid
import zipfile
import io
from typing import Optional, List
from pathlib import Path

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

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select

from contextlib import asynccontextmanager
from core.models import create_db_and_tables, async_session_maker, Tenant, AcademicGroup, Student, AssessmentBatch, StudentResult
from core.syllabus_master import ALL_SUBJECTS, ALL_LEVELS
from core.scanner_service import detect_scanners, detect_scanners_cached, scan_page, is_sane_installed, is_wia_available, ScannerDevice
import sys as _sys

async def fix_existing_scores():
    """Recalculates any legacy StudentResult.total_score and normalizes hardcoded localhost URLs to relative URLs."""
    async with async_session_maker() as session:
        query = select(StudentResult)
        res = await session.execute(query)
        all_results = res.scalars().all()
        
        for r in all_results:
            # 1. Normalize hardcoded http://localhost:8000 image URLs to relative URLs
            if r.paper_images_urls:
                updated_urls = {}
                changed = False
                for k, u in dict(r.paper_images_urls).items():
                    if isinstance(u, str) and u.startswith("http://localhost:8000"):
                        updated_urls[k] = u.replace("http://localhost:8000", "")
                        changed = True
                    else:
                        updated_urls[k] = u
                if changed:
                    r.paper_images_urls = updated_urls

            # 2. Recalculate any legacy total_score > 100
            if r.total_score is not None and r.total_score > 100:
                html = r.raw_extracted_html or ""
                match = re.search(r'(\d+)\s*/\s*(\d+)', html)
                if match:
                    pts = float(match.group(1))
                    max_pts = float(match.group(2))
                    if max_pts > 0:
                        r.total_score = min(100, max(0, round((pts / max_pts) * 100)))
                else:
                    r.total_score = 100

        await session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    await fix_existing_scores()
    yield

app = FastAPI(title="Edulytics AI Engine - Standalone", version="1.0.0", lifespan=lifespan)

# ── CORS — allow production domains (edumerc.net, edulytics.net) & dev server ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://edumerc.net",
        "https://www.edumerc.net",
        "http://edumerc.net",
        "http://www.edumerc.net",
        "https://edulytics.net",
        "https://www.edulytics.net",
        "http://edulytics.net",
        "http://www.edulytics.net",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve Uploaded Scans ──
uploads_dir = Path(BASE_DIR) / "static" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# ── Pydantic Request Models ──
class StudentOnboard(BaseModel):
    full_name: str
    index_number: Optional[str] = None

class AcademicGroupOnboard(BaseModel):
    level: str
    stream: str
    students: List[StudentOnboard] = []

class OnboardingRequest(BaseModel):
    school_name: str
    groups: List[AcademicGroupOnboard] = []

class StudentCreateRequest(BaseModel):
    full_name: str
    index_number: Optional[str] = None

class BatchCreateRequest(BaseModel):
    academic_group_id: str
    subject: str
    exam_type: str
    mode: Optional[str] = "worksheet"

class AssignStudentRequest(BaseModel):
    student_id: str

async def generate_unique_index_number(session, prefix: str = "STU") -> str:
    """
    Generates a guaranteed unique student index number (e.g. STU-2026-0001, STU-2026-0002).
    """
    from datetime import datetime
    current_year = datetime.utcnow().year
    
    query = select(Student.index_number).where(
        Student.index_number.like(f"{prefix}-{current_year}-%")
    )
    res = await session.execute(query)
    existing_indices = set(idx for idx in res.scalars().all() if idx)
    
    seq = len(existing_indices) + 1
    while True:
        candidate = f"{prefix}-{current_year}-{seq:04d}"
        if candidate not in existing_indices:
            check_q = select(Student.id).where(Student.index_number == candidate)
            check_res = await session.execute(check_q)
            if not check_res.scalar_one_or_none():
                return candidate
        seq += 1

# ── Tenant Onboarding Endpoint ──
@app.post("/api/v1/tenant/onboard")
async def onboard_tenant(req: OnboardingRequest):
    async with async_session_maker() as session:
        tenant = Tenant(name=req.school_name)
        session.add(tenant)
        await session.flush()
        
        for group_req in req.groups:
            group = AcademicGroup(
                tenant_id=tenant.id,
                level=group_req.level,
                stream=group_req.stream
            )
            session.add(group)
            await session.flush()
            
            for stu_req in group_req.students:
                idx_num = (stu_req.index_number or "").strip()
                if not idx_num:
                    idx_num = await generate_unique_index_number(session)
                else:
                    # Check collision
                    coll_check = await session.execute(select(Student.id).where(Student.index_number == idx_num))
                    if coll_check.scalar_one_or_none():
                        idx_num = await generate_unique_index_number(session)

                student = Student(
                    academic_group_id=group.id,
                    full_name=stu_req.full_name,
                    index_number=idx_num
                )
                session.add(student)
                
        await session.commit()
        return {"tenant_id": str(tenant.id), "message": "Onboarding successful"}

# ── Roster & Tenant Dashboard Endpoints ──
@app.get("/api/v1/tenant/list")
async def list_tenants():
    async with async_session_maker() as session:
        query = select(Tenant).order_by(Tenant.name)
        res = await session.execute(query)
        tenants = res.scalars().all()
        return [{"id": str(t.id), "name": t.name} for t in tenants]

class GroupCreateRequest(BaseModel):
    level: str
    stream: str

@app.get("/api/v1/tenant/{tenant_id}/groups")
async def list_academic_groups(tenant_id: str):
    async with async_session_maker() as session:
        query = select(AcademicGroup).where(AcademicGroup.tenant_id == uuid.UUID(tenant_id))
        res = await session.execute(query)
        groups = res.scalars().all()
        return [{"id": str(g.id), "level": g.level, "stream": g.stream} for g in groups]

@app.post("/api/v1/tenant/{tenant_id}/groups")
async def create_academic_group(tenant_id: str, req: GroupCreateRequest):
    async with async_session_maker() as session:
        group = AcademicGroup(
            tenant_id=uuid.UUID(tenant_id),
            level=req.level,
            stream=req.stream
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return {"id": str(group.id), "level": group.level, "stream": group.stream}


@app.get("/api/v1/academic-group/{group_id}/students")
async def list_students(group_id: str):
    async with async_session_maker() as session:
        query = select(Student).where(Student.academic_group_id == uuid.UUID(group_id)).order_by(Student.full_name)
        res = await session.execute(query)
        students = res.scalars().all()
        return [{"id": str(s.id), "full_name": s.full_name, "index_number": s.index_number} for s in students]

@app.post("/api/v1/academic-group/{group_id}/students")
async def add_student(group_id: str, req: StudentCreateRequest):
    async with async_session_maker() as session:
        idx_num = (req.index_number or "").strip()
        if not idx_num:
            idx_num = await generate_unique_index_number(session)
        else:
            coll_q = select(Student.id).where(Student.index_number == idx_num)
            coll_res = await session.execute(coll_q)
            if coll_res.scalar_one_or_none():
                raise HTTPException(400, f"Index number '{idx_num}' is already assigned to another student. Must be unique.")

        student = Student(
            academic_group_id=uuid.UUID(group_id),
            full_name=req.full_name,
            index_number=idx_num
        )
        session.add(student)
        await session.commit()
        await session.refresh(student)
        return {"id": str(student.id), "full_name": student.full_name, "index_number": student.index_number}


@app.get("/api/v1/academic-group/{group_id}/export-roster-csv")
async def export_roster_csv(group_id: str):
    """
    Exports the enrolled student class roster as a CSV file.
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io as _io

    async with async_session_maker() as session:
        g_uuid = uuid.UUID(group_id)
        group = await session.get(AcademicGroup, g_uuid)
        if not group:
            raise HTTPException(404, "Class group not found")
            
        tenant = await session.get(Tenant, group.tenant_id)
        tenant_name = tenant.name if tenant else "School"
        
        query = select(Student).where(Student.academic_group_id == g_uuid).order_by(Student.full_name)
        res = await session.execute(query)
        students = res.scalars().all()

        output = _io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Index Number", "Student Full Name", "Academic Level", "Class Stream", "School Name"])

        for s in students:
            writer.writerow([
                s.index_number or "—",
                s.full_name,
                group.level,
                group.stream,
                tenant_name
            ])

        output.seek(0)
        filename = f"Roster_{group.level}_{group.stream}_{tenant_name.replace(' ', '_')}.csv"
        return StreamingResponse(
            _io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

# ── Gradebook & Batch History Endpoints ──
@app.get("/api/v1/assessment/batches")
async def list_batches():
    async with async_session_maker() as session:
        query = select(AssessmentBatch, AcademicGroup, Tenant).join(
            AcademicGroup, AssessmentBatch.academic_group_id == AcademicGroup.id
        ).join(
            Tenant, AcademicGroup.tenant_id == Tenant.id
        ).order_by(AssessmentBatch.created_at.desc())
        res = await session.execute(query)
        rows = res.all()
        
        batches_data = []
        for batch, group, tenant in rows:
            batches_data.append({
                "id": str(batch.id),
                "academic_group_id": str(batch.academic_group_id),
                "level": group.level,
                "stream": group.stream,
                "tenant_name": tenant.name,
                "subject": batch.subject,
                "exam_type": batch.exam_type,
                "status": batch.status,
                "created_at": batch.created_at.isoformat()
            })
        return batches_data

@app.get("/api/v1/assessment/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    try:
        batch_uuid = uuid.UUID(batch_id)
        async with async_session_maker() as session:
            query = select(StudentResult, Student).outerjoin(
                Student, StudentResult.student_id == Student.id
            ).where(StudentResult.batch_id == batch_uuid)
            res = await session.execute(query)
            rows = res.all()
            
            results_data = []
            for result, student in rows:
                results_data.append({
                    "id": str(result.id),
                    "student_id": str(result.student_id) if result.student_id else None,
                    "student_name": student.full_name if student else "Unmatched/Review",
                    "index_number": student.index_number if student else None,
                    "total_score": result.total_score,
                    "ai_remarks": result.ai_remarks,
                    "needs_manual_review": result.needs_manual_review,
                    "paper_images_urls": result.paper_images_urls,
                    "raw_extracted_html": result.raw_extracted_html
                })
            return results_data
    except Exception as e:
        print(f"Error in get_batch_results: {e}")
        return []

# ── Assessment Grading Endpoints ──
@app.post("/api/v1/assessment/batch/create")
async def create_batch(req: BatchCreateRequest):
    async with async_session_maker() as session:
        batch = AssessmentBatch(
            academic_group_id=uuid.UUID(req.academic_group_id),
            subject=req.subject,
            exam_type=req.exam_type,
            mode=req.mode or "worksheet",
            status="Initiated"
        )
        session.add(batch)
        await session.commit()
        await session.refresh(batch)
        return {"batch_id": str(batch.id)}

@app.post("/api/v1/assessment/batch/{batch_id}/upload-master-question")
async def upload_master_question_paper(batch_id: str, files: List[UploadFile] = File(...)):
    out_dir = Path(BASE_DIR) / "static" / "uploads" / batch_id / "master"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    sorted_files = sorted(files, key=lambda f: natural_sort_filename_key(f.filename or ""))
    master_urls = {}
    b64s = []
    
    for idx, file in enumerate(sorted_files):
        file_bytes = await file.read()
        ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
        if ext[1:] not in ["jpg", "jpeg", "png", "webp"]:
            ext = ".jpg"
            
        unique_name = f"master_p{idx+1}_{uuid.uuid4().hex[:6]}{ext}"
        file_path = out_dir / unique_name
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        url = f"/static/uploads/{batch_id}/master/{unique_name}"
        master_urls[f"page{idx+1}"] = url
        b64s.append(base64.b64encode(file_bytes).decode('utf-8'))

    # Extract Question Paper & Marking Guide Structure using Vision AI
    structure = {"questions": []}
    if b64s:
        system_prompt = """
        You are a master examination question paper indexer.
        Extract all questions, sub-questions, question statements, and max mark allocations from this master exam paper.
        
        Return JSON format:
        {
          "exam_title": "Extracted Exam Title",
          "total_marks": 100,
          "questions": [
            {
              "number": "1(a)",
              "question_text": "Full text of question 1a",
              "max_marks": 5
            }
          ]
        }
        """
        payload = [{"type": "text", "text": system_prompt}]
        for p_i, b64_img in enumerate(b64s):
            payload.append({"type": "text", "text": f"\n--- MASTER QUESTION PAPER PAGE {p_i+1} OF {len(b64s)} ---"})
            payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
            
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": payload}],
                max_tokens=4096
            )
            structure = json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Master Question Paper AI Ingestion error: {e}")

    async with async_session_maker() as session:
        batch = await session.get(AssessmentBatch, uuid.UUID(batch_id))
        if batch:
            batch.mode = "answer_sheet"
            batch.master_question_urls = master_urls
            batch.master_exam_structure = structure
            await session.commit()
            
    return {"status": "success", "master_urls": master_urls, "structure": structure}

import re

def natural_sort_filename_key(filename: str) -> list:
    """Natural sort key helper so 'page2.jpg' comes before 'page10.jpg'."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(filename))]

def get_filename_prefix(filename: str) -> str:
    base = os.path.basename(filename)
    name_without_ext, _ = os.path.splitext(base)
    name_without_ext = name_without_ext.strip()
    
    # Pattern A: Matches parenthesized or bracketed page indicators, e.g. " (1)", " (Page 1)", " [2]"
    name = re.sub(r'\s*[\(\[][^\]\)]*?\d+[^\]\)]*?[\)\]]$', '', name_without_ext, flags=re.IGNORECASE)
    
    # Pattern B: Matches trailing delimiters followed by page/p/pg and a number, or just a number
    # E.g. " - Page 1", "_page1", " page 2", " _1", "-2"
    name = re.sub(r'[\s\-_]+(?:page|pg|p)?[\s\-_]*\d+$', '', name, flags=re.IGNORECASE)
    
    return name.strip()

@app.post("/api/v1/assessment/batch/{batch_id}/upload")
async def upload_batch_files(batch_id: str, files: List[UploadFile] = File(...)):
    out_dir = Path(BASE_DIR) / "static" / "uploads" / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Sort files naturally by filename so page2 comes before page10
    sorted_files = sorted(files, key=lambda f: natural_sort_filename_key(f.filename or ""))
    
    groups = {}
    for file in sorted_files:
        prefix = get_filename_prefix(file.filename or "scan")
        if not prefix:
            prefix = "scan"
        
        file_bytes = await file.read()
        ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
        if ext[1:] not in ["jpg", "jpeg", "png", "webp"]:
            ext = ".jpg"
            
        unique_name = f"scan_{uuid.uuid4().hex[:8]}{ext}"
        file_path = out_dir / unique_name
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        url = f"/static/uploads/{batch_id}/{unique_name}"
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append(url)
        
    async with async_session_maker() as session:
        for prefix, urls in groups.items():
            paper_images_urls = {f"page{i+1}": url for i, url in enumerate(urls)}
            result = StudentResult(
                batch_id=uuid.UUID(batch_id),
                paper_images_urls=paper_images_urls,
                needs_manual_review=False
            )
            session.add(result)
        await session.commit()
        
    return {"uploaded_count": len(files)}

@app.post("/api/v1/assessment/batch/{batch_id}/upload-zip")
async def upload_batch_zip(batch_id: str, file: UploadFile = File(...)):
    out_dir = Path(BASE_DIR) / "static" / "uploads" / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    zip_bytes = await file.read()
    
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            # Sort ZIP names naturally to preserve exact page ordering (e.g. page2 before page10)
            sorted_names = sorted(z.namelist(), key=natural_sort_filename_key)
            groups = {}
            extracted_count = 0
            
            for name in sorted_names:
                if name.endswith("/"):
                    continue
                
                base_name = os.path.basename(name)
                if not base_name or base_name.startswith("."):
                    continue
                
                ext = base_name.split(".")[-1].lower()
                if ext not in ["jpg", "jpeg", "png", "webp"]:
                    continue
                
                # Determine group: folder name if present, else filename prefix
                parent_dir = os.path.dirname(name).strip()
                if parent_dir and parent_dir != "." and parent_dir != "/":
                    group_name = os.path.basename(parent_dir)
                else:
                    group_name = get_filename_prefix(base_name)
                
                file_data = z.read(name)
                safe_filename = f"scan_{uuid.uuid4().hex[:8]}.{ext}"
                file_path = out_dir / safe_filename
                with open(file_path, "wb") as f:
                    f.write(file_data)
                
                url = f"/static/uploads/{batch_id}/{safe_filename}"
                
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(url)
                extracted_count += 1
                
            async with async_session_maker() as session:
                for group_name, urls in groups.items():
                    paper_images_urls = {f"page{i+1}": url for i, url in enumerate(urls)}
                    result = StudentResult(
                        batch_id=uuid.UUID(batch_id),
                        paper_images_urls=paper_images_urls,
                        needs_manual_review=False
                    )
                    session.add(result)
                await session.commit()
                
            return {"uploaded_count": extracted_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid zip file: {str(e)}")

async def process_batch_background(batch_id: str):
    from core.ai_engine import get_async_openai_client
    import base64
    import json
    
    client = get_async_openai_client()
    batch_uuid = uuid.UUID(batch_id)
    
    # 1. Fetch metadata and result list in a quick transaction
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if not batch_obj: 
            return
        batch_obj.status = "Processing"
        await session.commit()
        
        subject = batch_obj.subject
        group_id = batch_obj.academic_group_id
        
        # Get all result IDs to process
        query = select(StudentResult.id).where(StudentResult.batch_id == batch_uuid)
        res = await session.execute(query)
        result_ids = res.scalars().all()
# In-memory event stream subscribers per batch
batch_subscribers: dict = {}

async def broadcast_event(batch_id: str, event_type: str, data: dict):
    """
    Pushes real-time SSE events to all connected clients listening to batch_id stream.
    """
    if batch_id in batch_subscribers:
        payload = json.dumps({"type": event_type, "timestamp": data.get("timestamp", ""), **data})
        for q in list(batch_subscribers[batch_id]):
            try:
                await q.put(payload)
            except Exception:
                pass


import difflib

def find_closest_student_match(ocr_name: str, students: list, threshold: float = 0.50):
    """
    Finds the closest matching student from DB roster based on token overlap,
    Levenshtein edit distance ratio, and substring similarity.
    Returns (matched_student_dict, similarity_score).
    """
    if not ocr_name or not str(ocr_name).strip() or not students:
        return None, 0.0

    clean_ocr = re.sub(r'[^a-zA-Z0-9\s]', '', str(ocr_name).lower()).strip()
    ocr_tokens = set(clean_ocr.split())

    best_student = None
    best_score = 0.0

    for st in students:
        full_name = st["full_name"]
        clean_db = re.sub(r'[^a-zA-Z0-9\s]', '', str(full_name).lower()).strip()
        db_tokens = set(clean_db.split())

        # 1. Exact match
        if clean_ocr == clean_db:
            return st, 1.0

        # 2. Token overlap ratio (e.g. "Kizito Mukasa" vs "Mukasa Kizito")
        if ocr_tokens and db_tokens:
            token_intersection = ocr_tokens.intersection(db_tokens)
            token_score = len(token_intersection) / max(len(ocr_tokens), len(db_tokens))
        else:
            token_score = 0.0

        # 3. Levenshtein edit distance ratio
        seq_score = difflib.SequenceMatcher(None, clean_ocr, clean_db).ratio()

        # 4. Substring inclusion boost
        sub_boost = 0.2 if (clean_ocr in clean_db or clean_db in clean_ocr) else 0.0

        final_score = max(token_score, seq_score) + sub_boost

        if final_score > best_score:
            best_score = final_score
            best_student = st

    if best_score >= threshold and best_student:
        return best_student, best_score

    return None, best_score


def generate_html_report_from_json(ai_data: dict, subject: str) -> str:
    """
    Programmatically builds a complete, clean, responsive HTML report
    from structured question objects so zero questions are skipped or truncated.
    """
    student_name = ai_data.get("student_name", "Unknown Student")
    total_score = ai_data.get("score")
    max_possible = ai_data.get("max_possible_score", 100)
    questions = ai_data.get("questions", [])
    qualitative_feedback = ai_data.get("qualitative_feedback", "")
    
    # Sort questions by q_number if present
    try:
        questions = sorted(questions, key=lambda x: int(re.search(r'\d+', str(x.get("q_number", 0))).group() if re.search(r'\d+', str(x.get("q_number", 0))) else 0))
    except Exception:
        pass
        
    score_str = f"{total_score}" if total_score is not None else "N/A"
    
    rows_html = []
    for q in questions:
        q_num = q.get("q_number", "")
        q_text = q.get("question_text", "")
        student_ans = q.get("student_answer", "") or "—"
        status = str(q.get("status", "INCORRECT")).upper()
        score_awarded = q.get("score_awarded", 0)
        max_score = q.get("max_score", 5)
        explanation = q.get("explanation", "")
        alts = q.get("alternative_answers", [])
        remarks = q.get("remarks", "")
        
        # Color coding
        if status in ["CORRECT", "PASS"]:
            status_badge = '<span style="background-color:#dcfce7; color:#15803d; border:1px solid #86efac; padding:2px 8px; font-weight:bold; font-size:11px; display:inline-block;">CORRECT</span>'
        elif status in ["PARTIAL", "HALF"]:
            status_badge = '<span style="background-color:#fef3c7; color:#b45309; border:1px solid #fde047; padding:2px 8px; font-weight:bold; font-size:11px; display:inline-block;">PARTIAL</span>'
        else:
            status_badge = '<span style="background-color:#ffe4e6; color:#be123c; border:1px solid #fecdd3; padding:2px 8px; font-weight:bold; font-size:11px; display:inline-block;">INCORRECT</span>'
            
        alt_html = ""
        if alts and isinstance(alts, list) and len(alts) > 0:
            alt_items = "".join([f'<li style="color:#16a34a; font-weight:600;">{alt}</li>' for alt in alts])
            alt_html = f'<div style="margin-top:4px;"><strong style="font-size:11px; color:#16a34a;">Valid Alternative Answers:</strong><ul style="margin:2px 0 0 16px; padding:0; font-size:11px;">{alt_items}</ul></div>'
            
        rows_html.append(f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 10px; font-weight: bold; vertical-align: top;">Q{q_num}</td>
          <td style="padding: 10px; vertical-align: top;">{q_text}</td>
          <td style="padding: 10px; font-weight: 500; vertical-align: top;">{student_ans}</td>
          <td style="padding: 10px; vertical-align: top;">{status_badge}</td>
          <td style="padding: 10px; font-weight: bold; vertical-align: top;">{score_awarded}/{max_score}</td>
          <td style="padding: 10px; vertical-align: top;">
            <div>{explanation}</div>
            {alt_html}
          </td>
          <td style="padding: 10px; color: #475569; vertical-align: top;">{remarks}</td>
        </tr>
        """)
        
    table_body = "\n".join(rows_html)
    
    html = f"""
    <div style="font-family: inherit; color: inherit; width: 100%;">
      <!-- Executive Summary -->
      <div style="display: flex; gap: 16px; margin-bottom: 24px;">
        <div style="flex: 1; border: 1px solid #e2e8f0; padding: 16px; background: #f8fafc;">
          <div style="font-size: 10px; font-weight: bold; text-transform: uppercase; color: #64748b;">Student Name</div>
          <div style="font-size: 18px; font-weight: bold; margin-top: 4px;">{student_name}</div>
        </div>
        <div style="flex: 1; border: 1px solid #e2e8f0; padding: 16px; background: #f8fafc;">
          <div style="font-size: 10px; font-weight: bold; text-transform: uppercase; color: #64748b;">Subject</div>
          <div style="font-size: 18px; font-weight: bold; margin-top: 4px;">{subject}</div>
        </div>
        <div style="flex: 1; border: 1px solid #fecdd3; padding: 16px; background: #fff1f2;">
          <div style="font-size: 10px; font-weight: bold; text-transform: uppercase; color: #be123c;">Total Score</div>
          <div style="font-size: 20px; font-weight: 900; color: #be123c; margin-top: 4px;">{score_str} / {max_possible}</div>
        </div>
      </div>

      <!-- Question Table -->
      <h3 style="font-size: 16px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">Question-By-Question Grading</h3>
      <table style="width: 100%; text-align: left; border-collapse: collapse; border: 1px solid #e2e8f0; font-size: 12px; margin-bottom: 24px;">
        <thead>
          <tr style="background: #f1f5f9; border-bottom: 1px solid #cbd5e1; font-weight: bold; color: #475569;">
            <th style="padding: 10px; width: 60px;">Q#</th>
            <th style="padding: 10px;">Question Description/Topic</th>
            <th style="padding: 10px;">Student's Response</th>
            <th style="padding: 10px; width: 100px;">Status</th>
            <th style="padding: 10px; width: 80px;">Score</th>
            <th style="padding: 10px;">Detailed Explanation & Alternative Answers</th>
            <th style="padding: 10px;">Teacher/AI Remarks</th>
          </tr>
        </thead>
        <tbody>
          {table_body}
        </tbody>
      </table>

      <!-- Qualitative Feedback -->
      {f'<h3 style="font-size: 16px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">Qualitative Feedback & Key Recommendations</h3><div style="border: 1px solid #fecdd3; border-left: 4px solid #e11d48; background: #fff1f2; padding: 16px; font-size: 13px; line-height: 1.6;">{qualitative_feedback}</div>' if qualitative_feedback else ''}
    </div>
    """
    return html.strip()


def natural_sort_page_key(key: str) -> int:
    """Extracts numeric page suffix (e.g. page_1 -> 1, p2 -> 2) or last integer for strict natural sorting."""
    m = re.search(r'(?:page[_\-]?|p[_\-]?|slide[_\-]?)(\d+)', str(key), re.IGNORECASE)
    if m:
        return int(m.group(1))
    nums = re.findall(r'\d+', str(key))
    return int(nums[-1]) if nums else 0


async def process_batch_background(batch_id: str):
    from core.ai_engine import get_async_openai_client
    import base64
    import json
    import asyncio
    
    client = get_async_openai_client()
    batch_uuid = uuid.UUID(batch_id)
    
    # 1. Fetch metadata and result list in a quick transaction
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if not batch_obj: 
            return
        batch_obj.status = "Processing"
        await session.commit()
        
        subject = batch_obj.subject
        group_id = batch_obj.academic_group_id
        
        # Get all result IDs to process
        query = select(StudentResult.id).where(StudentResult.batch_id == batch_uuid)
        res = await session.execute(query)
        result_ids = res.scalars().all()
        
        # Get all student profiles for fuzzy matching
        st_query = select(Student).where(Student.academic_group_id == group_id)
        st_res = await session.execute(st_query)
        students = [
            {"id": s.id, "full_name": s.full_name} 
            for s in st_res.scalars().all()
        ]

    total_papers = len(result_ids)
    await broadcast_event(batch_id, "batch_started", {"total_papers": total_papers})

    # 2. Worker pool with Semaphore=3 for high-performance disintegrated grading
    semaphore = asyncio.Semaphore(3)
    
    async def grade_single_paper_disintegrated(r_id, paper_idx: int):
        async with semaphore:
            await broadcast_event(batch_id, "paper_start", {
                "paper_id": str(r_id),
                "paper_idx": paper_idx + 1,
                "total_papers": total_papers,
                "phase": "Phase 1: Page Extraction"
            })
            
            async with async_session_maker() as session:
                result = await session.get(StudentResult, r_id)
                if not result or not result.paper_images_urls:
                    return
                paper_images_urls = dict(result.paper_images_urls)
            
            try:
                b64s = []
                sorted_keys = sorted(
                    paper_images_urls.keys(),
                    key=natural_sort_page_key
                )
                for key in sorted_keys:
                    url = paper_images_urls[key]
                    filename = url.split("/")[-1]
                    file_path = Path(BASE_DIR) / "static" / "uploads" / batch_id / filename
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            b64s.append(base64.b64encode(f.read()).decode('utf-8'))
                            
                if not b64s:
                    return

                master_b64s = []
                master_struct_str = ""
                master_rubric_block = ""
                if batch_obj and (batch_obj.mode == "answer_sheet" or batch_obj.master_question_urls or batch_obj.master_exam_structure):
                    if batch_obj.master_question_urls:
                        for m_key in sorted(dict(batch_obj.master_question_urls).keys(), key=natural_sort_page_key):
                            m_url = batch_obj.master_question_urls[m_key]
                            m_filename = m_url.split("/")[-1]
                            m_path = Path(BASE_DIR) / "static" / "uploads" / batch_id / "master" / m_filename
                            if m_path.exists():
                                with open(m_path, "rb") as mf:
                                    master_b64s.append(base64.b64encode(mf.read()).decode('utf-8'))
                    if batch_obj.master_exam_structure:
                        master_struct_str = json.dumps(batch_obj.master_exam_structure, indent=2)
                        master_rubric_block = f"INDEXED MASTER EXAM RUBRIC:\n{master_struct_str}\n"

                # ── PHASE 1: Multi-Page Unified Vision Document OCR & Context Preservation ──
                system_prompt = f"""
                You are a master academic OCR and exam vision engine.
                You are evaluating a {subject} student exam paper consisting of {len(b64s)} pages in exact chronological order (Page 1 of {len(b64s)}, Page 2 of {len(b64s)}, etc.).

                CRITICAL SECONDARY MARKING RULES:
                1. REFER TO MASTER QUESTION PAPER: You MUST evaluate the student's handwritten answers by referring directly to the Master Question Paper images and Indexed Exam Rubric provided.
                2. QUESTION ALIGNMENT: Match each handwritten answer on the student's answer sheet (e.g. "1(a)", "No 2", "Qn 3b") to the corresponding Master Question statement, diagrams, passages, and max mark allocations.
                3. HYBRID FORMAT SUPPORT: For Hybrid exams (Section A Worksheet + Section B Answer Sheet), evaluate Section A questions & student answers printed on front pages, and evaluate Section B/C extended answers either referencing the Master Question Paper (if attached) or directly from the student's written pages.
                4. MULTI-PAGE CONTINUITY: Read all pages together as one continuous answer booklet!
                5. STUDENT NAME: Extract the student's full name from the cover or page header.

                {master_rubric_block}

                Return JSON format:
                {{
                  "student_name": "Extracted Student Name or empty string",
                  "questions": [
                    {{
                      "q_number": "1(a)",
                      "question_text": "Full question statement from Master Question Paper",
                      "student_answer": "Student written answer..."
                    }}
                  ]
                }}
                """

                content_payload = []
                if master_b64s:
                    content_payload.append({
                        "type": "text",
                        "text": f"=== UNIVERSAL MASTER QUESTION PAPER ({len(master_b64s)} PAGES) ===\nRefer directly to these Master Question Paper images to verify questions, passages, diagrams, tables, and max marks:"
                    })
                    for m_i, m_b64 in enumerate(master_b64s):
                        content_payload.append({"type": "text", "text": f"\n--- MASTER QUESTION PAPER PAGE {m_i + 1} OF {len(master_b64s)} ---"})
                        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m_b64}"}})

                content_payload.append({"type": "text", "text": f"\n=== STUDENT ANSWER SCRIPT ({len(b64s)} PAGES) ===\n{system_prompt}"})
                for p_i, b64_img in enumerate(b64s):
                    content_payload.append({"type": "text", "text": f"\n--- STUDENT SCRIPT PAGE {p_i + 1} OF {len(b64s)} ---"})
                    content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})

                doc_data = {"student_name": "", "questions": []}
                for attempt in range(3):
                    try:
                        resp = await client.chat.completions.create(
                            model="gpt-4o",
                            response_format={"type": "json_object"},
                            messages=[{"role": "user", "content": content_payload}],
                            max_tokens=4096
                        )
                        doc_data = json.loads(resp.choices[0].message.content)
                        break
                    except Exception as e:
                        print(f"GPT-4o vision extraction attempt {attempt + 1} failed: {e}")
                        if attempt < 2:
                            await asyncio.sleep(2 ** (attempt + 1))
                        else:
                            try:
                                resp = await client.chat.completions.create(
                                    model="gpt-4o-mini",
                                    response_format={"type": "json_object"},
                                    messages=[{"role": "user", "content": content_payload}],
                                    max_tokens=4096
                                )
                                doc_data = json.loads(resp.choices[0].message.content)
                            except Exception as e2:
                                print(f"Fallback extraction error: {e2}")
                                doc_data = {"student_name": "", "questions": []}

                extracted_name = doc_data.get("student_name", "")
                all_extracted_questions = doc_data.get("questions", [])

                # Ensure question numbers are sorted
                try:
                    all_extracted_questions = sorted(
                        all_extracted_questions,
                        key=lambda x: int(re.search(r'\d+', str(x.get("q_number", 0))).group() if re.search(r'\d+', str(x.get("q_number", 0))) else 0)
                    )
                except Exception:
                    pass

                await broadcast_event(batch_id, "page_extraction_complete", {
                    "paper_id": str(r_id),
                    "paper_idx": paper_idx + 1,
                    "student_name": extracted_name or f"Paper #{paper_idx + 1}",
                    "total_questions_extracted": len(all_extracted_questions),
                    "phase": "Phase 2: Micro-Chunk Grading"
                })

                # If no questions extracted via vision, fallback to chunking empty
                if not all_extracted_questions:
                    all_extracted_questions = [{"q_number": 1, "question_text": "Full Exam Assessment", "student_answer": "Complete"}]

                # ── PHASE 2: Parallel Micro-Batch Grading (Text Chunks of 12) ──
                chunk_size = 12
                question_chunks = [
                    all_extracted_questions[i:i + chunk_size]
                    for i in range(0, len(all_extracted_questions), chunk_size)
                ]

                async def grade_chunk(c_idx: int, q_chunk: list):
                    rubric_ref = f"REFER TO MASTER QUESTION PAPER & MARKING RUBRIC:\n{master_struct_str}\n" if master_struct_str else ""
                    chunk_prompt = f"""
                    You are an expert academic examiner grading chunk {c_idx + 1} of a {subject} exam.
                    
                    {rubric_ref}

                    Grade the following extracted student answers accurately against the Master Question Paper & Rubric:
                    {json.dumps(q_chunk)}

                    Return JSON format:
                    {{
                      "graded_questions": [
                        {{
                          "q_number": 1,
                          "question_text": "Question...",
                          "student_answer": "Answer...",
                          "status": "CORRECT", // "CORRECT", "INCORRECT", or "PARTIAL"
                          "score_awarded": 5,
                          "max_score": 5,
                          "explanation": "Detailed step-by-step reason for mark.",
                          "alternative_answers": ["alternative acceptable answer"],
                          "remarks": "Teacher remark..."
                        }}
                      ]
                    }}
                    """
                    try:
                        resp = await client.chat.completions.create(
                            model="gpt-4o-mini",
                            response_format={"type": "json_object"},
                            messages=[{"role": "user", "content": chunk_prompt}],
                            max_tokens=4096
                        )
                        chunk_res = json.loads(resp.choices[0].message.content)
                        return chunk_res.get("graded_questions", q_chunk)
                    except Exception as e:
                        print(f"Error grading chunk {c_idx+1}: {e}")
                        return q_chunk

                chunk_results = await asyncio.gather(*[grade_chunk(i, chunk) for i, chunk in enumerate(question_chunks)])
                
                graded_all_questions = []
                for c_res in chunk_results:
                    graded_all_questions.extend(c_res)

                # ── PHASE 3: Assembly & Qualitative Feedback Synthesis ──
                total_score = sum(int(q.get("score_awarded", 0)) for q in graded_all_questions)
                max_possible = sum(int(q.get("max_score", 5)) for q in graded_all_questions) or 100

                ai_data = {
                    "student_name": extracted_name or f"Student #{paper_idx + 1}",
                    "score": total_score,
                    "max_possible_score": max_possible,
                    "questions": graded_all_questions,
                    "qualitative_feedback": f"Demonstrates solid overall understanding across {len(graded_all_questions)} evaluated questions."
                }
                
                html = generate_html_report_from_json(ai_data, subject)

                # Advanced fuzzy match OCR student name to closest DB student
                matched_student, match_score = find_closest_student_match(extracted_name, students, threshold=0.50)
                if matched_student:
                    matched_student_id = matched_student["id"]
                    matched_student_name = matched_student["full_name"]
                    matched = True
                    print(f"INFO: Matched OCR name '{extracted_name}' to DB student '{matched_student_name}' (Score: {match_score:.2f})")
                else:
                    matched_student_id = None
                    matched_student_name = extracted_name
                    matched = False

                async with async_session_maker() as session:
                    result_obj = await session.get(StudentResult, r_id)
                    if result_obj:
                        score_pct = min(100, max(0, round((total_score / max_possible) * 100))) if max_possible > 0 else 0
                        result_obj.total_score = score_pct
                        result_obj.raw_extracted_html = html
                        if matched:
                            result_obj.student_id = matched_student_id
                            result_obj.needs_manual_review = False
                        else:
                            result_obj.needs_manual_review = True
                            result_obj.ai_remarks = f"Could not precisely match OCR name: '{extracted_name}' to class roster."
                        await session.commit()

                score_pct_broadcast = min(100, max(0, round((total_score / max_possible) * 100))) if max_possible > 0 else 0
                await broadcast_event(batch_id, "paper_completed", {
                    "paper_id": str(r_id),
                    "paper_idx": paper_idx + 1,
                    "student_name": matched_student_name if matched else extracted_name,
                    "score": score_pct_broadcast,
                    "max_score": max_possible,
                    "questions_count": len(graded_all_questions),
                    "matched": matched,
                    "phase": "Complete"
                })

            except Exception as e:
                print(f"Error processing paper {r_id}: {e}")
                async with async_session_maker() as session:
                    result_obj = await session.get(StudentResult, r_id)
                    if result_obj:
                        result_obj.needs_manual_review = True
                        result_obj.ai_remarks = f"Error processing: {str(e)}"
                        await session.commit()
                await broadcast_event(batch_id, "paper_error", {
                    "paper_id": str(r_id),
                    "paper_idx": paper_idx + 1,
                    "error": str(e)
                })

    # High-performance chunked execution for scale (up to 5,000+ papers)
    CHUNK_SIZE = 5
    for i in range(0, total_papers, CHUNK_SIZE):
        chunk_items = list(enumerate(result_ids))[i:i + CHUNK_SIZE]
        tasks = [
            grade_single_paper_disintegrated(r_id, idx)
            for idx, r_id in chunk_items
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        # Yield to event loop to allow garbage collection & prevent RAM bloat
        await asyncio.sleep(0.1)
                    
    # 3. Mark batch as completed
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if batch_obj:
            batch_obj.status = "Completed"
            try:
                insights = await generate_batch_insights(batch_uuid, session)
                batch_obj.batch_insights = insights
            except Exception as e:
                print(f"Error post-processing batch insights: {e}")
            await session.commit()

    await broadcast_event(batch_id, "batch_complete", {"batch_id": batch_id, "total_papers": total_papers})


@app.get("/api/v1/assessment/batch/{batch_id}/stream")
async def stream_batch_events(batch_id: str):
    """
    Server-Sent Events (SSE) endpoint streaming real-time grading progress to frontend UI.
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        q = asyncio.Queue()
        if batch_id not in batch_subscribers:
            batch_subscribers[batch_id] = []
        batch_subscribers[batch_id].append(q)
        
        try:
            yield f"data: {json.dumps({'type': 'connected', 'batch_id': batch_id})}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=5.0)
                    yield f"data: {payload}\n\n"
                    msg_obj = json.loads(payload)
                    if msg_obj.get("type") == "batch_complete":
                        break
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if batch_id in batch_subscribers and q in batch_subscribers[batch_id]:
                batch_subscribers[batch_id].remove(q)
                if not batch_subscribers[batch_id]:
                    del batch_subscribers[batch_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    )


@app.post("/api/v1/assessment/batch/{batch_id}/process")
async def trigger_batch_process(batch_id: str, background_tasks: BackgroundTasks):
    try:
        batch_uuid = uuid.UUID(batch_id)
    except Exception:
        raise HTTPException(400, "Invalid batch UUID")

    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if not batch_obj:
            raise HTTPException(404, "Batch not found")

    background_tasks.add_task(process_batch_background, batch_id)
    return {"status": "processing_started", "batch_id": batch_id}

@app.get("/api/v1/assessment/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    try:
        batch_uuid = uuid.UUID(batch_id)
        async with async_session_maker() as session:
            batch_obj = await session.get(AssessmentBatch, batch_uuid)
            if not batch_obj: raise HTTPException(404, "Batch not found")
            
            query = select(StudentResult).where(StudentResult.batch_id == batch_uuid)
            res = await session.execute(query)
            results = res.scalars().all()
            
            total = len(results)
            needs_review = sum(1 for r in results if r.needs_manual_review)
            processed = sum(1 for r in results if r.raw_extracted_html is not None or r.ai_remarks is not None)

            paper_summaries = []
            for idx, r in enumerate(results):
                student_name = f"Paper #{idx + 1}"
                if r.student_id:
                    st = await session.get(Student, r.student_id)
                    if st:
                        student_name = f"{st.first_name} {st.last_name}".strip()
                
                paper_summaries.append({
                    "paper_idx": idx + 1,
                    "result_id": str(r.id),
                    "student_name": student_name,
                    "score": r.total_score,
                    "max_score": getattr(r, 'max_score', 100),
                    "status": "completed" if r.total_score is not None else ("grading" if r.raw_extracted_html else "pending"),
                    "needs_review": r.needs_manual_review
                })
            
            return {
                "status": batch_obj.status,
                "total": total,
                "processed": processed,
                "needs_review": needs_review,
                "papers": paper_summaries
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_batch_status: {e}")
        return {
            "status": "Processing",
            "total": 0,
            "processed": 0,
            "needs_review": 0,
            "papers": []
        }

@app.patch("/api/v1/assessment/result/{result_id}/assign-student")
async def assign_student_to_result(result_id: str, req: AssignStudentRequest):
    async with async_session_maker() as session:
        res_obj = await session.get(StudentResult, uuid.UUID(result_id))
        if not res_obj: raise HTTPException(404, "Result not found")
        
        res_obj.student_id = uuid.UUID(req.student_id)
        res_obj.needs_manual_review = False
        res_obj.ai_remarks = "Resolved manually by teacher."
        await session.commit()
        return {"status": "success"}

@app.get("/api/syllabus/config")
def get_config(level: Optional[str] = None):
    from core.syllabus_master import MASTER_SYLLABUS, get_subjects_for_level
    subjects = get_subjects_for_level(level) if level else ALL_SUBJECTS
    return {
        "subjects": subjects,
        "all_subjects": ALL_SUBJECTS,
        "levels": ALL_LEVELS,
        "syllabus": MASTER_SYLLABUS
    }

# ── Analytics Endpoints ──

@app.get("/api/v1/analytics/overview")
async def analytics_overview():
    """Returns platform-wide summary stats for the analytics dashboard."""
    async with async_session_maker() as session:
        tenants_res = await session.execute(select(Tenant))
        tenants = tenants_res.scalars().all()

        students_res = await session.execute(select(Student))
        students = students_res.scalars().all()

        batches_res = await session.execute(select(AssessmentBatch))
        batches = batches_res.scalars().all()

        graded_res = await session.execute(
            select(StudentResult).where(StudentResult.total_score != None)
        )
        graded = graded_res.scalars().all()

        avg_score = round(sum(r.total_score for r in graded) / len(graded), 1) if graded else 0
        needs_review_res = await session.execute(
            select(StudentResult).where(StudentResult.needs_manual_review == True)
        )
        needs_review = needs_review_res.scalars().all()

        return {
                    "total_schools": len(tenants),
                    "total_students": len(students),
                    "total_batches": len(batches),
                    "total_graded": len(graded),
                    "average_score": avg_score,
                    "needs_review_count": len(needs_review),
                    "completed_batches": sum(1 for b in batches if b.status == "Completed"),
                }

@app.get("/api/v1/analytics/score-distribution/{batch_id}")
async def score_distribution(batch_id: str):
    """Returns score distribution buckets for a batch (for charting)."""
    try:
        batch_uuid = uuid.UUID(batch_id)
        async with async_session_maker() as session:
            query = select(StudentResult).where(
                StudentResult.batch_id == batch_uuid,
                StudentResult.total_score != None
            )
            res = await session.execute(query)
            results = res.scalars().all()

            buckets = {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
            for r in results:
                s = r.total_score
                if s < 50: buckets["0-49"] += 1
                elif s < 60: buckets["50-59"] += 1
                elif s < 70: buckets["60-69"] += 1
                elif s < 80: buckets["70-79"] += 1
                elif s < 90: buckets["80-89"] += 1
                else: buckets["90-100"] += 1

            scores = [r.total_score for r in results]
            avg = round(sum(scores) / len(scores), 1) if scores else 0
            highest = max(scores) if scores else 0
            lowest = min(scores) if scores else 0

            return {
                "buckets": buckets,
                "average": avg,
                "highest": highest,
                "lowest": lowest,
                "count": len(results)
            }
    except Exception as e:
        print(f"Error in score_distribution: {e}")
        return {
            "buckets": {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0},
            "average": 0,
            "highest": 0,
            "lowest": 0,
            "count": 0
        }


async def generate_batch_insights(batch_uuid: uuid.UUID, session) -> str:
    """
    Generate general AI recommendations, improvements and insights for a batch based on student results.
    """
    from core.models import StudentResult, AssessmentBatch, Student, AcademicGroup
    
    # 1. Fetch batch
    batch_obj = await session.get(AssessmentBatch, batch_uuid)
    if not batch_obj:
        return ""
        
    group_obj = await session.get(AcademicGroup, batch_obj.academic_group_id)
    level_str = group_obj.level if group_obj else "Unknown"
    stream_str = group_obj.stream if group_obj else "Unknown"
        
    # 2. Fetch results
    results_q = select(StudentResult, Student).outerjoin(
        Student, StudentResult.student_id == Student.id
    ).where(StudentResult.batch_id == batch_uuid)
    results_res = await session.execute(results_q)
    rows = results_res.all()
    
    if not rows:
        return "<p class='text-xs text-foreground/50 italic'>No student results found for this batch to analyze.</p>"
        
    # 3. Build summary
    results_summary = []
    scores = []
    for r, student in rows:
        remarks = r.ai_remarks or ""
        score_val = r.total_score
        student_name = student.full_name if student else "Unmatched/Review"
        if score_val is not None:
            scores.append(score_val)
        results_summary.append(f"- Student: {student_name}, Score: {score_val if score_val is not None else 'N/A'}%, Remarks: {remarks}")
        
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    highest = max(scores) if scores else 0
    lowest = min(scores) if scores else 0
    
    summary_header = (
        f"Batch Overview:\n"
        f"- Subject: {batch_obj.subject}\n"
        f"- Level/Stream: {level_str} {stream_str}\n"
        f"- Class Average Score: {avg}%\n"
        f"- Highest Score: {highest}%\n"
        f"- Lowest Score: {lowest}%\n"
        f"- Total Students Graded: {len(rows)}\n\n"
        f"Individual Student Breakdowns:\n"
    )
    
    results_summary_text = summary_header + "\n".join(results_summary)
    
    # 4. Call LLM with automatic retries and model fallbacks for 5xx/transient errors
    try:
        from core.ai_engine import get_async_openai_client
        client = get_async_openai_client()
        if not client:
            return "<p class='text-xs text-red-500 italic'>OpenAI client not initialized.</p>"
            
        prompt = f"""
        You are an expert educational data analyst.
        Analyze the following student performance results for a {batch_obj.subject} assessment ({batch_obj.exam_type}) for class {level_str} {stream_str}.
        
        {results_summary_text}
        
        Provide a comprehensive, beautiful HTML report containing batch-level insights.
        You MUST wrap each section in specific HTML tags as follows:
        
        1. General Performance Insight:
        Wrap in: <section id="general-insight"><h3>General Performance Insight</h3><p>...</p></section>
        
        2. Key Strengths:
        Wrap in: <section id="key-strengths"><h3>Key Strengths</h3><ul><li>...</li></ul></section>
        
        3. Key Weaknesses & Areas for Improvement:
        Wrap in: <section id="key-weaknesses"><h3>Key Weaknesses & Areas for Improvement</h3><ul><li>...</li></ul></section>
        
        4. Actionable AI Recommendations:
        Wrap in: <section id="actionable-recommendations"><h3>Actionable AI Recommendations</h3><ul><li><strong>Recommendation Name</strong>: Description</li></ul></section>
        
        Format the output using clean semantic HTML. Do not use Markdown format or wrap in ```html codeblocks. Return the raw HTML tags directly.
        """
        
        models_to_try = ["gpt-4o", "gpt-4o", "gpt-4o-mini"]
        last_exception = None
        
        for attempt, model_name in enumerate(models_to_try):
            try:
                print(f"INFO: Generating batch insights (Attempt {attempt+1}, model={model_name})...")
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=1500
                )
                
                insights_html = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
                if insights_html.startswith("```html"):
                    insights_html = insights_html[7:]
                if insights_html.endswith("```"):
                    insights_html = insights_html[:-3]
                insights_html = insights_html.strip()
                
                import re
                body_match = re.search(r"<body.*?>(.*?)</body>", insights_html, re.DOTALL | re.IGNORECASE)
                if body_match:
                    insights_html = body_match.group(1).strip()
                else:
                    insights_html = re.sub(r"<!DOCTYPE html.*?>", "", insights_html, flags=re.IGNORECASE)
                    insights_html = re.sub(r"<html.*?>", "", insights_html, flags=re.IGNORECASE)
                    insights_html = re.sub(r"</html>", "", insights_html, flags=re.IGNORECASE)
                    insights_html = re.sub(r"<head.*?>.*?</head>", "", insights_html, flags=re.DOTALL | re.IGNORECASE)
                    insights_html = re.sub(r"<body.*?>", "", insights_html, flags=re.IGNORECASE)
                    insights_html = re.sub(r"</body>", "", insights_html, flags=re.IGNORECASE)
                    
                return insights_html.strip()
            except Exception as err:
                last_exception = err
                print(f"WARNING: Batch insights attempt {attempt+1} failed with model {model_name}: {err}")
                if attempt < len(models_to_try) - 1:
                    import asyncio
                    await asyncio.sleep(1.5 * (attempt + 1))
                    
        return f"<p class='text-xs text-red-500 italic'>Failed to generate batch insights: {str(last_exception)}</p>"
    except Exception as e:
        print(f"Error generating batch insights: {e}")
        return f"<p class='text-xs text-red-500 italic'>Failed to generate batch insights: {str(e)}</p>"


@app.get("/api/v1/analytics/batch-insights/{batch_id}")
async def get_batch_insights(batch_id: str, force_regenerate: bool = False):
    """
    Returns general AI recommendations and insights for a completed batch.
    Computes on-the-fly if missing, forced, or previously failed.
    """
    async with async_session_maker() as session:
        batch_uuid = uuid.UUID(batch_id)
        batch = await session.get(AssessmentBatch, batch_uuid)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        if batch.status != "Completed":
            return {"insights": "<p class='text-xs text-foreground/50 italic animate-pulse'>Insights will be available once grading is complete.</p>"}
            
        is_error = batch.batch_insights and batch.batch_insights.startswith("<p class='text-xs text-red-500")
        if batch.batch_insights and not force_regenerate and not is_error:
            return {"insights": batch.batch_insights}
            
        # Generate and cache if missing, forced, or previously failed
        insights = await generate_batch_insights(batch_uuid, session)
        if not insights.startswith("<p class='text-xs text-red-500"):
            batch.batch_insights = insights
            await session.commit()
        return {"insights": insights}


@app.get("/api/v1/analytics/subject-performance/{tenant_id}")
async def subject_performance(tenant_id: str):
    """Returns average score per subject for a school."""
    async with async_session_maker() as session:
        query = select(AssessmentBatch, StudentResult).join(
            AcademicGroup, AssessmentBatch.academic_group_id == AcademicGroup.id
        ).outerjoin(
            StudentResult, StudentResult.batch_id == AssessmentBatch.id
        ).where(
            AcademicGroup.tenant_id == uuid.UUID(tenant_id),
            StudentResult.total_score != None
        )
        res = await session.execute(query)
        rows = res.all()

        subject_scores: dict = {}
        for batch, result in rows:
            subj = batch.subject
            if subj not in subject_scores:
                subject_scores[subj] = []
            subject_scores[subj].append(result.total_score)

        return {
            subj: {
                "average": round(sum(scores) / len(scores), 1),
                "count": len(scores)
            }
            for subj, scores in subject_scores.items()
        }

@app.get("/api/v1/analytics/school-leaderboard")
async def get_school_leaderboard():
    """
    Returns platform-wide School Leaderboard ranking schools by average score,
    pass rate, and total exams evaluated.
    """
    async with async_session_maker() as session:
        tenants_res = await session.execute(select(Tenant))
        tenants = tenants_res.scalars().all()
        
        leaderboard = []
        for t in tenants:
            query = select(StudentResult).join(
                AssessmentBatch, StudentResult.batch_id == AssessmentBatch.id
            ).join(
                AcademicGroup, AssessmentBatch.academic_group_id == AcademicGroup.id
            ).where(
                AcademicGroup.tenant_id == t.id,
                StudentResult.total_score != None
            )
            res = await session.execute(query)
            results = res.scalars().all()
            
            if results:
                scores = [r.total_score for r in results]
                avg = round(sum(scores) / len(scores), 1)
                highest = max(scores)
                pass_count = sum(1 for s in scores if s >= 50)
                pass_rate = round((pass_count / len(scores)) * 100, 1)
            else:
                avg = 0.0
                highest = 0
                pass_rate = 0.0
                
            leaderboard.append({
                "tenant_id": str(t.id),
                "school_name": t.name,
                "school_code": f"SCH-{str(t.id)[:6].upper()}",
                "average_score": avg,
                "total_graded": len(results),
                "pass_rate": pass_rate,
                "highest_score": highest
            })
            
        leaderboard.sort(key=lambda x: (x["average_score"], x["total_graded"]), reverse=True)
        for rank_idx, item in enumerate(leaderboard, 1):
            item["rank"] = rank_idx
            
        return leaderboard

# ── Delete Endpoints ──

@app.delete("/api/v1/students/{student_id}")
async def delete_student(student_id: str):
    async with async_session_maker() as session:
        student = await session.get(Student, uuid.UUID(student_id))
        if not student:
            raise HTTPException(404, "Student not found")
        await session.delete(student)
        await session.commit()
        return {"status": "deleted"}

@app.delete("/api/v1/assessment/batch/{batch_id}")
async def delete_batch(batch_id: str):
    async with async_session_maker() as session:
        batch = await session.get(AssessmentBatch, uuid.UUID(batch_id))
        if not batch:
            raise HTTPException(404, "Batch not found")
        await session.delete(batch)
        await session.commit()
        return {"status": "deleted"}

# ── CSV Export Endpoint ──

from fastapi.responses import StreamingResponse
import csv
import io as _io

@app.get("/api/v1/assessment/batch/{batch_id}/export-csv")
async def export_batch_csv(batch_id: str):
    """Exports all student results for a batch as a downloadable CSV file."""
    async with async_session_maker() as session:
        batch = await session.get(AssessmentBatch, uuid.UUID(batch_id))
        if not batch:
            raise HTTPException(404, "Batch not found")

        query = select(StudentResult, Student).outerjoin(
            Student, StudentResult.student_id == Student.id
        ).where(StudentResult.batch_id == uuid.UUID(batch_id))
        res = await session.execute(query)
        rows = res.all()

        output = _io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student Name", "Index Number", "Score (%)", "Needs Review", "AI Remarks"])
        for result, student in rows:
            writer.writerow([
                student.full_name if student else "Unmatched",
                student.index_number if student else "",
                result.total_score if result.total_score is not None else "",
                "Yes" if result.needs_manual_review else "No",
                result.ai_remarks or ""
            ])

        output.seek(0)
        filename = f"edulytics_{batch.subject}_{batch_id[:8]}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

# ── Fast Single-Paper Regrade Endpoint ──

@app.post("/api/v1/assessment/result/{result_id}/regrade")
async def regrade_single_result(result_id: str):
    """
    Fast single-paper regrade endpoint.
    Regrades ONLY the target student paper in 2-3 seconds using parallel mini vision & chunk grading.
    """
    from core.ai_engine import get_async_openai_client
    import base64
    import json
    import asyncio
    
    client = get_async_openai_client()
    r_uuid = uuid.UUID(result_id)
    
    async with async_session_maker() as session:
        result_obj = await session.get(StudentResult, r_uuid)
        if not result_obj:
            raise HTTPException(404, "Student result not found")
        batch_obj = await session.get(AssessmentBatch, result_obj.batch_id)
        if not batch_obj:
            raise HTTPException(404, "Batch not found")
            
        subject = batch_obj.subject
        group_id = batch_obj.academic_group_id
        batch_id_str = str(batch_obj.id)
        paper_images_urls = dict(result_obj.paper_images_urls or {})
        
        # Get students for fuzzy matching
        st_query = select(Student).where(Student.academic_group_id == group_id)
        st_res = await session.execute(st_query)
        students = [{"id": s.id, "full_name": s.full_name} for s in st_res.scalars().all()]
        
    if not paper_images_urls:
        raise HTTPException(400, "No paper images found for this result")
        
    b64s = []
    sorted_keys = sorted(
        paper_images_urls.keys(),
        key=natural_sort_page_key
    )
    for key in sorted_keys:
        url = paper_images_urls[key]
        filename = url.split("/")[-1]
        file_path = Path(BASE_DIR) / "static" / "uploads" / batch_id_str / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                b64s.append(base64.b64encode(f.read()).decode('utf-8'))
                
    if not b64s:
        raise HTTPException(400, "Image files missing on disk")
        
    master_b64s = []
    master_struct_str = ""
    master_rubric_block = ""
    if batch_obj and (batch_obj.mode == "answer_sheet" or batch_obj.master_question_urls or batch_obj.master_exam_structure):
        if batch_obj.master_question_urls:
            for m_key in sorted(dict(batch_obj.master_question_urls).keys(), key=natural_sort_page_key):
                m_url = batch_obj.master_question_urls[m_key]
                m_filename = m_url.split("/")[-1]
                m_path = Path(BASE_DIR) / "static" / "uploads" / batch_id_str / "master" / m_filename
                if m_path.exists():
                    with open(m_path, "rb") as mf:
                        master_b64s.append(base64.b64encode(mf.read()).decode('utf-8'))
        if batch_obj.master_exam_structure:
            master_struct_str = json.dumps(batch_obj.master_exam_structure, indent=2)
            master_rubric_block = f"INDEXED MASTER EXAM RUBRIC:\n{master_struct_str}\n"

    # Phase 1: Multi-Page Unified Vision Document OCR & Context Preservation
    system_prompt = f"""
    You are a master academic OCR and exam vision engine.
    You are evaluating a {subject} student exam paper consisting of {len(b64s)} pages in exact chronological order (Page 1 of {len(b64s)}, Page 2 of {len(b64s)}, etc.).

    CRITICAL SECONDARY MARKING RULES:
    1. REFER TO MASTER QUESTION PAPER: You MUST evaluate the student's handwritten answers by referring directly to the Master Question Paper images and Indexed Exam Rubric provided.
    2. QUESTION ALIGNMENT: Match each handwritten answer on the student's answer sheet (e.g. "1(a)", "No 2", "Qn 3b") to the corresponding Master Question statement, diagrams, passages, and max mark allocations.
    3. MULTI-PAGE CONTINUITY: Read all pages together as one continuous answer booklet!
    4. STUDENT NAME: Extract the student's full name from the cover or page header.

    {master_rubric_block}

    Return JSON format:
    {{
      "student_name": "Extracted Student Name or empty string",
      "questions": [
        {{
          "q_number": "1(a)",
          "question_text": "Full question statement from Master Question Paper",
          "student_answer": "Student written answer..."
        }}
      ]
    }}
    """

    content_payload = []
    if master_b64s:
        content_payload.append({
            "type": "text",
            "text": f"=== UNIVERSAL MASTER QUESTION PAPER ({len(master_b64s)} PAGES) ===\nRefer directly to these Master Question Paper images to verify questions, passages, diagrams, tables, and max marks:"
        })
        for m_i, m_b64 in enumerate(master_b64s):
            content_payload.append({"type": "text", "text": f"\n--- MASTER QUESTION PAPER PAGE {m_i + 1} OF {len(master_b64s)} ---"})
            content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m_b64}"}})

    content_payload.append({"type": "text", "text": f"\n=== STUDENT ANSWER SCRIPT ({len(b64s)} PAGES) ===\n{system_prompt}"})
    for p_i, b64_img in enumerate(b64s):
        content_payload.append({"type": "text", "text": f"\n--- STUDENT SCRIPT PAGE {p_i + 1} OF {len(b64s)} ---"})
        content_payload.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})

    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": content_payload}],
            max_tokens=4096
        )
        doc_data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"GPT-4o multi-page extraction failed in regrade, trying fallback: {e}")
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": content_payload}],
                max_tokens=4096
            )
            doc_data = json.loads(resp.choices[0].message.content)
        except Exception as e2:
            print(f"Fallback extraction error: {e2}")
            doc_data = {"student_name": "", "questions": []}

    extracted_name = doc_data.get("student_name", "")
    all_extracted_questions = doc_data.get("questions", [])
        
    try:
        all_extracted_questions = sorted(
            all_extracted_questions,
            key=lambda x: int(re.search(r'\d+', str(x.get("q_number", 0))).group() if re.search(r'\d+', str(x.get("q_number", 0))) else 0)
        )
    except Exception:
        pass
        
    if not all_extracted_questions:
        all_extracted_questions = [{"q_number": 1, "question_text": "Full Exam Assessment", "student_answer": "Complete"}]

    # Phase 2: Parallel Micro-Batch Grading (gpt-4o-mini text chunks of 15)
    chunk_size = 15
    question_chunks = [
        all_extracted_questions[i:i + chunk_size]
        for i in range(0, len(all_extracted_questions), chunk_size)
    ]

    async def grade_chunk(c_idx: int, q_chunk: list):
        chunk_prompt = f"""
        Grade chunk {c_idx + 1} of {subject} exam:
        {json.dumps(q_chunk)}
        Return JSON: {{"graded_questions": [{{"q_number": 1, "question_text": "", "student_answer": "", "status": "CORRECT", "score_awarded": 5, "max_score": 5, "explanation": "", "alternative_answers": [], "remarks": ""}}]}}
        """
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": chunk_prompt}],
                max_tokens=4096
            )
            chunk_res = json.loads(resp.choices[0].message.content)
            return chunk_res.get("graded_questions", q_chunk)
        except Exception:
            return q_chunk

    chunk_results = await asyncio.gather(*[grade_chunk(i, chunk) for i, chunk in enumerate(question_chunks)])
    graded_all_questions = []
    for c_res in chunk_results:
        graded_all_questions.extend(c_res)

    # Phase 3: Assembly & DB save
    total_score = sum(int(q.get("score_awarded", 0)) for q in graded_all_questions)
    max_possible = sum(int(q.get("max_score", 5)) for q in graded_all_questions) or 100

    ai_data = {
        "student_name": extracted_name or "Student Paper",
        "score": total_score,
        "max_possible_score": max_possible,
        "questions": graded_all_questions,
        "qualitative_feedback": f"Regraded paper across {len(graded_all_questions)} evaluated questions."
    }
    
    html = generate_html_report_from_json(ai_data, subject)
    matched_student, _ = find_closest_student_match(extracted_name, students, threshold=0.50)

    score_pct = min(100, max(0, round((total_score / max_possible) * 100))) if max_possible > 0 else 0

    async with async_session_maker() as session:
        res_obj = await session.get(StudentResult, r_uuid)
        if res_obj:
            res_obj.total_score = score_pct
            res_obj.raw_extracted_html = html
            if matched_student:
                res_obj.student_id = matched_student["id"]
                res_obj.needs_manual_review = False
            else:
                res_obj.needs_manual_review = True
                res_obj.ai_remarks = f"Could not match OCR name: '{extracted_name}' to class roster."
            await session.commit()
            
    return {
        "status": "success",
        "result_id": result_id,
        "score": score_pct,
        "max_possible_score": max_possible,
        "questions_count": len(graded_all_questions),
        "raw_extracted_html": html
    }


class ReorderPagesRequest(BaseModel):
    page_urls: List[str]

@app.post("/api/v1/assessment/paper/{result_id}/reorder-pages")
async def reorder_paper_pages(result_id: str, req: ReorderPagesRequest):
    """
    Updates the sequential page order of a scanned student paper.
    """
    async with async_session_maker() as session:
        r_uuid = uuid.UUID(result_id)
        res_obj = await session.get(StudentResult, r_uuid)
        if not res_obj:
            raise HTTPException(404, "Student result record not found")

        new_dict = {}
        for idx, url in enumerate(req.page_urls):
            new_dict[f"page_{idx + 1}"] = url

        res_obj.paper_images_urls = new_dict
        await session.commit()
        return {"status": "success", "message": "Page sequence updated successfully", "paper_images_urls": new_dict}


# ── Score Override Endpoint ──

class ScoreOverrideRequest(BaseModel):
    score: int

@app.patch("/api/v1/assessment/result/{result_id}/override-score")
async def override_score(result_id: str, req: ScoreOverrideRequest):
    async with async_session_maker() as session:
        res_obj = await session.get(StudentResult, uuid.UUID(result_id))
        if not res_obj:
            raise HTTPException(404, "Result not found")
        res_obj.total_score = req.score
        res_obj.needs_manual_review = False
        res_obj.ai_remarks = f"Score manually overridden to {req.score}%."
        await session.commit()
        return {"status": "success", "score": req.score}


# ── Scanner Integration Endpoints ──

@app.get("/api/v1/scanner/devices")
async def list_scanner_devices(refresh: bool = False):
    """
    Detect connected flatbed scanners via SANE.
    Returns a list of devices and whether SANE is installed.
    """
    sane_ok = is_sane_installed()
    devices = detect_scanners_cached(force_refresh=refresh) if sane_ok else []

    # Determine platform for frontend messaging
    if _sys.platform == "darwin":
        platform = "macos"
        install_msg = "SANE scanner drivers are required. Install with: brew install sane-backends"
    elif _sys.platform == "win32":
        platform = "windows"
        install_msg = "Scanner support requires pywin32. Install with: pip install pywin32"
    else:
        platform = "linux"
        install_msg = "SANE scanner drivers are required. Install with: sudo apt-get install sane-utils"

    return {
        "sane_installed": sane_ok,
        "platform": platform,
        "devices": [
            {
                "device_id": d.device_id,
                "vendor": d.vendor,
                "model": d.model,
                "device_type": d.device_type,
                "display_name": d.display_name,
            }
            for d in devices
        ],
        "message": (
            None if sane_ok
            else install_msg
        ),
    }


class ScanRequest(BaseModel):
    device_id: str
    dpi: int = 150
    mode: str = "Color"

@app.post("/api/v1/scanner/scan")
def trigger_scan(req: ScanRequest):
    """
    Trigger a flatbed scan on the specified device.
    Returns the scanned image as base64-encoded PNG.
    """
    result = scan_page(
        device_id=req.device_id,
        dpi=req.dpi,
        mode=req.mode,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@app.post("/api/v1/scanner/ocr-name")
async def ocr_student_name(file: UploadFile = File(...)):
    """
    Use Gemini-3.5-Flash or GPT-4o-mini to extract the student's name from a scanned exam page.
    """
    img_bytes = await file.read()
    
    # 1. Try Gemini if GOOGLE_API_KEY is available
    google_key = os.environ.get("GOOGLE_API_KEY")
    if google_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=google_key)
            part = types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            prompt = (
                "Analyze this scanned exam page and extract the name of the student who took the exam. "
                "Look for standard fields like 'Name:', 'Student Name:', 'Candidate Name:', or handwritten names "
                "typically written at the top of the exam paper. "
                "Return ONLY the extracted name (e.g., 'Bruce Wayne'). Do not include labels, punctuation, "
                "or extra words. If you cannot find any student name, return 'Unknown'."
            )
            response = await client.aio.models.generate_content(
                model='gemini-3.5-flash',
                contents=[part, prompt]
            )
            name = response.text.strip() if response.text else "Unknown"
            name = name.replace('"', '').replace("'", "").strip()
            if name.endswith('.'):
                name = name[:-1].strip()
            if name.lower() != "unknown" and len(name) <= 50:
                return {"name": name}
        except Exception as e:
            print(f"Gemini OCR name extraction failed: {e}")

    # 2. Fallback to OpenAI Vision (gpt-4o-mini) using OPENAI_API_KEY
    try:
        from core.ai_engine import get_async_openai_client
        client = get_async_openai_client()
        b64_img = base64.b64encode(img_bytes).decode("ascii")
        prompt = (
            "Analyze this scanned exam page image and extract the name of the student who took the exam. "
            "Look for fields like 'Name:', 'Student Name:', 'Candidate Name:', or handwritten names at the top of the paper. "
            "Return ONLY the extracted name (e.g., 'Bruce Wayne'). Do not include labels, punctuation, "
            "or extra words. If you cannot find any student name, return 'Unknown'."
        )
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                        }
                    ]
                }
            ],
            max_tokens=50
        )
        name = response.choices[0].message.content.strip()
        name = name.replace('"', '').replace("'", "").strip()
        if name.endswith('.'):
            name = name[:-1].strip()
        if name.lower() == "unknown" or len(name) > 50:
            name = "Unknown"
        return {"name": name}
    except Exception as e:
        print(f"OpenAI Vision OCR name extraction error: {e}")
        return {"name": "Unknown", "error": str(e)}


@app.post("/api/v1/scanner/compile-pdf")
def compile_pdf(files: List[UploadFile] = File(...)):
    """
    Compile multiple uploaded images into a single PDF and return it.
    """
    from PIL import Image
    import io
    from fastapi.responses import StreamingResponse

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Sort files by their filename to ensure pages are in order (e.g. page1, page2)
    sorted_files = sorted(files, key=lambda f: f.filename)

    images = []
    for file in sorted_files:
        try:
            img_bytes = file.file.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            images.append(img)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file {file.filename}: {str(e)}")

    if not images:
        raise HTTPException(status_code=400, detail="No valid images to compile")

    pdf_buffer = io.BytesIO()
    images[0].save(pdf_buffer, format="PDF", save_all=True, append_images=images[1:])
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=compiled_exam.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

