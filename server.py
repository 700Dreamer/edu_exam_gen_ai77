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

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from core.ai_engine import generate_ai_content, analyze_pedagogy, generate_flow_step, chat_response, get_openai_client, generate_scenario_content
from core.db_engine import save_project, load_projects, init_db
from ui.document_builder import build_full_html
from core.syllabus_master import ALL_SUBJECTS, ALL_LEVELS, get_master_topics
from core.ingestion_db import get_ingest_stats
from core.export_engine import generate_docx_stream
from core.marking_engine import mark_student_work

app = FastAPI(title="EduQuest AI Engine", version="3.1.0")

# ── CORS — allow Next.js dev server ──
_EXTRA_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        # Docker Compose service-name (server-side rendering calls)
        "http://frontend:3000",
        # Production — set CORS_ORIGINS env var for custom domains
        *_EXTRA_ORIGINS,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

class GenerateRequest(BaseModel):
    mode: str
    level: str
    subject: str
    term: str
    question_count: int
    topic: Optional[str] = ""
    brand_name: Optional[str] = "EduQuest"
    ai_model: Optional[str] = "gpt-4o"
    content_override: Optional[str] = None
    pedagogy_hint: Optional[dict] = None

class ScenarioRequest(BaseModel):
    subject: str
    level: str
    term: str
    theme: str
    topic: Optional[str] = ""
    difficulty: Optional[str] = "Standard"
    brand_name: Optional[str] = "EduQuest"
    ai_model: Optional[str] = "gpt-4o"

@app.post("/api/scenario")
async def scenario_endpoint(req: ScenarioRequest):
    try:
        raw_data, raw_str, title = generate_scenario_content(
            req.theme, req.level, req.subject, req.term, req.topic, req.difficulty, req.ai_model
        )
        
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
async def generate_endpoint(req: GenerateRequest):
    try:
        if req.content_override:
            raw = json.loads(req.content_override)
            raw_str = req.content_override
            title = f"{req.subject} {req.level} - Refined"
        else:
            raw, raw_str, title = await generate_ai_content(
                req.mode, req.level, req.subject, req.term, 
                req.question_count, "Balanced", req.ai_model, "Internal", 
                req.topic, req.pedagogy_hint
            )
        
        # Render the actual HTML for the frontend
        html = build_full_html(
            mode=req.mode,
            exam_type="Internal",
            level=req.level,
            subject=req.subject,
            term_roman=req.term,
            exam_year="2026",
            duration="2 HR 30 MIN",
            school_name="EduQuest Central",
            brand_name=req.brand_name,
            question_count=req.question_count,
            content_raw=raw_str,
            topic=req.topic
        )
        
        # Auto-save history
        save_project(req.subject, req.level, req.term, raw_str, html, title)
        
        return {"raw": raw, "html": html, "title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# ── INSIGHTS: Quick-Index — AI synthesises content for a missing topic ──
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

@app.post("/api/flow/stream")
async def stream_flow(data: dict):
    nodes = data.get("nodes", [])
    
    async def generator():
        source = next((n for n in nodes if n['type'] == 'source'), {'data': {}})
        topics_node = next((n for n in nodes if n['type'] == 'topic'), {'data': {}})
        logic = next((n for n in nodes if n['type'] == 'logic'), {'data': {}})
        
        subject = source['data'].get('subject', 'General')
        level = source['data'].get('level', 'Standard')
        topic_list = topics_node['data'].get('topics', ['General Concept'])
        bloom = logic['data'].get('bloom', 'Analysis')
        
        for t in topic_list:
            q = await generate_flow_step(t, subject, level, bloom)
            yield f"data: {json.dumps(q)}\n\n"
            
    return StreamingResponse(generator(), media_type="text/event-stream")

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
        config = {
            "brand_name": req.brand_name,
            "subject": req.subject,
            "level": req.level,
            "term": req.term,
            "term_roman": term_roman,
            "exam_type": "Internal", # Fallback
            "exam_year": "2026",
            "duration": "2 HR 30 MIN",
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

@app.get("/api/health/resources")
def health_resources():
    import os
    try:
        cpu = round(os.getloadavg()[0] / os.cpu_count() * 100, 1)
        mem = 0
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            avail = next((int(l.split()[1]) for l in lines if l.startswith("MemAvailable:")), 0)
            total = next((int(l.split()[1]) for l in lines if l.startswith("MemTotal:")), 0)
            if total > 0 and avail > 0:
                mem = round((total - avail) / 1024)
        return {"memory_mb": mem, "cpu_percent": cpu}
    except Exception:
        return {"memory_mb": 0, "cpu_percent": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
