import os
import json
from pathlib import Path

BASE_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler")
DATABASE_DIR = BASE_DIR / "EduQuest_Syllabus_Database"
JSON_PATH = BASE_DIR / "extracted_syllabus_data.json"
DB_DIR = BASE_DIR / "chroma_db"

def sync_syllabus_metadata():
    print("Initializing Metadata & ChromaDB Sync...")
    
    if not JSON_PATH.exists():
        print("extracted_syllabus_data.json does not exist. Run extract_data.py first.")
        return
        
    # 1. Load the flat JSON dataset
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} records from JSON.")
    
    # 2. Build a physical directory file map
    physical_files = {}
    for root, dirs, files in os.walk(DATABASE_DIR):
        for file in files:
            if file.lower().split('.')[-1] in ['pdf', 'docx', 'doc'] and not file.startswith("."):
                physical_files[file] = os.path.join(root, file)
                
    print(f"Scanned {len(physical_files)} physical documents in target curriculum directories.")
    
    # 3. Synchronize paths and metadata in JSON
    moved_count = 0
    updated_filenames = set()
    
    for doc in dataset:
        filename = doc.get("filename")
        if filename in physical_files:
            new_path = physical_files[filename]
            old_path = doc.get("filepath", "")
            
            # Check if path changed
            if Path(new_path).resolve() != Path(old_path).resolve():
                doc["filepath"] = new_path
                moved_count += 1
                updated_filenames.add(filename)
                
            # If the file resides under Primary and Integrated_Science, update subject to Science
            if "2. Primary" in new_path and "Integrated_Science" in new_path:
                if doc.get("subject") != "Science":
                    doc["subject"] = "Science"
                    updated_filenames.add(filename)
                    
    print(f"Updated metadata/paths for {len(updated_filenames)} affected files in extracted_syllabus_data.json.")
    
    # Save the updated JSON back to disk
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4)
    print("Saved synchronized JSON dataset.")
    
    # 4. Surgical ChromaDB Cleanup
    if updated_filenames:
        print(f"Connecting to ChromaDB to prune and update {len(updated_filenames)} collections...")
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
            
            # Retrieve or create existing collection
            from chromadb.utils import embedding_functions
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model_name="text-embedding-3-small"
            )
            collection = chroma_client.get_collection(
                name="exam_syllabus_collection",
                embedding_function=openai_ef
            )
            
            # Delete outdated chunks for affected files
            print("Deleting old vector chunks for moved science files...")
            for fname in updated_filenames:
                collection.delete(where={"filename": fname})
                
            print("ChromaDB pruning completed successfully!")
            
            # 5. Trigger build_vector_db to re-embed only the missing/updated files
            print("\nTriggering build_vector_db.py to surgically re-embed changed files...")
            from build_vector_db import build_vector_db
            build_vector_db()
            
        except Exception as e:
            print(f"ChromaDB Sync Warning: {e}")
            print("Please ensure OPENAI_API_KEY is configured in your shell environment.")

if __name__ == "__main__":
    # Load env variables for OpenAI client
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val.strip("'\"")
                    
    sync_syllabus_metadata()
