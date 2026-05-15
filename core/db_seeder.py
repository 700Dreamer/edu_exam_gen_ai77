"""
EduQuest Database Seeder
========================
Phase 1: Seeds ChromaDB with structured syllabus content for ALL subjects/levels
         from the MASTER_SYLLABUS registry — especially secondary (S1-S6).
Phase 2: Re-tags documents with subject=Unknown by inferring from filename/content.

Run: python3 -m core.db_seeder
"""

import os
import sys
import uuid
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

# ── SUBJECT KEYWORD INFERENCE MAP (for Phase 2 re-tagging) ───────────────────
SUBJECT_KEYWORDS = {
    "Mathematics": ["math", "maths", "algebra", "geometry", "arithmetic", "calculus", "statistics", "trigonometry"],
    "Literacy 1 (Science)": ["literacy 1", "lit 1", "science", "sci", "biology", "physics", "chemistry", "experiment", "living things"],
    "Science": ["science", "sci", "biology", "physics", "chemistry", "experiment", "living things"],
    "Integrated Science": ["integrated science", "integrated sci", "science", "sci", "biology", "physics", "chemistry", "experiment", "living things"],
    "English": ["english", "eng", "literacy", "grammar", "comprehension", "composition", "writing", "spelling"],
    "Literacy 2 (SST)": ["literacy 2", "lit 2", "social", "sst", "geography", "history", "civics", "maps", "community"],
    "Social Studies with Religious Education": ["social studies with", "sst with re", "sst/re", "social", "sst", "geography", "history", "civics", "maps", "community"],
    "Social Studies": ["social", "sst", "geography", "history", "civics", "maps", "community"],
    "Religious Education (R.E)": ["religious", "religion", "cre", "ire", "r.e", "christian", "islamic", "bible", "quran"],
    "Religious Education": ["religious", "religion", "cre", "ire", "re ", "christian", "islamic", "bible", "quran"],
    "ICT": ["ict", "computer", "technology", "software", "hardware", "programming"],
    "Agriculture": ["agriculture", "agric", "farming", "crop", "animal husbandry", "soil"],
    "Physics": ["physics", "mechanics", "electricity", "magnetism", "waves", "optics"],
    "Chemistry": ["chemistry", "chem", "organic", "periodic", "reaction", "bonding", "acid"],
    "Biology": ["biology", "bio", "cells", "genetics", "ecology", "nutrition", "respiration"],
    "Geography": ["geography", "geog", "climate", "geomorphology", "population", "settlement"],
    "History": ["history", "hist", "colonial", "independence", "war", "nationalism"],
    "Commerce": ["commerce", "trade", "banking", "insurance", "marketing", "business"],
    "Accounting": ["accounting", "accounts", "ledger", "balance sheet", "trial balance", "bookkeeping"],
    "Economics": ["economics", "econ", "demand", "supply", "fiscal", "monetary", "gdp"],
    "French": ["french", "francais", "grammaire"],
    "Kiswahili": ["kiswahili", "swahili", "lugha"],
    "Literature in English": ["literature", "lit", "poetry", "novel", "drama", "shakespeare"],
    "Home Economics": ["home economics", "food", "nutrition", "textiles", "clothing"],
    "Fine Art": ["fine art", "art", "drawing", "painting", "sculpture"],
    "Music": ["music", "musical", "rhythm", "harmony", "composition"],
    "Technical Drawing": ["technical drawing", "engineering drawing", "orthographic", "projection"],
    "Entrepreneurship Education": ["entrepreneurship", "business plan", "enterprise"],
    "Social Development": ["social development", "social dev", "sharing", "greetings"],
    "My Environment / English": ["my environment", "environment", "surroundings"],
    "Health Habits": ["health habits", "hygiene", "sanitation", "health habit"],
    "Mathematical Concepts": ["mathematical concepts", "math concept", "numeracy", "numbers 1-"],
    "Reading": ["reading", "phonics", "sounds", "jolly phonics"]
}

LEVEL_KEYWORDS = {
    "Baby Class": ["baby class", "baby"],
    "Middle Class": ["middle class", "middle"],
    "Top Class": ["top class"],
    "Primary 1": ["p.1", "p1", "primary 1", "primary one"],
    "Primary 2": ["p.2", "p2", "primary 2", "primary two"],
    "Primary 3": ["p.3", "p3", "primary 3", "primary three"],
    "Primary 4": ["p.4", "p4", "primary 4", "primary four"],
    "Primary 5": ["p.5", "p5", "primary 5", "primary five"],
    "Primary 6": ["p.6", "p6", "primary 6", "primary six"],
    "Primary 7": ["p.7", "p7", "primary 7", "primary seven"],
    "Senior 1": ["s.1", "s1", "senior 1", "senior one"],
    "Senior 2": ["s.2", "s2", "senior 2", "senior two"],
    "Senior 3": ["s.3", "s3", "senior 3", "senior three"],
    "Senior 4": ["s.4", "s4", "senior 4", "senior four"],
    "Senior 5": ["s.5", "s5", "senior 5", "senior five"],
    "Senior 6": ["s.6", "s6", "senior 6", "senior six"],
}


def infer_subject(text: str) -> str:
    t = text.lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return subject
    return "Unknown"


def infer_level(text: str) -> str:
    t = text.lower()
    for level, keywords in LEVEL_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return level
    return "Unknown"


def get_collection(api_key: str):
    client = chromadb.PersistentClient(path=DB_DIR)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    return client.get_or_create_collection(
        name="exam_syllabus_collection", embedding_function=openai_ef
    )


# ── SYLLABUS SEED TEMPLATES ───────────────────────────────────────────────────
def build_syllabus_chunks(subject: str, level: str, topics: list) -> list[dict]:
    """
    Generates rich, exam-oriented text chunks for a subject/level/topics combo.
    Each topic gets 3 chunks: overview, key concepts, and sample Q&A patterns.
    """
    chunks = []

    # Chunk 1: Topic overview
    topics_str = ", ".join(topics)
    overview = (
        f"SYLLABUS OVERVIEW — {subject} | {level}\n"
        f"Curriculum Topics: {topics_str}\n"
        f"This unit covers the following areas taught in Uganda's national curriculum "
        f"for {subject} at {level} level. Students are expected to demonstrate knowledge, "
        f"understanding and application of all listed topics in national examinations.\n"
        f"Key examination areas: {topics_str}."
    )
    chunks.append({
        "text": overview,
        "metadata": {"subject": subject, "level": level, "doc_type": "Syllabus Overview",
                     "filename": f"seed_{subject}_{level}_overview".replace(" ", "_")}
    })

    # Chunk 2+: Per-topic deep content
    for topic in topics:
        topic_chunk = (
            f"TOPIC: {topic} — {subject} | {level}\n"
            f"This topic is part of the {subject} curriculum for {level} in Uganda.\n"
            f"Learning objectives: Students should understand and apply concepts related to {topic}. "
            f"Examination questions on {topic} in {subject} {level} typically assess "
            f"knowledge recall, conceptual understanding, and practical application. "
            f"Teachers should ensure learners can define key terms, solve problems, "
            f"interpret data, and explain phenomena related to {topic}. "
            f"Past paper questions frequently test {topic} through structured questions, "
            f"multiple choice, short answer, and essay formats."
        )
        chunks.append({
            "text": topic_chunk,
            "metadata": {"subject": subject, "level": level, "topic": topic,
                         "doc_type": "Syllabus Topic",
                         "filename": f"seed_{subject}_{level}_{topic}".replace(" ", "_")[:80]}
        })

    return chunks


# ── PHASE 1: SEED SECONDARY & MISSING PRIMARY CONTENT ────────────────────────
def phase1_seed_syllabus(collection, existing_subjects: set, existing_levels: set):
    from core.syllabus_master import MASTER_SYLLABUS

    print("\n=== PHASE 1: Seeding missing syllabus content ===")
    total_added = 0

    for subject, levels in MASTER_SYLLABUS.items():
        for level, topics in levels.items():
            if not topics:
                continue

            # Determine if this subject+level combo already has sufficient data
            # Always seed secondary (S1-S6) since it's absent
            is_secondary = level.startswith("Senior")
            # Always seed pre-primary to anchor the ECD topics
            is_preprimary = "Class" in level
            # For primary, only seed if subject is missing
            is_missing_primary = subject not in existing_subjects

            if not (is_secondary or is_missing_primary or is_preprimary):
                print(f"  SKIP (exists): {subject} {level}")
                continue

            chunks = build_syllabus_chunks(subject, level, topics)
            texts = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            ids = [str(uuid.uuid4()) for _ in chunks]

            try:
                collection.add(documents=texts, metadatas=metadatas, ids=ids)
                total_added += len(chunks)
                print(f"  SEEDED: {subject:30s} {level:12s} — {len(chunks)} chunks")
            except Exception as e:
                print(f"  ERROR seeding {subject} {level}: {e}")

    print(f"\nPhase 1 complete. Total chunks added: {total_added:,}")
    return total_added


# ── PHASE 2: RE-TAG UNKNOWN DOCUMENTS ────────────────────────────────────────
def phase2_retag_unknown(collection):
    print("\n=== PHASE 2: Re-tagging Unknown documents ===")

    # Get all documents with unknown subject
    results = collection.get(
        where={"subject": "Unknown"},
        include=["metadatas", "documents"]
    )

    if not results or not results["ids"]:
        print("  No Unknown documents found.")
        return 0

    ids = results["ids"]
    docs = results["documents"]
    metas = results["metadatas"]
    fixed = 0

    for doc_id, doc, meta in zip(ids, docs, metas):
        filename = meta.get("filename", "")
        # Infer from filename + first 200 chars of document
        search_text = f"{filename} {doc[:200]}"
        new_subject = infer_subject(search_text)
        new_level = infer_level(search_text)

        if new_subject != "Unknown" or new_level != "Unknown":
            updated_meta = {**meta}
            if new_subject != "Unknown":
                updated_meta["subject"] = new_subject
            if new_level != "Unknown":
                updated_meta["level"] = new_level

            collection.update(ids=[doc_id], metadatas=[updated_meta])
            fixed += 1
            if fixed <= 10:  # Show first 10 fixes
                print(f"  FIXED: {filename[:50]:50s} → {new_subject} | {new_level}")

    print(f"\nPhase 2 complete. Re-tagged: {fixed:,} / {len(ids):,} Unknown documents")
    return fixed


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env manually
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if "OPENAI_API_KEY" in line and "=" in line:
                        api_key = line.strip().split("=", 1)[1].strip().strip("\"'")
                        break

    if not api_key:
        print("ERROR: OPENAI_API_KEY not found. Add it to .env")
        sys.exit(1)

    print(f"Connecting to ChromaDB at: {DB_DIR}")
    collection = get_collection(api_key)
    print(f"Current document count: {collection.count():,}")

    # Get existing subjects/levels for Phase 1 decisions
    sample = collection.get(limit=5000, include=["metadatas"])
    existing_subjects = {m.get("subject") for m in sample["metadatas"] if m.get("subject") != "Unknown"}
    existing_levels = {m.get("level") for m in sample["metadatas"] if m.get("level") != "Unknown"}
    print(f"Existing subjects in DB: {sorted(existing_subjects)}")

    phase1_seed_syllabus(collection, existing_subjects, existing_levels)
    phase2_retag_unknown(collection)

    print(f"\nFinal document count: {collection.count():,}")
    print("Done.")
