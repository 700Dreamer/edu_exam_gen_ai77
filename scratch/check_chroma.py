import chromadb
import os

BASE_DIR = "/Users/luke/Downloads/docs/Filemail.com - eduquest"
DB_DIR = os.path.join(BASE_DIR, "chroma_db")

client = chromadb.PersistentClient(path=DB_DIR)
col = client.get_or_create_collection(name="exam_syllabus_collection")

results = col.get(include=["metadatas"], limit=100)
metas = results["metadatas"] or []

subjects = set()
levels = set()

for m in metas:
    subjects.add(m.get("subject"))
    levels.add(m.get("level"))

print(f"Total Chunks: {col.count()}")
print(f"Sample Subjects: {list(subjects)}")
print(f"Sample Levels: {list(levels)}")
