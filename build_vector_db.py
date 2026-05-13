import os
import json
from tqdm import tqdm

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Warning: chromadb not found. Install with: pip install chromadb openai")
    chromadb = None

# 1. Secure Environment Loader
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
INPUT_JSON = os.path.join(BASE_DIR, "extracted_syllabus_data.json")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

def chunk_text(text, chunk_size=1500, overlap=200):
    """
    Splits the text into smaller chunks with overlap to preserve context.
    It attempts to break at double-newlines (paragraphs), single newlines, or spaces.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        
        # If we're not at the very end, try to find a clean break point
        if end < len(text):
            # Try splitting by double newline first
            break_point = text.rfind('\n\n', start, end)
            if break_point == -1 or break_point <= start:
                # Fallback to single newline
                break_point = text.rfind('\n', start, end)
            if break_point == -1 or break_point <= start:
                # Fallback to space
                break_point = text.rfind(' ', start, end)
            
            # If a clean break point was found, adjust the end
            if break_point != -1 and break_point > start:
                end = break_point

        chunks.append(text[start:end].strip())
        # Step back by overlap to ensure context is preserved between chunks
        start = end - overlap if end < len(text) else len(text)
        
    # Remove any empty chunks
    return [c for c in chunks if c]

def build_vector_db():
    print(f"Loading data from {INPUT_JSON}...")
    if not os.path.exists(INPUT_JSON):
        print("Data file not found. Have you completed Step 1 (extract_data.py)?")
        return

    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    if not chromadb:
        return

    print("Initializing ChromaDB and OpenAI Embeddings...")
    chroma_client = chromadb.PersistentClient(path=DB_DIR)
    
    # We use OpenAI's text-embedding-3-small (much cheaper and highly efficient)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )

    # 3. Incremental Database Updates (Check for Existing Documents)
    collection = chroma_client.get_or_create_collection(
        name="exam_syllabus_collection",
        embedding_function=openai_ef
    )
    print("Connected to existing ChromaDB collection.")
    
    # Fetch existing metadatas to track what we have already embedded (Paginated to avoid SQLite limits)
    existing_filenames = set()
    total_docs = collection.count()
    batch_size = 10000
    
    if total_docs > 0:
        print(f"Fetching {total_docs} existing metadata records to prevent duplicates...")
        for offset in range(0, total_docs, batch_size):
            try:
                batch_data = collection.get(limit=batch_size, offset=offset, include=["metadatas"])
                if batch_data and batch_data.get("metadatas"):
                    for m in batch_data["metadatas"]:
                        if m and "filename" in m:
                            existing_filenames.add(m["filename"])
            except Exception as e:
                print(f"Warning skipping batch {offset}: {e}")
                
    print(f"Found {len(existing_filenames)} unique documents currently in the Vector DB.")

    documents = []
    metadatas = []
    ids = []

    print("Chunking documents...")
    chunk_id_counter = total_docs  # Continue IDs from where we left off

    new_documents_added = 0
    for doc in tqdm(dataset, desc="Processing Document Chunks"):
        if "content" not in doc or not doc["content"]:
            continue
            
        filename = str(doc.get("filename", "Unknown"))
        # Skip if already in the Vector Database! (Saves API Costs & Time)
        if filename in existing_filenames:
            continue
            
        new_documents_added += 1
        chunks = chunk_text(doc["content"])
        
        for chunk in chunks:
            safe_metadata = {
                "filename": filename,
                "level": str(doc.get("level", "Unknown")),
                "subject": str(doc.get("subject", "Unknown")),
                "term": str(doc.get("term", "Unknown")),
                "doc_type": str(doc.get("doc_type", "Unknown"))
            }

            documents.append(chunk)
            metadatas.append(safe_metadata)
            ids.append(f"chunk_{chunk_id_counter}")
            chunk_id_counter += 1

    if new_documents_added == 0:
        print("\nNo new documents to embed. Database is fully up-to-date!")
        return

    print(f"\nPushing {len(documents)} chunks to Vector Database (Calling OpenAI API)...")
    
    # Upload in batches of 100 to avoid memory / API limits
    batch_size = 100
    for i in tqdm(range(0, len(documents), batch_size), desc="Embedding & Storing to ChromaDB"):
        end = min(i + batch_size, len(documents))
        try:
            collection.add(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
        except Exception as e:
            print(f"Error uploading batch {i}-{end}: {e}")

    print(f"\n✅ Successfully built Vector Database at '{DB_DIR}'!")

if __name__ == "__main__":
    build_vector_db()
