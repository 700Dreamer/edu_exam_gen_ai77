"""
Edulytics PDF Report Generator
-------------------------------
Server-side PDF generation using WeasyPrint + Jinja2.
Generates two report types:
  1. Individual Student Report PDF
  2. Class Performance Report PDF (with optional ZIP bundle of all student PDFs)
"""

import os
import sys
import re
import uuid
import io
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# Expose Homebrew C libraries (libgobject, libpango, libcairo) to cffi on macOS
if sys.platform == "darwin":
    _homebrew_libs = ["/opt/homebrew/lib", "/usr/local/lib"]
    _existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    _paths = [p for p in _homebrew_libs if os.path.exists(p)]
    if _existing:
        _paths.append(_existing)
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(_paths)

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from sqlalchemy import select
from core.models import (
    async_session_maker, StudentResult, Student,
    AssessmentBatch, AcademicGroup, Tenant
)

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
REPORTS_DIR = os.path.join(BASE_DIR, "static", "uploads", "reports")

# Ensure reports output directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── Jinja2 Environment ──
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True
)

# ── Grade Scale ──
GRADE_SCALE = [
    ("A", 80, 100),
    ("B", 70, 79),
    ("C", 60, 69),
    ("D", 50, 59),
    ("F", 0, 49),
]


def get_grade_letter(score: int) -> str:
    """Returns the grade letter for a given percentage score."""
    for letter, low, high in GRADE_SCALE:
        if low <= score <= high:
            return letter
    return "F"


def parse_questions_from_html(raw_html: str) -> List[Dict[str, Any]]:
    """
    Parses the raw_extracted_html from a StudentResult into structured question data.
    Mirrors the parseResultQuestions logic from GradebookView.tsx.
    """
    if not raw_html:
        return []

    try:
        from lxml import etree
        parser = etree.HTMLParser()
        doc = etree.fromstring(raw_html, parser)

        rows = doc.xpath("//table//tbody//tr")
        questions = []

        for tr in rows:
            tds = tr.findall("td")
            if len(tds) < 5:
                continue

            q_num_raw = (tds[0].text or "").strip()
            q_num = re.sub(r'^Q', '', q_num_raw, flags=re.IGNORECASE).strip()

            q_text = _get_text(tds[1])
            student_ans = _get_text(tds[2])
            status_text = _get_text(tds[3]).upper()
            score_str = _get_text(tds[4])

            explanation = _get_text(tds[5]) if len(tds) > 5 else ""
            remarks = _get_text(tds[6]) if len(tds) > 6 else ""

            # Clean up explanation: strip HTML tags for PDF
            explanation_clean = re.sub(r'<[^>]+>', '', explanation).strip()
            if remarks:
                explanation_clean = f"{explanation_clean} {remarks}".strip()

            # Parse score fraction
            score_awarded = 0.0
            max_score = 5.0
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', score_str)
            if score_match:
                score_awarded = float(score_match.group(1))
                max_score = float(score_match.group(2))

            questions.append({
                "q_num": q_num,
                "q_text": q_text,
                "student_ans": student_ans,
                "status": status_text,
                "score_str": score_str,
                "score_awarded": score_awarded,
                "max_score": max_score,
                "explanation_clean": explanation_clean,
            })

        return questions
    except Exception as e:
        print(f"[PDF Generator] Error parsing questions HTML: {e}")
        return []


def _get_text(element) -> str:
    """Extracts all text content from an lxml element, including nested children."""
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def parse_batch_insights(insights_html: str) -> Dict[str, Any]:
    """
    Parses the batch_insights HTML into structured sections:
    general, strengths, weaknesses.
    """
    result = {"general": "", "strengths": [], "weaknesses": []}
    if not insights_html:
        return result

    try:
        from lxml import etree
        parser = etree.HTMLParser()
        doc = etree.fromstring(insights_html, parser)

        # Try to find structured sections by ID first
        general_el = doc.xpath('//*[@id="general-insight"]') or doc.xpath('//*[contains(@id, "insight")]')
        strengths_el = doc.xpath('//*[@id="key-strengths"]') or doc.xpath('//*[contains(@id, "strength")]')
        weaknesses_el = doc.xpath('//*[@id="key-weaknesses"]') or doc.xpath('//*[contains(@id, "weakness")]')

        if general_el:
            result["general"] = _get_text(general_el[0])
        if strengths_el:
            lis = strengths_el[0].findall(".//li")
            result["strengths"] = [_get_text(li) for li in lis if _get_text(li)]
        if weaknesses_el:
            lis = weaknesses_el[0].findall(".//li")
            result["weaknesses"] = [_get_text(li) for li in lis if _get_text(li)]

        # Fallback: parse by heading text
        if not result["general"] and not result["strengths"] and not result["weaknesses"]:
            body = doc.find(".//body")
            if body is None:
                body = doc
            current_section = ""
            for child in body:
                text = _get_text(child)
                lower = text.lower()
                tag = child.tag if hasattr(child, 'tag') else ""

                if tag in ("h1", "h2", "h3", "h4") or (tag == "p" and child.find("strong") is not None and len(text) < 100):
                    if "insight" in lower or "performance" in lower:
                        current_section = "general"
                    elif "strength" in lower:
                        current_section = "strengths"
                    elif "weakness" in lower or "improvement" in lower:
                        current_section = "weaknesses"
                else:
                    if current_section == "general":
                        result["general"] += " " + text
                    elif current_section in ("strengths", "weaknesses"):
                        lis = child.findall(".//li")
                        if lis:
                            for li in lis:
                                t = _get_text(li)
                                if t:
                                    result[current_section].append(t)
                        elif text:
                            result[current_section].append(text)

            result["general"] = result["general"].strip()

    except Exception as e:
        print(f"[PDF Generator] Error parsing batch insights: {e}")
        # Fallback: use raw text
        plain = re.sub(r'<[^>]+>', ' ', insights_html).strip()
        result["general"] = plain[:500]

    return result


def _render_pdf_bytes(template_name: str, context: Dict[str, Any]) -> bytes:
    """Renders a Jinja2 HTML template to PDF bytes using WeasyPrint."""
    template = jinja_env.get_template(template_name)
    html_string = template.render(**context)

    font_config = FontConfiguration()
    html_doc = HTML(
        string=html_string,
        base_url=TEMPLATES_DIR
    )
    pdf_bytes = html_doc.write_pdf(font_config=font_config)
    return pdf_bytes


# ── Public API ──

async def generate_student_pdf(result_id: str) -> Tuple[bytes, str]:
    """
    Generates a single student report PDF.
    Returns (pdf_bytes, suggested_filename).
    """
    r_uuid = uuid.UUID(result_id)

    async with async_session_maker() as session:
        result_obj = await session.get(StudentResult, r_uuid)
        if not result_obj:
            raise ValueError(f"StudentResult {result_id} not found")

        batch_obj = await session.get(AssessmentBatch, result_obj.batch_id)
        if not batch_obj:
            raise ValueError(f"AssessmentBatch not found for result {result_id}")

        group_obj = await session.get(AcademicGroup, batch_obj.academic_group_id)
        tenant_obj = await session.get(Tenant, group_obj.tenant_id) if group_obj else None

        student_obj = None
        if result_obj.student_id:
            student_obj = await session.get(Student, result_obj.student_id)

        # Fetch all results in the batch for ranking
        all_results_q = select(StudentResult, Student).outerjoin(
            Student, StudentResult.student_id == Student.id
        ).where(
            StudentResult.batch_id == result_obj.batch_id,
            StudentResult.total_score != None
        )
        all_res = await session.execute(all_results_q)
        all_rows = all_res.all()

    # Compute class stats
    scores = [r.total_score for r, s in all_rows if r.total_score is not None]
    class_average = round(sum(scores) / len(scores), 1) if scores else 0
    total_students = len(scores)

    # Compute rank
    sorted_scores = sorted(scores, reverse=True)
    student_score = result_obj.total_score if result_obj.total_score is not None else 0
    student_score_clamped = min(100, max(0, round(student_score)))
    class_rank = sorted_scores.index(student_score_clamped) + 1 if student_score_clamped in sorted_scores else total_students

    # Parse questions
    questions = parse_questions_from_html(result_obj.raw_extracted_html or "")

    # Filter by attempted items if present
    attempted = result_obj.attempted_items
    if attempted and isinstance(attempted, dict) and "items" in attempted:
        attempted_nums = set(attempted["items"])
        questions = [q for q in questions if q["q_num"] in attempted_nums]

    student_name = student_obj.full_name if student_obj else "Unmatched Student"
    index_number = student_obj.index_number if student_obj else None
    school_name = tenant_obj.name if tenant_obj else "School"
    level = group_obj.level if group_obj else ""
    stream = group_obj.stream if group_obj else ""

    context = {
        "student_name": student_name,
        "index_number": index_number,
        "score": student_score_clamped,
        "grade_letter": get_grade_letter(student_score_clamped),
        "class_rank": class_rank,
        "total_students": total_students,
        "class_average": class_average,
        "school_name": school_name,
        "level": level,
        "stream": stream,
        "subject": batch_obj.subject,
        "exam_type": batch_obj.exam_type,
        "exam_date": batch_obj.created_at.strftime("%d %B %Y"),
        "questions": questions,
        "ai_remarks": result_obj.ai_remarks or "",
        "generated_at": datetime.utcnow().strftime("%d %B %Y, %H:%M UTC"),
    }

    pdf_bytes = _render_pdf_bytes("student_report.html", context)

    safe_name = re.sub(r'[^\w\s-]', '', student_name).strip().replace(' ', '_')
    filename = f"Edulytics_{safe_name}_{batch_obj.subject}_Report.pdf"

    return pdf_bytes, filename


async def generate_class_report_zip(batch_id: str) -> Tuple[str, str]:
    """
    Generates a ZIP containing:
      - ClassReport.pdf (class performance overview)
      - Individual student PDFs for every graded student in the batch

    Returns (zip_file_path, suggested_filename).
    The ZIP is saved to disk at the returned path.
    """
    batch_uuid = uuid.UUID(batch_id)

    async with async_session_maker() as session:
        batch_obj = await session.get(AssessmentBatch, batch_uuid)
        if not batch_obj:
            raise ValueError(f"AssessmentBatch {batch_id} not found")

        group_obj = await session.get(AcademicGroup, batch_obj.academic_group_id)
        tenant_obj = await session.get(Tenant, group_obj.tenant_id) if group_obj else None

        # Fetch all results
        all_results_q = select(StudentResult, Student).outerjoin(
            Student, StudentResult.student_id == Student.id
        ).where(StudentResult.batch_id == batch_uuid)
        all_res = await session.execute(all_results_q)
        all_rows = all_res.all()

        # Score distribution
        graded_rows = [(r, s) for r, s in all_rows if r.total_score is not None and not r.needs_manual_review]
        scores = [r.total_score for r, s in graded_rows]

        # Batch insights
        insights_html = batch_obj.batch_insights or ""

    if not scores:
        scores = [0]

    class_average = round(sum(scores) / len(scores), 1)
    highest_score = max(scores)
    lowest_score = min(scores)
    pass_count = sum(1 for s in scores if s >= 50)
    pass_rate = round((pass_count / len(scores)) * 100, 1) if scores else 0
    total_students = len(scores)

    school_name = tenant_obj.name if tenant_obj else "School"
    level = group_obj.level if group_obj else ""
    stream = group_obj.stream if group_obj else ""

    # Score distribution buckets
    buckets = {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for s in scores:
        if s < 50:
            buckets["0-49"] += 1
        elif s < 60:
            buckets["50-59"] += 1
        elif s < 70:
            buckets["60-69"] += 1
        elif s < 80:
            buckets["70-79"] += 1
        elif s < 90:
            buckets["80-89"] += 1
        else:
            buckets["90-100"] += 1

    max_bucket = max(buckets.values()) if buckets.values() else 1
    distribution_buckets = []
    for key, count in buckets.items():
        bar_height = max(2, int((count / max(max_bucket, 1)) * 60))
        distribution_buckets.append({
            "key": key,
            "label": key,
            "count": count,
            "bar_height": bar_height,
        })

    # Grade distribution
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for s in scores:
        grade_counts[get_grade_letter(min(100, max(0, round(s))))] += 1

    grade_distribution = [
        {"letter": "A", "count": grade_counts["A"], "range": "80-100%"},
        {"letter": "B", "count": grade_counts["B"], "range": "70-79%"},
        {"letter": "C", "count": grade_counts["C"], "range": "60-69%"},
        {"letter": "D", "count": grade_counts["D"], "range": "50-59%"},
        {"letter": "F", "count": grade_counts["F"], "range": "0-49%"},
    ]

    # Ranked student list
    ranked = sorted(graded_rows, key=lambda x: x[0].total_score or 0, reverse=True)
    ranked_students = []
    for rank_idx, (r, s) in enumerate(ranked, 1):
        sc = min(100, max(0, round(r.total_score or 0)))
        ranked_students.append({
            "rank": rank_idx,
            "student_name": s.full_name if s else "Unmatched",
            "index_number": s.index_number if s else None,
            "score": sc,
            "grade": get_grade_letter(sc),
        })

    # Parse batch insights
    parsed_insights = parse_batch_insights(insights_html)

    class_context = {
        "school_name": school_name,
        "level": level,
        "stream": stream,
        "subject": batch_obj.subject,
        "exam_type": batch_obj.exam_type,
        "exam_date": batch_obj.created_at.strftime("%d %B %Y"),
        "total_students": total_students,
        "class_average": class_average,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "pass_rate": pass_rate,
        "distribution_buckets": distribution_buckets,
        "grade_distribution": grade_distribution,
        "ranked_students": ranked_students,
        "insights_general": parsed_insights["general"],
        "insights_strengths": parsed_insights["strengths"],
        "insights_weaknesses": parsed_insights["weaknesses"],
        "generated_at": datetime.utcnow().strftime("%d %B %Y, %H:%M UTC"),
    }

    # Generate class report PDF
    class_pdf = _render_pdf_bytes("class_report.html", class_context)

    # Generate individual student PDFs
    student_pdfs: List[Tuple[str, bytes]] = []
    for r, s in graded_rows:
        try:
            pdf_bytes, pdf_filename = await generate_student_pdf(str(r.id))
            student_pdfs.append((pdf_filename, pdf_bytes))
        except Exception as e:
            print(f"[PDF Generator] Error generating PDF for result {r.id}: {e}")
            continue

    # Bundle into ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Class_Report_{batch_obj.subject}_{level}_{stream}.pdf", class_pdf)
        for filename, pdf_data in student_pdfs:
            zf.writestr(f"Student_Reports/{filename}", pdf_data)

    zip_buffer.seek(0)

    # Save to disk
    batch_report_dir = os.path.join(REPORTS_DIR, batch_id)
    os.makedirs(batch_report_dir, exist_ok=True)

    safe_school = re.sub(r'[^\w\s-]', '', school_name).strip().replace(' ', '_')
    zip_filename = f"Edulytics_{safe_school}_{batch_obj.subject}_{level}_{stream}_Reports.zip"
    zip_path = os.path.join(batch_report_dir, zip_filename)

    with open(zip_path, 'wb') as f:
        f.write(zip_buffer.getvalue())

    return zip_path, zip_filename
