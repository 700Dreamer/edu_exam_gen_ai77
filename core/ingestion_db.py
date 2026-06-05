import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGEST_DB_PATH = os.path.join(BASE_DIR, "ingestion_staging.db")

def get_ingest_conn():
    conn = sqlite3.connect(INGEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_ingest_db():
    conn = get_ingest_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS extracted_content (
            filename TEXT PRIMARY KEY,
            level TEXT,
            subject TEXT,
            term TEXT,
            doc_type TEXT,
            content TEXT,
            content_length INTEGER,
            is_embedded INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending'
        )
    """)
    # Migration: Add missing columns if they don't exist
    try:
        conn.execute("ALTER TABLE extracted_content ADD COLUMN status TEXT DEFAULT 'Pending'")
    except: pass
    try:
        conn.execute("ALTER TABLE extracted_content ADD COLUMN last_error TEXT")
    except: pass
    
    conn.commit()
    conn.close()

def save_extracted_file(meta, status='Success', error=None):
    conn = get_ingest_conn()
    conn.execute("""
        INSERT OR REPLACE INTO extracted_content 
        (filename, level, subject, term, doc_type, content, content_length, status, last_error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meta["filename"], meta.get("level", "Unknown"), meta.get("subject", "Unknown"), 
        meta.get("term", "Unknown"), meta.get("doc_type", "Other"), 
        meta.get("content", ""), meta.get("content_length", 0),
        status, error
    ))
    conn.commit()
    conn.close()

def log_extraction_error(filename, error_msg):
    conn = get_ingest_conn()
    conn.execute("INSERT OR REPLACE INTO extracted_content (filename, status, last_error) VALUES (?, ?, ?)", (filename, 'Error', error_msg))
    conn.commit()
    conn.close()

def get_unembedded_files():
    conn = get_ingest_conn()
    rows = conn.execute("SELECT * FROM extracted_content WHERE is_embedded = 0 AND status = 'Success'").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_as_embedded(filenames):
    conn = get_ingest_conn()
    conn.executemany("UPDATE extracted_content SET is_embedded = 1, status = 'Done' WHERE filename = ?", [(f,) for f in filenames])
    conn.commit()
    conn.close()

def get_ingest_stats():
    conn = get_ingest_conn()
    total = conn.execute("SELECT COUNT(*) FROM extracted_content").fetchone()[0]
    embedded = conn.execute("SELECT COUNT(*) FROM extracted_content WHERE is_embedded = 1").fetchone()[0]
    errors = conn.execute("SELECT filename, last_error FROM extracted_content WHERE status = 'Error'").fetchall()
    filenames = [r[0] for r in conn.execute("SELECT filename FROM extracted_content WHERE status='Success' OR status='Done'").fetchall()]
    conn.close()
    return {
        "total_files": total, 
        "embedded_files": embedded, 
        "error_count": len(errors),
        "errors": [{"filename": r[0], "error": r[1]} for r in errors],
        "filenames": filenames
    }

init_ingest_db()
