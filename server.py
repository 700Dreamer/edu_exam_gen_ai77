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

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(title="Edulytics AI Engine - Cloud", version="1.0.0", lifespan=lifespan)

# ── CORS — allow Next.js dev server ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
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

class AssignStudentRequest(BaseModel):
    student_id: str

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
                student = Student(
                    academic_group_id=group.id,
                    full_name=stu_req.full_name,
                    index_number=stu_req.index_number
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

@app.get("/api/v1/tenant/{tenant_id}/groups")
async def list_academic_groups(tenant_id: str):
    async with async_session_maker() as session:
        query = select(AcademicGroup).where(AcademicGroup.tenant_id == uuid.UUID(tenant_id))
        res = await session.execute(query)
        groups = res.scalars().all()
        return [{"id": str(g.id), "level": g.level, "stream": g.stream} for g in groups]

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
        student = Student(
            academic_group_id=uuid.UUID(group_id),
            full_name=req.full_name,
            index_number=req.index_number
        )
        session.add(student)
        await session.commit()
        await session.refresh(student)
        return {"id": str(student.id), "full_name": student.full_name, "index_number": student.index_number}

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
    async with async_session_maker() as session:
        query = select(StudentResult, Student).outerjoin(
            Student, StudentResult.student_id == Student.id
        ).where(StudentResult.batch_id == uuid.UUID(batch_id))
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

# ── Assessment Grading Endpoints ──
@app.post("/api/v1/assessment/batch/create")
async def create_batch(req: BatchCreateRequest):
    async with async_session_maker() as session:
        batch = AssessmentBatch(
            academic_group_id=uuid.UUID(req.academic_group_id),
            subject=req.subject,
            exam_type=req.exam_type,
            status="Initiated"
        )
        session.add(batch)
        await session.commit()
        await session.refresh(batch)
        return {"batch_id": str(batch.id)}

import re

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
    
    # Sort files by original filename to ensure alphabetical order (which matches page order)
    sorted_files = sorted(files, key=lambda f: f.filename or "")
    
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
            
        url = f"http://localhost:8000/static/uploads/{batch_id}/{unique_name}"
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
            # Sort ZIP names alphabetically to preserve page ordering
            sorted_names = sorted(z.namelist())
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
                
                url = f"http://localhost:8000/static/uploads/{batch_id}/{safe_filename}"
                
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
        
        # Get all student profiles for fuzzy matching
        st_query = select(Student).where(Student.academic_group_id == group_id)
        st_res = await session.execute(st_query)
        students = [
            {"id": s.id, "full_name": s.full_name} 
            for s in st_res.scalars().all()
        ]
        
    # 2. Process each result decoupled from long database transactions
    for r_id in result_ids:
        # Step A: Load image URLs in a quick session
        async with async_session_maker() as session:
            result = await session.get(StudentResult, r_id)
            if not result or not result.paper_images_urls:
                continue
            paper_images_urls = dict(result.paper_images_urls)
            
        try:
            # Step B: Base64 encode pages in correct numerical order
            b64s = []
            sorted_keys = sorted(
                paper_images_urls.keys(),
                key=lambda k: int(re.search(r'\d+', k).group() if re.search(r'\d+', k) else 0)
            )
            for key in sorted_keys:
                url = paper_images_urls[key]
                filename = url.split("/")[-1]
                file_path = Path(BASE_DIR) / "static" / "uploads" / batch_id / filename
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                b64 = base64.b64encode(file_bytes).decode('utf-8')
                b64s.append(b64)
            
            if not b64s:
                continue
            
            # Step C: Call OpenAI API (takes several seconds)
            prompt = f"""
            You are grading a {subject} exam. Note that this exam has {len(b64s)} pages, which are attached in order.
            1. Extract the student's full name from the top of the first page.
            2. Grade the entire exam (across all pages). You MUST list and grade EVERY single question present on the exam paper. Do not skip, omit, or summarize any questions. Every question must have its own row in the table. The table MUST contain a row for every question from first to last (e.g. Questions 1 to 15, or whatever range is on the paper).
            3. Provide a highly detailed, clean HTML report. The HTML MUST look professional, clean, and follow standard educational feedback formats.
               The report MUST contain:
               - An executive summary showing Student Name, Subject, and Total Score.
               - A structured question-by-question grading table containing a row for every single question on the paper with these columns:
                 * Question Number/ID
                 * Question Description/Topic
                 * Student's Response (the actual answer written or ticked by the student)
                 * Status (Correct, Incorrect, or Partially Correct - styled with color-coded text or background: green (#16a34a) for Correct, red (#dc2626) for Incorrect, and orange/yellow (#d97706) for Partially Correct)
                 * Score Awarded (e.g., "5/5" or "0/3")
                 * Detailed Explanation & Alternative Answers (Explain why the correct answer is correct. Underneath, explicitly list all acceptable alternative correct answers, synonyms, calculations, or variations in a bulleted list, using green color-coded styling for these alternative choices to make them visually distinct for teachers).
                 * Teacher/AI Remarks (specific constructive feedback on their answer).
               - A final section with qualitative feedback and key recommendations for the student to improve.
            
            Return JSON format: {{"student_name": "Extracted Name", "score": 85, "html": "<div class='space-y-6'>...</div>"}}
            """
            
            content_blocks = [{"type": "text", "text": prompt}]
            for b64 in b64s:
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }],
                max_tokens=4096
            )
            
            ai_data = json.loads(response.choices[0].message.content)
            extracted_name = ai_data.get("student_name", "")
            score = ai_data.get("score")
            html = ai_data.get("html")
            
            # Fuzzy match student name
            matched_student_id = None
            matched = False
            for st in students:
                st_name_lower = st["full_name"].lower()
                ext_name_lower = extracted_name.lower()
                if extracted_name and (st_name_lower in ext_name_lower or ext_name_lower in st_name_lower):
                    matched_student_id = st["id"]
                    matched = True
                    break
            
            # Step D: Save result in a quick transaction
            async with async_session_maker() as session:
                result_obj = await session.get(StudentResult, r_id)
                if result_obj:
                    result_obj.total_score = score
                    result_obj.raw_extracted_html = html
                    if matched:
                        result_obj.student_id = matched_student_id
                        result_obj.needs_manual_review = False
                    else:
                        result_obj.needs_manual_review = True
                        result_obj.ai_remarks = f"Could not precisely match OCR name: '{extracted_name}'."
                    await session.commit()
                    
        except Exception as e:
            # Save error state in a quick transaction
            async with async_session_maker() as session:
                result_obj = await session.get(StudentResult, r_id)
                if result_obj:
                    result_obj.needs_manual_review = True
                    result_obj.ai_remarks = f"Error processing: {str(e)}"
                    await session.commit()
                    
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

@app.post("/api/v1/assessment/batch/{batch_id}/process")
async def trigger_batch_process(batch_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_batch_background, batch_id)
    return {"status": "Processing initiated"}

@app.get("/api/v1/assessment/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, uuid.UUID(batch_id))
        if not batch_obj: raise HTTPException(404, "Batch not found")
        
        query = select(StudentResult).where(StudentResult.batch_id == uuid.UUID(batch_id))
        res = await session.execute(query)
        results = res.scalars().all()
        
        total = len(results)
        needs_review = sum(1 for r in results if r.needs_manual_review)
        processed = sum(1 for r in results if r.raw_extracted_html is not None or r.ai_remarks is not None)
        
        return {
            "status": batch_obj.status,
            "total": total,
            "processed": processed,
            "needs_review": needs_review
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
def get_config():
    from core.syllabus_master import MASTER_SYLLABUS
    return {
        "subjects": ALL_SUBJECTS,
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
    async with async_session_maker() as session:
        query = select(StudentResult).where(
            StudentResult.batch_id == uuid.UUID(batch_id),
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
    
    # 4. Call GPT-4o
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
        
        response = await client.chat.completions.create(
            model="gpt-4o",
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
    except Exception as e:
        print(f"Error generating batch insights: {e}")
        return f"<p class='text-xs text-red-500 italic'>Failed to generate batch insights: {str(e)}</p>"


@app.get("/api/v1/analytics/batch-insights/{batch_id}")
async def get_batch_insights(batch_id: str):
    """
    Returns general AI recommendations and insights for a completed batch.
    Computes on-the-fly if not already generated.
    """
    async with async_session_maker() as session:
        batch_uuid = uuid.UUID(batch_id)
        batch = await session.get(AssessmentBatch, batch_uuid)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        if batch.status != "Completed":
            return {"insights": "<p class='text-xs text-foreground/50 italic animate-pulse'>Insights will be available once grading is complete.</p>"}
            
        if batch.batch_insights:
            return {"insights": batch.batch_insights}
            
        # Generate and cache if missing
        insights = await generate_batch_insights(batch_uuid, session)
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

