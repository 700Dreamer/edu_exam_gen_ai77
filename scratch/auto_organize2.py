import os
import shutil
import re
from pathlib import Path

WORKSPACE_DIR = "/Users/luke/Downloads/docs/ eduquest 2 stabler"
DB_DIR = os.path.join(WORKSPACE_DIR, "EduQuest_Syllabus_Database")

def infer_category(filename):
    filename_lower = filename.lower()
    level = "Unknown"
    
    # ── 1. LEVEL INFERENCE ──
    # Match P1-P7, e.g., P.4, P_7, p1, p. 1
    p_match = re.search(r'\bp[._\-\s]*([1-7])\b', filename_lower)
    primary_word_match = re.search(r'primary\s*(one|two|three|four|five|six|seven|1|2|3|4|5|6|7)', filename_lower)
    
    if p_match:
        level = f"P{p_match.group(1)}"
    elif primary_word_match:
        word_to_num = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
            "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7"
        }
        level = f"P{word_to_num[primary_word_match.group(1)]}"
    elif re.search(r'\bple\b', filename_lower):
        level = "P7"
    elif re.search(r'\bbaby\b', filename_lower) or "apple class" in filename_lower or "kg i " in filename_lower or "kg 1" in filename_lower:
        level = "Baby_Class"
    elif re.search(r'\bmiddle\b', filename_lower) or "kg ii " in filename_lower or "kg 2" in filename_lower:
        level = "Middle_Class"
    elif re.search(r'\btop\b', filename_lower) or "kg iii" in filename_lower or "kg 3" in filename_lower:
        level = "Top_Class"
    elif "nursery" in filename_lower or "kg" in filename_lower or "kindergarten" in filename_lower:
        level = "Nursery_Uncategorized"
    elif re.search(r'\bs[._\-\s]*([1-6])\b', filename_lower):
        s_match = re.search(r'\bs[._\-\s]*([1-6])\b', filename_lower)
        level = f"S{s_match.group(1)}"
    elif "senior" in filename_lower:
        s_match = re.search(r'senior\s*([1-6])', filename_lower)
        if s_match:
            level = f"S{s_match.group(1)}"
        else:
            level = "Senior_Uncategorized"

    # ── 2. SUBJECT INFERENCE ──
    subject = "General"
    
    if re.search(r'\b(maths?|mathematics|mtc|numeracy|number|numbers|integers|submath)\b', filename_lower):
        subject = "Mathematics"
    elif re.search(r'\b(eng|english|grammar|comprehension|language|reading|literacy|lit|rhymes|writing|news)\b', filename_lower):
        subject = "English"
    elif re.search(r'\b(sci|scie|science|biology|physics|chemistry|bio|phy|chem)\b', filename_lower):
        subject = "Science"
    elif re.search(r'\b(sst|social\s*studies|geography|history|geog|hist)\b', filename_lower):
        subject = "Social_Studies"
    elif re.search(r'\b(re|c\.?r\.?e|i\.?r\.?e|religious|christian|islamic|health|habits)\b', filename_lower):
        if re.search(r'\bi\.?r\.?e|islamic\b', filename_lower):
            subject = "Islamic_Religious_Education"
        elif re.search(r'\bc\.?r\.?e|christian\b', filename_lower):
            subject = "Christian_Religious_Education"
        else:
            subject = "Religious_Education"
    elif "luganda" in filename_lower:
        subject = "Luganda"
    elif "french" in filename_lower:
        subject = "French"
    elif "music" in filename_lower:
        subject = "Music"
    elif "art" in filename_lower or "design" in filename_lower or "craft" in filename_lower:
        subject = "Art_and_Design"
    elif "p.e" in filename_lower or "physical education" in filename_lower:
        subject = "Physical_Education"

    return level, subject

def get_target_dir(level, subject, filename):
    filename_lower = filename.lower()
    base = "Uncategorized"
    
    # Pre-primary
    if level in ["Baby_Class", "Middle_Class", "Top_Class", "Nursery_Uncategorized"]:
        if level == "Nursery_Uncategorized":
            base = "1. Pre_Primary/Uncategorized"
        else:
            base = f"1. Pre_Primary/{level}"
            
        if subject == "Mathematics":
            subj_dir = "LA4_Mathematical_Concepts"
        elif subject == "English":
            subj_dir = "LA1_Language_and_Literacy"
        elif subject == "Science":
            subj_dir = "LA2_Environment_and_Science"
        elif subject == "Social_Studies" or "health" in filename_lower or "habits" in filename_lower:
            subj_dir = "LA5_Social_and_Health_Habits"
        elif "psy" in filename_lower or "art" in filename_lower or "draw" in filename_lower:
            subj_dir = "LA3_Psychomotor"
        else:
            subj_dir = "General"
            
        return os.path.join(base, subj_dir)
        
    # Primary
    elif level.startswith("P") and len(level) == 2:
        num = int(level[1])
        if num <= 3:
            base = f"2. Primary/{level}_Lower_Primary"
        else:
            base = f"2. Primary/{level}_Upper_Primary"
            
        if subject == "Science": subject = "Integrated_Science"
        elif subject == "English": subject = "English_Grammar"
        
        return os.path.join(base, subject)
        
    # Secondary
    elif level.startswith("S") and len(level) == 2:
        num = int(level[1])
        if num <= 4:
            base = "3. Secondary/O_Level_S1_S4"
        else:
            base = "3. Secondary/A_Level_S5_S6"
        return os.path.join(base, subject)
        
    else:
        return os.path.join("Uncategorized", subject)

def auto_organize():
    print("Scanning EduQuest_Syllabus_Database for remaining unorganized files...")
    
    all_files = []
    for root, dirs, files in os.walk(DB_DIR):
        for f in files:
            if not f.startswith(".") and f.lower().endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx')):
                all_files.append(os.path.join(root, f))
                
    moved_count = 0
    already_correct_count = 0
    
    for filepath in all_files:
        filename = os.path.basename(filepath)
        current_dir = os.path.dirname(filepath)
        
        level, subject = infer_category(filename)
        rel_target = get_target_dir(level, subject, filename)
        
        target_dir = os.path.join(DB_DIR, rel_target)
        target_path = os.path.join(target_dir, filename)
        
        if current_dir == target_dir:
            already_correct_count += 1
            continue
            
        os.makedirs(target_dir, exist_ok=True)
        
        if os.path.exists(target_path) and target_path != filepath:
            base, ext = os.path.splitext(filename)
            target_path = os.path.join(target_dir, f"{base}_copy2{ext}")
            
        print(f"Moving '{filename}' \n  from: {os.path.relpath(current_dir, DB_DIR)}\n  to:   {rel_target}\n")
        try:
            shutil.move(filepath, target_path)
            moved_count += 1
        except Exception as e:
            print(f"Error moving {filename}: {e}")
            
    print(f"\nSecond Pass Done! Moved {moved_count} files. {already_correct_count} files were already correct.")
    
    # Clean up empty directories thoroughly
    for _ in range(3):
        for root, dirs, files in os.walk(DB_DIR, topdown=False):
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except:
                    pass

if __name__ == "__main__":
    auto_organize()
