"""
nursery_context.py
Extracts real exam/lesson content from nursery PDFs to inject into AI prompts.
Gives the AI variety by sampling from different papers each generation.
"""
import os
import random
import re

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NURSERY_DIR = os.path.join(BASE_DIR, "NURSERY ITEMS")

# Map each PDF to its class level(s) and learning area(s)
PDF_INDEX = {
    # ── BABY CLASS ──
    "BABY CLASS ENGLISH NOTES TERM III OSEB Educational consult-0": (["Baby Class"], ["LA1"]),
    "BABY CLASS LA 1 LESSON NOTES TM2 2024.pdf":  (["Baby Class"], ["LA1"]),
    "BABY CLASS LA 1 LESSON NOTES TM2.pdf":        (["Baby Class"], ["LA1"]),
    "BABY CLASS LA 2 LESSON NOTES TM2.pdf":        (["Baby Class"], ["LA2"]),
    "BABY CLASS LA 3 LESSON NOTES TM2.pdf":        (["Baby Class"], ["LA3"]),
    "BABY CLASS LESSON NOTES FOR SOCIAL DEVELOPMENT,2024.pdf": (["Baby Class"], ["LA5"]),
    "BABY HOLIDAY PACKAGE term 3.pdf":             (["Baby Class"], ["LA1", "LA4"]),
    "literacy scheme baby term 1.pdf":             (["Baby Class"], ["LA1"]),
    "TOP-MIDDLE-AND-BABY-CLASS-ENGLISH-MATHEMATICAL-CONCEPTS-AND-GENERAL-KNOWLEDGE-LESSON-NOTES.pdf":
        (["Baby Class", "Middle Class", "Top Class"], ["LA1", "LA4"]),

    # ── MIDDLE CLASS ──
    "EOT III MIDDLE LA4.pdf":                      (["Middle Class"], ["LA4"]),
    "LESSON-NOTES-FOR-ENGLISH-FOR-MIDDLE-CLASS-TERM-III-SIR-APOLLO-KAGGWA-SCHOOLS.pdf":
        (["Middle Class"], ["LA1"]),
    "LESSON-NOTES-FOR-NUMBERS-FOR-MIDDLE-CLASS-TERM-III.pdf": (["Middle Class"], ["LA4"]),
    "LESSON-NOTES-FOR-READING-FOR-MIDDLE-CLASS-TERM-I.pdf":   (["Middle Class"], ["LA1"]),
    "MIDDLE CLASS LA 1 LESSON NOTES TM 2.pdf":     (["Middle Class"], ["LA1"]),
    "MIDDLE CLASS LA 3 LESSON NOTES TM 2.pdf":     (["Middle Class"], ["LA3"]),
    "MIDDLE CLASS LA 5 LESSONNOTES TM2.pdf":       (["Middle Class"], ["LA5"]),
    "MIDDLE CLASS-LITERACY HOLIDAY WORK KINGS SCHOOL-KABOWA.pdf": (["Middle Class"], ["LA1"]),
    "MIDDLE CLASS-NUMBERS HOLIDAY WORK KINGS SCHOOL KABOWA.pdf":  (["Middle Class"], ["LA4"]),
    "MIDDLE EOT MATHS CONCEPTS.pdf":               (["Middle Class"], ["LA4"]),
    "MIDDLE HOLIDAY PACK term 3 2025.pdf":         (["Middle Class"], ["LA2", "LA4"]),
    "MIDDLE LA 4 BOT III.pdf":                     (["Middle Class"], ["LA4"]),
    "MIDDLE LA 4 MID II.pdf":                      (["Middle Class"], ["LA4"]),
    "MIDDLE LA 4 MID III.pdf":                     (["Middle Class"], ["LA4"]),
    "MIDDLE LA4 END I.pdf":                        (["Middle Class"], ["LA4"]),
    "MIDDLE LA4.pdf":                              (["Middle Class"], ["LA4"]),
    "MIDDLE-CLASS-EXTRA-HOLIDAY-WORK-TERM-ONE-2020-CORNERSTONE-JUNIOR-SCHOOL.pdf":
        (["Middle Class"], ["LA1", "LA4"]),
    "NUMERACY ( 4 - 5 YEARS ).pdf":               (["Middle Class"], ["LA4"]),
    "NUMERACY ( 4 - 5 YEARS).pdf":                (["Middle Class"], ["LA4"]),
    "NUMERACY BERRIES 4 - 5 YRS  CLASS.pdf":      (["Middle Class"], ["LA4"]),
    "Reading Middle Term III.pdf":                 (["Middle Class"], ["LA1"]),
    "BERRIES 4 - 5 YEARS   LANGUAGE DEVELOPMENT (1).pdf": (["Middle Class"], ["LA1"]),
    "LANGAUGE DEVELOPMENT ( 4 - 5  YEARS).pdf":   (["Middle Class"], ["LA1"]),
    "LANGUAGE DEVELOPMENT  ORANGE CLASS(4-5YEARS) (n).pdf": (["Middle Class"], ["LA1"]),
    "MIDDLE CLASS ROUTINE THIRD TERM.pdf":         (["Middle Class"], ["LA1", "LA2", "LA4"]),

    # ── TOP CLASS ──
    "TOP CLASS END OF  TERM  III  2022.pdf":       (["Top Class"], ["LA4"]),
    "TOP CLASS ENGLISH  RECESS PACKAGE,.pdf":      (["Top Class"], ["LA1"]),
    "TOP CLASS LA 1 LESSON NOTES TM 2.pdf":        (["Top Class"], ["LA1"]),
    "TOP CLASS LA 3 LESSON NOTES TM 2.pdf":        (["Top Class"], ["LA3"]),
    "TOP CLASS LA 5 LESSON NOTES TM 2.pdf":        (["Top Class"], ["LA5"]),
    "TOP CLASS LESSON NOTES NUMBERS  FULL YEAR 2022.pdf": (["Top Class"], ["LA4"]),
    "TOP CLASS NUMERACY.pdf":                      (["Top Class"], ["LA4"]),
    "LANGUAGE DEVELOPMENT (5 -6 ) TOP CLASS.pdf":  (["Top Class"], ["LA1"]),
    "LANGUAGE FOR TOP CLASS.pdf":                  (["Top Class"], ["LA1"]),
    "Top Class Notes.pdf":                         (["Top Class"], ["LA1", "LA4"]),
    "Top Class Numbers Scheme Term 2.pdf":         (["Top Class"], ["LA4"]),
    "Top Class Numbers Term 2 Lesson Notes.pdf":   (["Top Class"], ["LA4"]),
    "Top Class Reading Term II Lesson Notes.pdf":  (["Top Class"], ["LA1"]),
    "NUMERACY LESSON GUIDE FOR APPLE CLASS (1).pdf": (["Baby Class"], ["LA4"]),
    "LANGUAGE DEVELOPMENT FOR APPLE ( 3 - 4 YEARS).pdf": (["Baby Class"], ["LA1"]),
    "LANGUAGE DEVELOPMENT FOR APPLE CLASS (  3 - 4 YEARS).pdf": (["Baby Class"], ["LA1"]),
    "LANGUAGE DEVELOPMENT FOR APPLE CLASS 3 - 4 YRS  TERM ONE (1).pdf": (["Baby Class"], ["LA1"]),
}


def _extract_pdf_text(filepath: str, max_pages: int = 4) -> str:
    """Extract readable text from PDF, ignoring color errors."""
    if not HAS_PDFPLUMBER:
        return ""
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pdfplumber.open(filepath) as pdf:
                parts = []
                for page in pdf.pages[:max_pages]:
                    t = page.extract_text()
                    if t:
                        # Strip scanner noise lines
                        lines = [l for l in t.splitlines()
                                 if not l.startswith("Cannot set") and len(l.strip()) > 2]
                        parts.append("\n".join(lines))
                return "\n\n".join(parts)
    except Exception:
        return ""


def _extract_word_text(filepath: str) -> str:
    """Extract readable text from DOCX files, ignoring errors."""
    try:
        import docx
        doc = docx.Document(filepath)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception:
        return ""


def get_nursery_context(class_level: str, learning_area: str, n_samples: int = 3) -> str:
    """
    Returns real exam text from up to n_samples past papers matching the
    class level and learning area by dynamically querying ChromaDB (RAG).
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        
        chroma_client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "chroma_db"))
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        try:
            collection = chroma_client.get_collection(name="nursery_papers", embedding_function=openai_ef)
        except Exception:
            # Collection might not exist yet if script wasn't run
            return ""
        
        # We query the vector db using a synthetic ideal document
        query_text = f"Exam questions for {class_level} targeting learning area {learning_area}"
        
        # Add metadata filtering
        where_conditions = []
        if class_level != "Unknown":
            where_conditions.append({"class_level": class_level})
        if learning_area != "Unknown" and learning_area in ["LA1", "LA2", "LA3", "LA4", "LA5"]:
            where_conditions.append({"learning_area": learning_area})
            
        where_clause = None
        if len(where_conditions) == 1:
            where_clause = where_conditions[0]
        elif len(where_conditions) > 1:
            where_clause = {"$and": where_conditions}
            
        results = collection.query(
            query_texts=[query_text],
            n_results=n_samples,
            where=where_clause
        )
        
        if not results or not results.get("documents") or not results["documents"][0]:
            return ""
            
        snippets = []
        for doc in results["documents"][0]:
            # Take up to 1000 characters from the retrieved chunk to save tokens
            text_strip = doc.strip()
            if len(text_strip) > 1000:
                text_strip = text_strip[:1000]
            snippets.append(text_strip)
            
        joined = "\n\n---\n\n".join(snippets)
        return f"""REAL UGANDAN NURSERY EXAM CONTENT (RAG - Sampled from {len(snippets)} actual papers):
Use these as inspiration for question topics, vocabulary, and style — but generate NEW, DIFFERENT questions:

{joined}

---
"""
    except Exception as e:
        print(f"RAG Error in get_nursery_context: {e}")
        return ""
