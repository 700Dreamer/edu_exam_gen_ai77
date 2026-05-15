"""
UNEB / National Exam Paper Structure Registry
Maps each Subject + Level combination to the actual paper structure
used in Uganda's national examinations (PLE, UCE, UACE).

Sources: UNEB official specimen papers and past papers.
"""

from typing import Optional

# ─── PAPER STRUCTURE DEFINITION ────────────────────────────────────────────
# Each entry:
#   "sec_a_count": int   — number of objective/short-answer questions
#   "sec_a_marks": int   — marks for section A
#   "sec_b_count": int   — number of structured/essay questions
#   "sec_b_marks": int   — marks for section B
#   "total_marks": int
#   "duration":    str   — e.g. "2 HRS 30 MIN"
#   "description": str   — official paper name

PAPER_STRUCTURES = {

    # ─── PRIMARY LEAVING EXAMINATION (PLE) ───────────────────────────────
    ("Mathematics", "Primary 7"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Mathematics Paper 1 (PLE)",
        "sec_b_note": "Answer all 5 questions in Section B (structured)"
    },
    ("Science", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 10, "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Science Paper (PLE)",
        "sec_b_note": "Answer 10 questions in Section B"
    },
    ("English", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 5,  "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "English Language Paper (PLE)",
        "sec_b_note": "Section B: Composition, Letter Writing, Grammar"
    },
    ("Social Studies", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 15, "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Social Studies / Religious Education (PLE)",
        "sec_b_note": "Answer 15 questions in Section B"
    },
    ("Religious Education", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 15, "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Social Studies / Religious Education (PLE)",
        "sec_b_note": "Answer 15 questions in Section B"
    },

    # ─── LOWER PRIMARY (Internal / Promotional) ───────────────────────────
    ("Mathematics", "Primary 1"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 30,
        "total_marks": 50,  "duration": "1 HR 30 MIN",
        "description": "Mathematics Promotional Examination",
    },
    ("Mathematics", "Primary 2"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 30,
        "total_marks": 50,  "duration": "1 HR 30 MIN",
        "description": "Mathematics Promotional Examination",
    },
    ("Mathematics", "Primary 3"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 30,
        "total_marks": 50,  "duration": "1 HR 30 MIN",
        "description": "Mathematics Promotional Examination",
    },
    ("Mathematics", "Primary 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 40,
        "total_marks": 60,  "duration": "2 HRS",
        "description": "Mathematics Promotional Examination",
    },
    ("Mathematics", "Primary 5"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 40,
        "total_marks": 60,  "duration": "2 HRS",
        "description": "Mathematics Promotional Examination",
    },
    ("Mathematics", "Primary 6"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 40,
        "total_marks": 60,  "duration": "2 HRS",
        "description": "Mathematics Promotional Examination",
    },
    ("Social Studies", "Primary 6"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 80,  "duration": "2 HRS",
        "description": "Social Studies Promotional Examination",
    },
    ("Social Studies", "Primary 5"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 70,  "duration": "2 HRS",
        "description": "Social Studies Promotional Examination",
    },
    ("Social Studies", "Primary 4"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 70,  "duration": "1 HR 30 MIN",
        "description": "Social Studies Promotional Examination",
    },
    ("Science", "Primary 6"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 80,  "duration": "2 HRS",
        "description": "Science Promotional Examination",
    },
    ("English", "Primary 6"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 5,  "sec_b_marks": 40,
        "total_marks": 70,  "duration": "2 HRS",
        "description": "English Language Promotional Examination",
    },

    # ─── UGANDA CERTIFICATE OF EDUCATION (UCE / O-Level) ─────────────────
    ("Mathematics", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 10, "sec_b_marks": 80,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Mathematics UCE Paper 1 + 2",
        "sec_b_note": "Answer any 8 out of 10 questions in Section B"
    },
    ("Physics", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Physics UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("Chemistry", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Chemistry UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("Biology", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Biology UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("English", "Senior 4"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 5,  "sec_b_marks": 70,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "English Language UCE Paper",
        "sec_b_note": "Section B: Comprehension, Summary, Composition"
    },

    # ─── UACE (A-Level) ───────────────────────────────────────────────────
    ("Mathematics", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 15, "sec_b_marks": 150,
        "total_marks": 150, "duration": "3 HRS",
        "description": "Mathematics UACE Paper (Pure & Applied)",
        "sec_b_note": "Answer 5 compulsory questions + choose from optional sections"
    },
    ("Physics", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Physics UACE Paper",
        "sec_b_note": "Answer any 5 questions"
    },

    # ─── GEOGRAPHY ────────────────────────────────────────────────────────
    ("Geography", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Geography UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("Geography", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Geography UACE Paper",
        "sec_b_note": "Answer any 5 questions"
    },

    # ─── HISTORY ──────────────────────────────────────────────────────────
    ("History", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "History UCE Paper",
        "sec_b_note": "Answer any 6 essay questions in Section B"
    },
    ("History", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "History UACE Paper",
        "sec_b_note": "Answer any 5 questions"
    },

    # ─── COMMERCE ─────────────────────────────────────────────────────────
    ("Commerce", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Commerce UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },

    # ─── ACCOUNTING ───────────────────────────────────────────────────────
    ("Accounting", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Accounting UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("Accounting", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Accounting UACE Paper",
        "sec_b_note": "Answer any 5 questions"
    },

    # ─── ECONOMICS ────────────────────────────────────────────────────────
    ("Economics", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Economics UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },
    ("Economics", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Economics UACE Paper",
        "sec_b_note": "Answer any 5 questions"
    },

    # ─── AGRICULTURE ──────────────────────────────────────────────────────
    ("Agriculture", "Primary 7"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 70,  "duration": "2 HRS",
        "description": "Agriculture Promotional Examination (PLE)"
    },
    ("Agriculture", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Agriculture UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },

    # ─── ICT ──────────────────────────────────────────────────────────────
    ("ICT", "Primary 7"): {
        "sec_a_count": 30, "sec_a_marks": 30,
        "sec_b_count": 10, "sec_b_marks": 40,
        "total_marks": 70,  "duration": "2 HRS",
        "description": "ICT Promotional Examination"
    },
    ("ICT", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "ICT UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },

    # ─── CHRISTIAN RELIGIOUS EDUCATION ────────────────────────────────────
    ("Christian Religious Education", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 15, "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "CRE Paper (PLE)",
        "sec_b_note": "Answer 15 questions in Section B"
    },
    ("Christian Religious Education", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "CRE UCE Paper",
        "sec_b_note": "Answer any 6 essay questions"
    },

    # ─── ISLAMIC RELIGIOUS EDUCATION ──────────────────────────────────────
    ("Islamic Religious Education", "Primary 7"): {
        "sec_a_count": 40, "sec_a_marks": 40,
        "sec_b_count": 15, "sec_b_marks": 60,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "IRE Paper (PLE)",
        "sec_b_note": "Answer 15 questions in Section B"
    },
    ("Islamic Religious Education", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "IRE UCE Paper",
        "sec_b_note": "Answer any 6 essay questions"
    },

    # ─── LITERATURE IN ENGLISH ────────────────────────────────────────────
    ("Literature in English", "Senior 4"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Literature in English UCE Paper",
        "sec_b_note": "Answer 4 questions, at least one from each section"
    },
    ("Literature in English", "Senior 6"): {
        "sec_a_count": 0,  "sec_a_marks": 0,
        "sec_b_count": 8,  "sec_b_marks": 100,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Literature in English UACE Paper",
        "sec_b_note": "Answer any 4 questions"
    },

    # ─── FRENCH ───────────────────────────────────────────────────────────
    ("French", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "French UCE Paper",
        "sec_b_note": "Section B: Comprehension, Translation, Composition"
    },

    # ─── KISWAHILI ────────────────────────────────────────────────────────
    ("Kiswahili", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Kiswahili UCE Paper",
        "sec_b_note": "Section B: Ufahamu, Insha, Sarufi"
    },

    # ─── HOME ECONOMICS ───────────────────────────────────────────────────
    ("Home Economics", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Home Economics UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },

    # ─── FINE ART ─────────────────────────────────────────────────────────
    ("Fine Art", "Senior 4"): {
        "sec_a_count": 10, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Fine Art UCE Theory Paper",
        "sec_b_note": "Answer any 4 questions in Section B"
    },

    # ─── MUSIC ────────────────────────────────────────────────────────────
    ("Music", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Music UCE Theory Paper",
        "sec_b_note": "Answer any 4 questions in Section B"
    },

    # ─── TECHNICAL DRAWING ────────────────────────────────────────────────
    ("Technical Drawing", "Senior 4"): {
        "sec_a_count": 10, "sec_a_marks": 20,
        "sec_b_count": 5,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "3 HRS",
        "description": "Technical Drawing UCE Paper",
        "sec_b_note": "Answer any 4 questions requiring drawn solutions"
    },

    # ─── ENTREPRENEURSHIP EDUCATION ───────────────────────────────────────
    ("Entrepreneurship Education", "Senior 4"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 8,  "sec_b_marks": 80,
        "total_marks": 100, "duration": "2 HRS 30 MIN",
        "description": "Entrepreneurship Education UCE Paper",
        "sec_b_note": "Answer any 6 questions in Section B"
    },

    # ─── PRE-PRIMARY (Internal Assessment) ───────────────────────────────
    ("Pre-Primary", "Baby Class"): {
        "sec_a_count": 10, "sec_a_marks": 10,
        "sec_b_count": 0,  "sec_b_marks": 0,
        "total_marks": 10,  "duration": "30 MIN",
        "description": "Baby Class Internal Assessment"
    },
    ("Pre-Primary", "Middle Class"): {
        "sec_a_count": 15, "sec_a_marks": 15,
        "sec_b_count": 0,  "sec_b_marks": 0,
        "total_marks": 15,  "duration": "45 MIN",
        "description": "Middle Class Internal Assessment"
    },
    ("Pre-Primary", "Top Class"): {
        "sec_a_count": 20, "sec_a_marks": 20,
        "sec_b_count": 0,  "sec_b_marks": 0,
        "total_marks": 20,  "duration": "1 HR",
        "description": "Top Class Internal Assessment"
    },
}

# ─── DEFAULT (fallback for unlisted combinations) ─────────────────────────
DEFAULT_STRUCTURE = {
    "sec_a_count": 40, "sec_a_marks": 40,
    "sec_b_count": 15, "sec_b_marks": 60,
    "total_marks": 100, "duration": "2 HRS 30 MIN",
    "description": "Standard Examination Paper",
}


def get_paper_structure(subject: str, level: str) -> dict:
    """Returns the official UNEB paper structure for the given subject/level."""
    # Intercept Pre-Primary levels regardless of subject to enforce single-section ECD format
    if level in ["Baby Class", "Middle Class", "Top Class"]:
        return PAPER_STRUCTURES.get(("Pre-Primary", level))
        
    structure = PAPER_STRUCTURES.get((subject, level))
    if structure:
        return structure
        
    # Provide a sane fallback for Lower Primary (P1-P3) to avoid huge 55-question exams
    if level in ["Primary 1", "Primary 2", "Primary 3"]:
        return {
            "sec_a_count": 20, "sec_a_marks": 20,
            "sec_b_count": 5,  "sec_b_marks": 30,
            "total_marks": 50,  "duration": "1 HR 30 MIN",
            "description": f"{subject} Lower Primary Assessment"
        }
        
    return DEFAULT_STRUCTURE


def get_total_questions(subject: str, level: str) -> int:
    """Returns the official total question count (A + B) for the paper."""
    s = get_paper_structure(subject, level)
    return s["sec_a_count"] + s["sec_b_count"]
