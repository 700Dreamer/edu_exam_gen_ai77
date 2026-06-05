import os
import shutil
import re
import subprocess
from pathlib import Path

# Base Workspace Paths
WORKSPACE_DIR = "/Users/luke/Downloads/docs/ eduquest 2 stabler"
MASTER_DATABASE = os.path.join(WORKSPACE_DIR, "EduQuest_Curriculum_Database")

# Folders to consolidate
SOURCE_FOLDERS = [
    "p1-p3 schems and notes",
    "p4- p7  schems, notes and papers",
    "the final schemes",
    "ALL CLASSES",
    "NURSERY ITEMS"
]

def infer_category(filename):
    filename_lower = filename.lower()
    
    # ── 1. LEVEL INFERENCE ──
    level = "Other_Levels"
    
    # Match standard P1-P7
    p_match = re.search(r'\bp\.?\s*([1-7])\b', filename_lower)
    primary_word_match = re.search(r'primary\s*(one|two|three|four|five|six|seven|1|2|3|4|5|6|7)', filename_lower)
    
    if p_match:
        level = f"P{p_match.group(1)}"
    elif primary_word_match:
        word_to_num = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
            "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7"
        }
        level = f"P{word_to_num[primary_word_match.group(1)]}"
    elif "baby" in filename_lower:
        level = "Baby_Class"
    elif "middle" in filename_lower:
        level = "Middle_Class"
    elif "top" in filename_lower:
        level = "Top_Class"
    elif re.search(r'\bs\.?\s*([1-6])\b', filename_lower) or "senior" in filename_lower:
        s_match = re.search(r'senior\s*([1-6])', filename_lower)
        if s_match:
            level = f"Senior_S{s_match.group(1)}"
        else:
            level = "Senior"
    elif "a-level" in filename_lower or "a level" in filename_lower:
        level = "A-Level"

    # ── 2. SUBJECT INFERENCE ──
    subject = "General_and_Other"
    
    if re.search(r'\b(maths?|mathematics|mtc)\b', filename_lower):
        subject = "Mathematics"
    elif re.search(r'\b(eng|english|grammar|comprehension)\b', filename_lower):
        subject = "English"
    elif re.search(r'\b(sci|scie|science|biology|physics|chemistry|bio|phy|chem|sound)\b', filename_lower):
        subject = "Science"
    elif re.search(r'\b(sst|social\s*studies|geography|history|geog|hist|climate|ethnic)\b', filename_lower):
        subject = "Social_Studies"
    elif re.search(r'\b(re|c\.?r\.?re|i\.?r\.?e|religious|christian|islamic)\b', filename_lower):
        subject = "Religious_Education"
    elif "luganda" in filename_lower:
        subject = "Luganda"
    elif "reading" in filename_lower or "literacy" in filename_lower or "lit" in filename_lower:
        subject = "Literacy_and_Reading"

    return level, subject

def main():
    print("Initiating Master Workspace Physical Reorganization...")
    os.makedirs(MASTER_DATABASE, exist_ok=True)
    
    copy_count = 0
    skip_count = 0
    
    for folder in SOURCE_FOLDERS:
        source_path = os.path.join(WORKSPACE_DIR, folder)
        if not os.path.exists(source_path):
            print(f"Source folder not found, skipping: {folder}")
            continue
            
        print(f"Crawling loose directory: '{folder}'...")
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file.startswith('.') or file.lower().endswith(('.py', '.db', '.json', '.log')):
                    continue
                    
                filepath = os.path.join(root, file)
                level, subject = infer_category(file)
                
                # Direct folder destinations
                if level in ["Baby_Class", "Middle_Class", "Top_Class"]:
                    target_dir = os.path.join(MASTER_DATABASE, "Pre_Primary", level, subject)
                elif level.startswith("P"):
                    target_dir = os.path.join(MASTER_DATABASE, "Primary", level, subject)
                elif level.startswith("Senior") or level == "A-Level":
                    target_dir = os.path.join(MASTER_DATABASE, "Secondary", level, subject)
                else:
                    target_dir = os.path.join(MASTER_DATABASE, "Uncategorized_or_Combined", subject)
                    
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file)
                
                if os.path.exists(target_path):
                    skip_count += 1
                    continue
                    
                try:
                    shutil.copy2(filepath, target_path)
                    copy_count += 1
                except Exception as e:
                    print(f"Error copying {file}: {e}")

    print(f"\nPhysical organization complete. Mapped {copy_count} unique files.")

    # ── 3. CLEAN UP MESSY DIRECTORIES ──
    print("\nPhysically cleaning up loose original directories...")
    cleanup_targets = SOURCE_FOLDERS + ["Organized_Curriculum"]
    for target in cleanup_targets:
        target_path = os.path.join(WORKSPACE_DIR, target)
        if os.path.exists(target_path):
            print(f"Deleting messy folder: '{target}'...")
            try:
                shutil.rmtree(target_path)
            except Exception as e:
                print(f"Could not remove folder {target}: {e}")

    # ── 4. REBUILD INDEX PAYLOADS AND DB ──
    print("\nRe-indexing master database file path configurations...")
    
    # 4.1 Update extract_data.py to output from the new MASTER_DATABASE
    extract_script = os.path.join(WORKSPACE_DIR, "extract_data.py")
    if os.path.exists(extract_script):
        print("Executing clean data extraction...")
        # Delete old JSON so we extract fresh with clean database paths
        old_json = os.path.join(WORKSPACE_DIR, "extracted_syllabus_data.json")
        if os.path.exists(old_json):
            os.remove(old_json)
        
        subprocess.run([os.path.join(WORKSPACE_DIR, ".venv/bin/python3"), extract_script], check=True)

    # 4.2 Rebuild Chroma DB collection
    print("\nClearing old database records and rebuilding vector db...")
    chroma_db_dir = os.path.join(WORKSPACE_DIR, "chroma_db")
    if os.path.exists(chroma_db_dir):
        print("Removing old Chroma database collection indices...")
        try:
            shutil.rmtree(chroma_db_dir)
        except Exception as e:
            print(f"Could not clear Chroma DB: {e}")
            
    build_db_script = os.path.join(WORKSPACE_DIR, "build_vector_db.py")
    if os.path.exists(build_db_script):
        print("Executing vector db index rebuild...")
        subprocess.run([os.path.join(WORKSPACE_DIR, ".venv/bin/python3"), build_db_script], check=True)

    print("\n=============================================")
    print("WORKSPACE IMMACULATELY ORGANIZED AND INDEXED!")
    print("=============================================")

if __name__ == "__main__":
    main()
