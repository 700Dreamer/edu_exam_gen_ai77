import os
import json
import chromadb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "extracted_syllabus_data.json")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

primary_levels = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]

print("1. Cleaning extracted_syllabus_data.json...")
if os.path.exists(INPUT_JSON):
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Filter out primary
    original_len = len(dataset)
    new_dataset = [d for d in dataset if d.get("level") not in primary_levels]
    
    with open(INPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_dataset, f, indent=4)
    print(f"Removed {original_len - len(new_dataset)} primary documents from JSON. Remaining: {len(new_dataset)}")
else:
    print("No JSON found.")

print("2. Cleaning ChromaDB...")
if os.path.exists(DB_DIR):
    try:
        client = chromadb.PersistentClient(path=DB_DIR)
        col = client.get_or_create_collection(name="exam_syllabus_collection")
        col.delete(where={"level": {"$in": primary_levels}})
        print("Successfully removed primary documents from Vector DB.")
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
else:
    print("No ChromaDB found.")
