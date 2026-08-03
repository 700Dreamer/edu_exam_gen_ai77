from __future__ import annotations
import asyncio
import base64
import difflib
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from sqlalchemy import select, func
from core.models import async_session_maker, AssessmentBatch, StudentResult, Student, BatchTask
from core.ai_engine import get_async_openai_client

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Redis Connection & PubSub Management ──
redis_client: Optional[Any] = None

async def get_redis_client() -> Optional[Any]:
    global redis_client
    redis_url = os.getenv("REDIS_URL")
    if not redis_url or aioredis is None:
        return None
    if redis_client is None:
        try:
            client = aioredis.from_url(redis_url, decode_responses=True)
            await client.ping()
            redis_client = client
            print(f"Connected to Redis task broker at {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
        except Exception as e:
            print(f"Warning: Redis connection error ({e}). Falling back to DB task queue.")
            redis_client = None
    return redis_client

async def close_redis_client():
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.close()
        except Exception:
            pass
        redis_client = None

# ── In-Memory Event Streaming Subscriptions (Fallback) ──
batch_subscribers: Dict[str, List[asyncio.Queue]] = {}

async def broadcast_event(batch_id: str, event_type: str, data: dict):
    """
    Pushes real-time SSE events to all connected clients listening to batch_id stream.
    Publishes to Redis PubSub channel when active, plus local in-memory subscribers.
    """
    payload_dict = {"type": event_type, "timestamp": data.get("timestamp", datetime.utcnow().isoformat()), **data}
    payload = json.dumps(payload_dict)
    
    r = await get_redis_client()
    if r:
        try:
            await r.publish(f"edulytics:sse:{batch_id}", payload)
        except Exception as e:
            print(f"Redis PubSub publish error: {e}")

    if batch_id in batch_subscribers:
        for q in list(batch_subscribers[batch_id]):
            try:
                await q.put(payload)
            except Exception:
                pass

async def subscribe_batch_events(batch_id: str):
    """
    Async generator yielding real-time SSE payload strings for batch_id.
    Listens to Redis PubSub channel if Redis is active, or local asyncio Queue.
    """
    r = await get_redis_client()
    if r:
        pubsub = r.pubsub()
        channel_name = f"edulytics:sse:{batch_id}"
        await pubsub.subscribe(channel_name)
        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    yield message["data"]
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
            except Exception:
                pass
    else:
        q = asyncio.Queue()
        if batch_id not in batch_subscribers:
            batch_subscribers[batch_id] = []
        batch_subscribers[batch_id].append(q)
        try:
            while True:
                payload = await q.get()
                yield payload
        finally:
            if batch_id in batch_subscribers and q in batch_subscribers[batch_id]:
                batch_subscribers[batch_id].remove(q)
                if not batch_subscribers[batch_id]:
                    del batch_subscribers[batch_id]



def natural_sort_page_key(key: str) -> int:
    """Extracts numeric page suffix (e.g. page_1 -> 1, p2 -> 2) or last integer for strict natural sorting."""
    m = re.search(r'(?:page[_\-]?|p[_\-]?|slide[_\-]?)(\d+)', str(key), re.IGNORECASE)
    if m:
        return int(m.group(1))
    nums = re.findall(r'\d+', str(key))
    return int(nums[-1]) if nums else 0


def normalize_q_key(q_num: Any) -> str:
    """
    Standardizes question keys into a clean canonical format.
    Examples:
      "Q1(a)" -> "1a"
      "Question 1 (b)" -> "1b"
      "1. a" -> "1a"
      "2" -> "2"
    """
    if not q_num:
        return "0"
    s = str(q_num).lower().strip()
    s = re.sub(r'^(?:question|qn|q)[\.\s\-_]*', '', s)
    s = re.sub(r'[\(\)\[\]\.\s\-_]+', '', s)
    return s if s else "0"


def question_sort_tuple(q_obj: dict) -> tuple:
    """
    Deterministically sorts questions by major numeric index and minor subpart letter.
    e.g. 1a -> (1, 'a'), 1b -> (1, 'b'), 2 -> (2, '')
    """
    raw_q = q_obj.get("q_number", "0") if isinstance(q_obj, dict) else str(q_obj)
    q_key = normalize_q_key(raw_q)
    match = re.match(r'^(\d+)([a-z]*)$', q_key)
    if match:
        num = int(match.group(1))
        sub = match.group(2)
        return (num, sub)
    nums = re.findall(r'\d+', q_key)
    n = int(nums[0]) if nums else 0
    return (n, q_key)


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

        if clean_ocr == clean_db:
            return st, 1.0

        if ocr_tokens and db_tokens:
            token_intersection = ocr_tokens.intersection(db_tokens)
            token_score = len(token_intersection) / max(len(ocr_tokens), len(db_tokens))
        else:
            token_score = 0.0

        seq_score = difflib.SequenceMatcher(None, clean_ocr, clean_db).ratio()
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
    
    try:
        questions = sorted(questions, key=question_sort_tuple)
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


async def enqueue_batch_tasks(batch_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
    """
    Enqueues all student results of a batch into the persistent BatchTask database queue
    and pushes task IDs to Redis queue when active.
    """
    batch_uuid = uuid.UUID(str(batch_id)) if isinstance(batch_id, str) else batch_id
    
    task_ids_to_push = []
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if not batch_obj:
            raise ValueError(f"Batch {batch_id} not found.")
        
        batch_obj.status = "Queued"
        
        # Get all StudentResult records for this batch
        query = select(StudentResult.id).where(StudentResult.batch_id == batch_uuid)
        res = await session.execute(query)
        result_ids = res.scalars().all()
        
        enqueued_count = 0
        for r_id in result_ids:
            # Check if task already exists
            existing = await session.execute(
                select(BatchTask).where(
                    BatchTask.batch_id == batch_uuid,
                    BatchTask.student_result_id == r_id
                )
            )
            task_obj = existing.scalars().first()
            if not task_obj:
                task_obj = BatchTask(
                    batch_id=batch_uuid,
                    student_result_id=r_id,
                    task_type="grade_paper",
                    status="QUEUED"
                )
                session.add(task_obj)
                await session.flush()
            else:
                task_obj.status = "QUEUED"
                task_obj.attempts = 0
                task_obj.last_error = None
                task_obj.updated_at = datetime.utcnow()
                
            task_ids_to_push.append(str(task_obj.id))
            enqueued_count += 1
                
        await session.commit()

    # If Redis client is active, push task IDs to Redis queue list
    r = await get_redis_client()
    if r and task_ids_to_push:
        try:
            await r.rpush("edulytics:queue:batch_tasks", *task_ids_to_push)
        except Exception as e:
            print(f"Redis rpush task error: {e}")
        
    await broadcast_event(str(batch_id), "batch_queued", {
        "batch_id": str(batch_id),
        "total_enqueued": enqueued_count
    })
    
    return {
        "status": "queued",
        "batch_id": str(batch_id),
        "enqueued_tasks": enqueued_count
    }


async def fetch_and_lock_next_task() -> Optional[BatchTask]:
    """
    Atomically fetches and locks the next QUEUED or retriable FAILED task from Redis queue or database.
    """
    r = await get_redis_client()
    if r:
        try:
            task_id_str = await r.lpop("edulytics:queue:batch_tasks")
            if task_id_str:
                async with async_session_maker() as session:
                    task = await session.get(BatchTask, uuid.UUID(task_id_str))
                    if task and task.status in ["QUEUED", "FAILED"]:
                        task.status = "PROCESSING"
                        task.attempts += 1
                        task.updated_at = datetime.utcnow()
                        await session.commit()
                        await session.refresh(task)
                        return task
        except Exception as e:
            print(f"Redis queue pop error: {e}. Falling back to DB query.")

    # Fallback DB query if Redis is inactive or queue returned no task
    async with async_session_maker() as session:
        query = select(BatchTask).where(
            BatchTask.status == "QUEUED"
        ).order_by(BatchTask.created_at.asc()).limit(1)
        
        res = await session.execute(query)
        task = res.scalars().first()
        
        if not task:
            # Check for retriable failed tasks whose attempts < max_retries
            retry_query = select(BatchTask).where(
                BatchTask.status == "FAILED",
                BatchTask.attempts < BatchTask.max_retries
            ).order_by(BatchTask.updated_at.asc()).limit(1)
            res = await session.execute(retry_query)
            task = res.scalars().first()
            
        if task:
            task.status = "PROCESSING"
            task.attempts += 1
            task.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(task)
            return task
            
    return None


async def execute_task(task: BatchTask) -> bool:
    """
    Executes a single paper grading task with vision OCR and micro-chunk grading.
    """
    client = get_async_openai_client()
    b_id = str(task.batch_id)
    r_id = task.student_result_id
    
    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, task.batch_id)
        if not batch_obj:
            return False
            
        # Update batch status to Processing if queued
        if batch_obj.status == "Queued":
            batch_obj.status = "Processing"
            await session.commit()
            
        subject = batch_obj.subject
        group_id = batch_obj.academic_group_id
        
        st_query = select(Student).where(Student.academic_group_id == group_id)
        st_res = await session.execute(st_query)
        students = [{"id": s.id, "full_name": s.full_name} for s in st_res.scalars().all()]
        
        result = await session.get(StudentResult, r_id)
        if not result or not result.paper_images_urls:
            return False
        paper_images_urls = dict(result.paper_images_urls)

    try:
        await broadcast_event(b_id, "paper_start", {
            "paper_id": str(r_id),
            "paper_idx": str(r_id),
            "phase": "Phase 1: Page Extraction"
        })
        
        b64s = []
        sorted_keys = sorted(paper_images_urls.keys(), key=natural_sort_page_key)
        for key in sorted_keys:
            url = paper_images_urls[key]
            filename = url.split("/")[-1]
            file_path = Path(BASE_DIR) / "static" / "uploads" / b_id / filename
            if file_path.exists():
                with open(file_path, "rb") as f:
                    b64s.append(base64.b64encode(f.read()).decode('utf-8'))
                    
        if not b64s:
            raise ValueError(f"No local image files found for paper {r_id}")

        master_b64s = []
        master_struct_str = ""
        master_rubric_block = ""
        if batch_obj and (batch_obj.mode == "answer_sheet" or batch_obj.master_question_urls or batch_obj.master_exam_structure):
            if batch_obj.master_question_urls:
                for m_key in sorted(dict(batch_obj.master_question_urls).keys(), key=natural_sort_page_key):
                    m_url = batch_obj.master_question_urls[m_key]
                    m_filename = m_url.split("/")[-1]
                    m_path = Path(BASE_DIR) / "static" / "uploads" / b_id / "master" / m_filename
                    if m_path.exists():
                        with open(m_path, "rb") as mf:
                            master_b64s.append(base64.b64encode(mf.read()).decode('utf-8'))
            if batch_obj.master_exam_structure:
                master_struct_str = json.dumps(batch_obj.master_exam_structure, indent=2)
                master_rubric_block = f"INDEXED MASTER EXAM RUBRIC:\n{master_struct_str}\n"

        system_prompt = f"""
        You are a master academic OCR and exam vision engine.
        You are evaluating a {subject} student exam paper consisting of {len(b64s)} pages in exact chronological order (Page 1 of {len(b64s)}, Page 2 of {len(b64s)}, etc.).

        CRITICAL SECONDARY MARKING RULES:
        1. REFER TO MASTER QUESTION PAPER: You MUST evaluate the student's handwritten answers by referring directly to the Master Question Paper images and Indexed Exam Rubric provided.
        2. QUESTION ALIGNMENT: Match each handwritten answer on the student's answer sheet to the corresponding Master Question statement, diagrams, passages, and max mark allocations.
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
                "text": f"=== UNIVERSAL MASTER QUESTION PAPER ({len(master_b64s)} PAGES) ===\nRefer directly to these Master Question Paper images to verify questions and max marks:"
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
                    temperature=0.0,
                    seed=42,
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
                    resp = await client.chat.completions.create(
                        model="gpt-4o",
                        temperature=0.0,
                        seed=42,
                        response_format={"type": "json_object"},
                        messages=[{"role": "user", "content": content_payload}],
                        max_tokens=4096
                    )
                    doc_data = json.loads(resp.choices[0].message.content)

        extracted_name = doc_data.get("student_name", "")
        raw_questions = doc_data.get("questions", [])

        # Standardize question keys and sort deterministically
        all_extracted_questions = []
        for q in raw_questions:
            if isinstance(q, dict):
                q["q_number"] = normalize_q_key(q.get("q_number", "0"))
                all_extracted_questions.append(q)
                
        all_extracted_questions = sorted(all_extracted_questions, key=question_sort_tuple)

        if not all_extracted_questions:
            all_extracted_questions = [{"q_number": "1", "question_text": "Full Exam Assessment", "student_answer": "Complete"}]

        # ── PHASE 2: Parallel Micro-Batch Grading (Text Chunks of 12) ──
        chunk_size = 12
        question_chunks = [
            all_extracted_questions[i:i + chunk_size]
            for i in range(0, len(all_extracted_questions), chunk_size)
        ]

        async def grade_chunk(c_idx: int, q_chunk: list):
            rubric_ref = f"REFER TO MASTER QUESTION PAPER & MARKING RUBRIC:\n{master_struct_str}\n" if master_struct_str else ""
            chunk_prompt = f"""
            You are an authoritative national academic examiner grading chunk {c_idx + 1} of a {subject} examination.

            STRICT MARKING PROTOCOL:
            1. 100% DETERMINISTIC OBJECTIVITY: Grade strictly based on pedagogical facts and accuracy. Identical student responses MUST receive identical marks every single time.
            2. ACCURACY & EVIDENCE:
               - If the student's answer is factually correct or demonstrates full mastery, mark status as "CORRECT" with score_awarded = max_score.
               - If the student's answer is incomplete or partially correct, mark status as "PARTIAL" with partial score_awarded.
               - If the student's answer is wrong, nonsensical, or left blank, mark status as "INCORRECT" with score_awarded = 0.
            3. SYNONYMS & METHOD MARKS: Accept valid educational synonyms, equivalent numerical forms, and working steps. Do NOT accept incorrect facts.
            4. BOUNDS: Ensure 0 <= score_awarded <= max_score.

            {rubric_ref}

            STUDENT EXTRACTED ANSWERS TO GRADE:
            {json.dumps(q_chunk, indent=2)}

            Return JSON format:
            {{
              "graded_questions": [
                {{
                  "q_number": "1a",
                  "question_text": "Exact Question Statement",
                  "student_answer": "Student Written Response",
                  "status": "CORRECT",
                  "score_awarded": 5,
                  "max_score": 5,
                  "explanation": "Clear, objective reason for marks awarded.",
                  "alternative_answers": ["Valid alternative answer"],
                  "remarks": "Brief teacher remark"
                }}
              ]
            }}
            """
            try:
                resp = await client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.0,
                    seed=42,
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
            "student_name": extracted_name or "Student Script",
            "score": total_score,
            "max_possible_score": max_possible,
            "questions": graded_all_questions,
            "qualitative_feedback": f"Demonstrates solid overall understanding across {len(graded_all_questions)} evaluated questions."
        }
        
        html = generate_html_report_from_json(ai_data, subject)
        matched_student, match_score = find_closest_student_match(extracted_name, students, threshold=0.50)
        
        if matched_student:
            matched_student_id = matched_student["id"]
            matched_student_name = matched_student["full_name"]
            matched = True
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
                
            task_obj = await session.get(BatchTask, task.id)
            if task_obj:
                task_obj.status = "COMPLETED"
                task_obj.updated_at = datetime.utcnow()
                await session.commit()
                
            # Check if all tasks in this batch are complete
            remaining_res = await session.execute(
                select(func.count(BatchTask.id)).where(
                    BatchTask.batch_id == task.batch_id,
                    BatchTask.status.in_(["QUEUED", "PROCESSING"])
                )
            )
            remaining_count = remaining_res.scalar() or 0
            if remaining_count == 0:
                batch_obj = await session.get(AssessmentBatch, task.batch_id)
                if batch_obj:
                    batch_obj.status = "Completed"
                    await session.commit()

        score_pct_broadcast = min(100, max(0, round((total_score / max_possible) * 100))) if max_possible > 0 else 0
        await broadcast_event(b_id, "paper_completed", {
            "paper_id": str(r_id),
            "paper_idx": str(r_id),
            "student_name": matched_student_name if matched else extracted_name,
            "score": score_pct_broadcast,
            "matched": matched,
            "phase": "Complete"
        })
        return True

    except Exception as e:
        print(f"Error processing batch task {task.id} (paper {r_id}): {e}")
        async with async_session_maker() as session:
            task_obj = await session.get(BatchTask, task.id)
            if task_obj:
                task_obj.last_error = str(e)
                if task_obj.attempts >= task_obj.max_retries:
                    task_obj.status = "FAILED"
                else:
                    task_obj.status = "QUEUED" # Retry
                task_obj.updated_at = datetime.utcnow()
                await session.commit()
                
            result_obj = await session.get(StudentResult, r_id)
            if result_obj:
                result_obj.needs_manual_review = True
                result_obj.ai_remarks = f"Error processing task: {str(e)}"
                await session.commit()
                
        await broadcast_event(b_id, "paper_error", {
            "paper_id": str(r_id),
            "paper_idx": str(r_id),
            "error": str(e)
        })
        return False


async def process_worker_loop(single_run: bool = False, poll_interval: float = 2.0, max_concurrency: int = 3):
    """
    Main background worker loop for picking up and processing queued tasks.
    """
    print(f"Background Worker Loop Started (Concurrency: {max_concurrency}, Poll Interval: {poll_interval}s)")
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def worker_wrapper(task: BatchTask):
        async with semaphore:
            await execute_task(task)
            
    while True:
        task = await fetch_and_lock_next_task()
        if task:
            print(f"Processing Task ID: {task.id} | Batch ID: {task.batch_id} | Attempt: {task.attempts}/{task.max_retries}")
            asyncio.create_task(worker_wrapper(task))
            await asyncio.sleep(0.1) # yield to allow concurrency
        else:
            if single_run:
                break
            await asyncio.sleep(poll_interval)


async def get_queue_metrics() -> Dict[str, Any]:
    """
    Fetches real-time task queue status and statistics from DB and Redis task broker.
    """
    async with async_session_maker() as session:
        query = select(BatchTask.status, func.count(BatchTask.id)).group_by(BatchTask.status)
        res = await session.execute(query)
        counts = dict(res.all())
        
        redis_len = 0
        redis_host = "disabled (DB Fallback)"
        r = await get_redis_client()
        if r:
            redis_url = os.getenv("REDIS_URL", "")
            redis_host = redis_url.split("@")[-1] if "@" in redis_url else (redis_url or "active")
            try:
                redis_len = await r.llen("edulytics:queue:batch_tasks")
            except Exception:
                pass
        
        return {
            "queued": counts.get("QUEUED", 0),
            "processing": counts.get("PROCESSING", 0),
            "completed": counts.get("COMPLETED", 0),
            "failed": counts.get("FAILED", 0),
            "total_tasks": sum(counts.values()),
            "redis_active": r is not None,
            "redis_host": redis_host,
            "redis_queue_length": redis_len
        }

