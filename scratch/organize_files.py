import os
import shutil
import re
from pathlib import Path

# Base Paths
WORKSPACE_DIR = "/Users/luke/Downloads/docs/ eduquest 2 stabler"
ORGANIZED_ROOT = os.path.join(WORKSPACE_DIR, "Organized_Curriculum")

# mess folders to organize
MESSY_FOLDERS = [
    "p1-p3 schems and notes",
    "p4- p7  schems, notes and papers",
    "the final schemes"
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
    elif re.search(r'\b(re|c\.?r\.?e|i\.?r\.?e|religious|christian|islamic)\b', filename_lower):
        subject = "Religious_Education"
    elif "luganda" in filename_lower:
        subject = "Luganda"
    elif "reading" in filename_lower or "literacy" in filename_lower or "lit" in filename_lower:
        subject = "Literacy_and_Reading"

    return level, subject

def main():
    print("Initiating Curriculum File Organization...")
    os.makedirs(ORGANIZED_ROOT, exist_ok=True)
    
    copy_count = 0
    skip_count = 0
    
    for folder in MESSY_FOLDERS:
        source_dir = os.path.join(WORKSPACE_DIR, folder)
        if not os.path.exists(source_dir):
            print(f"Skipping non-existent directory: {folder}")
            continue
            
        print(f"Scanning folder: {folder}...")
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.startswith('.') or file.lower().endswith(('.py', '.db', '.json', '.log')):
                    continue
                    
                filepath = os.path.join(root, file)
                level, subject = infer_category(file)
                
                # Determine target path:
                # Pre-primary goes into Nursery directory
                if level in ["Baby_Class", "Middle_Class", "Top_Class"]:
                    target_dir = os.path.join(ORGANIZED_ROOT, "Pre_Primary", level, subject)
                elif level.startswith("P"):
                    target_dir = os.path.join(ORGANIZED_ROOT, "Primary", level, subject)
                elif level.startswith("Senior") or level == "A-Level":
                    target_dir = os.path.join(ORGANIZED_ROOT, "Secondary", level, subject)
                else:
                    target_dir = os.path.join(ORGANIZED_ROOT, "Uncategorized_or_Combined", subject)
                    
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file)
                
                # Prevent duplicate copy
                if os.path.exists(target_path):
                    skip_count += 1
                    continue
                    
                try:
                    shutil.copy2(filepath, target_path)
                    copy_count += 1
                except Exception as e:
                    print(f"Error copying {file}: {e}")

    print("\nFile Organization Complete!")
    print(f"Total Files Safely Categorized and Mirrored: {copy_count}")
    print(f"Duplicates Skipped: {skip_count}")
    print(f"Beautiful structured mirror created at: {ORGANIZED_ROOT}")

if __name__ == "__main__":
    main()
