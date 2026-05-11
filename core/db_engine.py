import os
import chromadb
from chromadb.utils import embedding_functions

# Get the base directory automatically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

def get_chroma_collection():
    """Initializes and returns the ChromaDB connection."""
    try:
        chroma_client = chromadb.PersistentClient(path=DB_DIR)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from environment variables.")
            
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key, 
            model_name="text-embedding-3-small"
        )
        return chroma_client.get_collection(name="exam_syllabus_collection", embedding_function=openai_ef)
    except Exception as e:
        print(f"Database Warning: {e}")
        return None

def retrieve_syllabus_context(level, subject, term, topic, strategy="syllabus"):
    """Safely retrieves context from the vector database with Semantic Re-Ranking."""
    collection = get_chroma_collection()
    if not collection:
        return ""
    
    try:
        search_query = f"{level} {subject} {term} {topic} {strategy}"
        # Step 1: Broad Retrieval (fetch 15 candidates)
        results = collection.query(query_texts=[search_query], n_results=15)
        
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}]*len(docs)
            
            # Step 2: Semantic Re-Ranking (Select top 5 best matches)
            from core.reranker import get_reranker
            ranker = get_reranker()
            
            rerank_docs = [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
            top_results = ranker.rerank(search_query, rerank_docs, top_n=5)
            
            final_context = "\n\n".join([r["text"] for r in top_results])
            return final_context
            
        return ""
    except Exception as e:
        print(f"Retrieval / Re-Rank Error: {e}")
        return ""

# ── PERSISTENT SQLITE STORAGE FOR AI STUDIO LIBRARY ──
import sqlite3
import uuid
import json
from datetime import datetime

def get_db_connection():
    """Establishes connection to the local lightweight database."""
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'eduquest_history.db'), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS projects
                    (id TEXT PRIMARY KEY, title TEXT, mode TEXT, 
                     subject TEXT, level TEXT, term TEXT, timestamp TEXT, data JSON)''')
    
    # Simple migration: add columns if they don't exist
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN level TEXT DEFAULT 'Unknown'")
        conn.execute("ALTER TABLE projects ADD COLUMN term TEXT DEFAULT 'Unknown'")
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    conn.commit()
    conn.close()

def save_project(title, mode, subject, level, term, data_json):
    """Saves a generated JSON document into the Studio Library."""
    conn = get_db_connection()
    project_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                 (project_id, title, mode, subject, level, term, timestamp, data_json))
    conn.commit()
    conn.close()
    return project_id

def load_projects():
    """Loads all previously generated projects sorted by newest first."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM projects ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Run initialization safely on module load
init_db()
