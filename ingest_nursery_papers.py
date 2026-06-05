import os
import docx
from tqdm import tqdm
try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Warning: chromadb not found.")
    chromadb = None

# Secure Environment Loader
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val.strip("'\"")

if "OPENAI_API_KEY" not in os.environ:
    print("Error: OPENAI_API_KEY not found in .env file.")
    exit(1)

DB_DIR = os.path.join(BASE_DIR, "chroma_db")
PAPERS_DIR = os.path.join(BASE_DIR, "PRIMARY PAPERS")

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def ingest_nursery_papers():
    if not chromadb:
        return
        
    print("Initializing ChromaDB and OpenAI Embeddings...")
    chroma_client = chromadb.PersistentClient(path=DB_DIR)
    
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )

    collection = chroma_client.get_or_create_collection(
        name="nursery_papers",
        embedding_function=openai_ef
    )
    print("Connected to ChromaDB collection: nursery_papers")
    
    existing_filenames = set()
    total_docs = collection.count()
    if total_docs > 0:
        batch_data = collection.get(include=["metadatas"])
        if batch_data and batch_data.get("metadatas"):
            for m in batch_data["metadatas"]:
                if m and "filename" in m:
                    existing_filenames.add(m["filename"])
                    
    print(f"Found {len(existing_filenames)} documents currently in the Vector DB.")

    docs_to_embed = []
    
    # Target identifiers for nursery exams
    nursery_keywords = ["nursery", "baby", "middle", "top"]
    
    for root, dirs, files in os.walk(PAPERS_DIR):
        for file in files:
            if file.endswith(".docx"):
                filepath = os.path.join(root, file)
                filepath_lower = filepath.lower()
                
                if any(kw in filepath_lower for kw in nursery_keywords):
                    if filepath in existing_filenames:
                        continue
                        
                    text = extract_text_from_docx(filepath)
                    if len(text) > 50: # filter out empty/corrupt files
                        
                        # Infer class level
                        class_level = "Unknown"
                        if "baby" in filepath_lower: class_level = "Baby Class"
                        elif "middle" in filepath_lower: class_level = "Middle Class"
                        elif "top" in filepath_lower: class_level = "Top Class"
                        
                        # Infer Learning Area (rough approximation)
                        la = "Unknown"
                        if "la" in filepath_lower or "l.a" in filepath_lower:
                            if "1" in filepath_lower: la = "LA1"
                            elif "2" in filepath_lower: la = "LA2"
                            elif "3" in filepath_lower: la = "LA3"
                            elif "4" in filepath_lower or "math" in filepath_lower or "num" in filepath_lower: la = "LA4"
                            elif "5" in filepath_lower or "eng" in filepath_lower or "read" in filepath_lower: la = "LA5"
                        elif "math" in filepath_lower or "num" in filepath_lower: la = "LA4"
                        elif "eng" in filepath_lower or "read" in filepath_lower or "lit" in filepath_lower: la = "LA5"
                        elif "health" in filepath_lower: la = "LA3"
                        elif "social" in filepath_lower: la = "LA1"
                        
                        docs_to_embed.append({
                            "id": f"doc_{len(docs_to_embed) + total_docs}",
                            "text": text,
                            "metadata": {
                                "filename": filepath,
                                "class_level": class_level,
                                "learning_area": la
                            }
                        })
                        
    if not docs_to_embed:
        print("No new documents to embed.")
        return
        
    print(f"Embedding {len(docs_to_embed)} new documents...")
    
    # Insert in batches
    documents = [d["text"] for d in docs_to_embed]
    metadatas = [d["metadata"] for d in docs_to_embed]
    ids = [d["id"] for d in docs_to_embed]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("✅ Ingestion complete.")

if __name__ == "__main__":
    ingest_nursery_papers()
