import os
import re

src_dir = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src"

ignore_dirs = {".git", ".next", "node_modules", "static", "chroma_db", "generated papers", "frontend"}

for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        if file.endswith((".py", ".json", ".yaml")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    # Check for role checks or user-level student/teacher
                    if 'role' in line.lower() and ('student' in line.lower() or 'teacher' in line.lower()):
                        print(f"File: {path} | Line {i+1}: {line.strip()}")
            except Exception as e:
                pass
