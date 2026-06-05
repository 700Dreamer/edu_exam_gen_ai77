import os
import shutil
import re
import subprocess
from pathlib import Path

# Workspace Root Paths
WORKSPACE_DIR = "/Users/luke/Downloads/docs/ eduquest 2 stabler"
SOURCE_DATABASE = os.path.join(WORKSPACE_DIR, "EduQuest_Curriculum_Database")
LOGICAL_DATABASE = os.path.join(WORKSPACE_DIR, "EduQuest_Syllabus_Database")

def parse_logical_destination(filename):
    filename_lower = filename.lower()
    
    # Default fallback folders
    level_path = "Uncategorized"
    subject_folder = "General"

    # ── 1. Nursery & Pre-Primary ──
    if "baby" in filename_lower:
        level_path = "1. Pre_Primary/Baby_Class"
    elif "middle" in filename_lower:
        level_path = "1. Pre_Primary/Middle_Class"
    elif "top" in filename_lower:
        level_path = "1. Pre_Primary/Top_Class"
        
    # ── 2. Primary Lower (P1 - P3) ──
    elif re.search(r'\bp\.?\s*1\b', filename_lower) or "primary one" in filename_lower or "p.i " in filename_lower:
        level_path = "2. Primary/P1_Lower_Primary"
    elif re.search(r'\bp\.?\s*2\b', filename_lower) or "primary two" in filename_lower:
        level_path = "2. Primary/P2_Lower_Primary"
    elif re.search(r'\bp\.?\s*3\b', filename_lower) or "primary three" in filename_lower:
        level_path = "2. Primary/P3_Lower_Primary"
        
    # ── 3. Primary Upper (P4 - P7) ──
    elif re.search(r'\bp\.?\s*4\b', filename_lower) or "primary four" in filename_lower:
        level_path = "2. Primary/P4_Upper_Primary"
    elif re.search(r'\bp\.?\s*5\b', filename_lower) or "primary five" in filename_lower:
        level_path = "2. Primary/P5_Upper_Primary"
    elif re.search(r'\bp\.?\s*6\b', filename_lower) or "primary six" in filename_lower:
        level_path = "2. Primary/P6_Upper_Primary"
    elif re.search(r'\bp\.?\s*7\b', filename_lower) or "primary seven" in filename_lower:
        level_path = "2. Primary/P7_Upper_Primary"
        
    # ── 4. Secondary O-Level (S1 - S4) ──
    elif re.search(r'\bs\.?\s*1\b', filename_lower) or "senior one" in filename_lower:
        level_path = "3. Secondary/O_Level_S1_S4/S1"
    elif re.search(r'\bs\.?\s*2\b', filename_lower) or "senior two" in filename_lower:
        level_path = "3. Secondary/O_Level_S1_S4/S2"
    elif re.search(r'\bs\.?\s*3\b', filename_lower) or "senior three" in filename_lower:
        level_path = "3. Secondary/O_Level_S1_S4/S3"
    elif re.search(r'\bs\.?\s*4\b', filename_lower) or "senior four" in filename_lower:
        level_path = "3. Secondary/O_Level_S1_S4/S4"
        
    # ── 5. Secondary A-Level (S5 - S6) ──
    elif re.search(r'\bs\.?\s*5\b', filename_lower) or "senior five" in filename_lower:
        level_path = "3. Secondary/A_Level_S5_S6/S5"
    elif re.search(r'\bs\.?\s*6\b', filename_lower) or "senior six" in filename_lower:
        level_path = "3. Secondary/A_Level_S5_S6/S6"
    elif "a-level" in filename_lower or "a level" in filename_lower:
        level_path = "3. Secondary/A_Level_S5_S6"

    # ── Subject Routing ──
    if re.search(r'\b(maths?|mathematics|mtc|algebra|geometry|integers|geometric|submath|sub-math|principle mathematics)\b', filename_lower):
        if "principle" in filename_lower:
            subject_folder = "Principal_Mathematics"
        elif "sub" in filename_lower:
            subject_folder = "Subsidiary_Mathematics"
        else:
            subject_folder = "Mathematics"
    elif re.search(r'\b(eng|english|grammar|comprehension|composition)\b', filename_lower):
        subject_folder = "English_Grammar"
    elif re.search(r'\b(sci|scie|science|biology|physics|chemistry|bio|phy|chem|sound|energy|sound)\b', filename_lower):
        if "physics" in filename_lower or "phy" in filename_lower: subject_folder = "Physics"
        elif "chemistry" in filename_lower or "chem" in filename_lower: subject_folder = "Chemistry"
        elif "biology" in filename_lower or "bio" in filename_lower: subject_folder = "Biology"
        else: subject_folder = "Integrated_Science"
    elif re.search(r'\b(sst|social\s*studies|geography|history|geog|hist|climate|ethnic|settlement|independence)\b', filename_lower):
        if "geography" in filename_lower or "geog" in filename_lower: subject_folder = "Geography"
        elif "history" in filename_lower or "hist" in filename_lower: subject_folder = "History"
        else: subject_folder = "Social_Studies"
    elif re.search(r'\b(re|c\.?r\.?e|i\.?r\.?e|religious|christian|islamic|divinity)\b', filename_lower):
        if "ire" in filename_lower or "islamic" in filename_lower: subject_folder = "Islamic_Religious_Education"
        elif "cre" in filename_lower or "christian" in filename_lower or "divinity" in filename_lower: subject_folder = "Christian_Religious_Education"
        else: subject_folder = "Religious_Education"
    elif "luganda" in filename_lower:
        subject_folder = "Luganda"
    elif "reading" in filename_lower or "literacy" in filename_lower or "lit" in filename_lower:
        subject_folder = "Literacy_and_Reading"
    elif "ict" in filename_lower or "computer" in filename_lower:
        subject_folder = "ICT_and_Computer_Studies"
    elif "food" in filename_lower or "nutrition" in filename_lower:
        subject_folder = "Food_and_Nutrition"
    elif "general-paper" in filename_lower or "general paper" in filename_lower:
        subject_folder = "General_Paper"
    elif "entrepreneurship" in filename_lower or "business" in filename_lower:
        subject_folder = "Entrepreneurship"
    elif "agriculture" in filename_lower:
        subject_folder = "Agriculture"

    return level_path, subject_folder

def main():
    print("Initiating Highly Logical Curriculum Physical Organization...")
    os.makedirs(LOGICAL_DATABASE, exist_ok=True)
    
    move_count = 0
    skip_count = 0
    
    if not os.path.exists(SOURCE_DATABASE):
        print(f"Error: Source directory {SOURCE_DATABASE} does not exist!")
        return
        
    # Crawl through current EduQuest_Curriculum_Database files
    for root, dirs, files in os.walk(SOURCE_DATABASE):
        for file in files:
            if file.startswith('.') or file.lower().endswith(('.py', '.db', '.json', '.log')):
                continue
                
            filepath = os.path.join(root, file)
            level_path, subject_folder = parse_logical_destination(file)
            
            target_dir = os.path.join(LOGICAL_DATABASE, level_path, subject_folder)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, file)
            
            if os.path.exists(target_path):
                skip_count += 1
                continue
                
            try:
                shutil.copy2(filepath, target_path)
                move_count += 1
            except Exception as e:
                print(f"Error copying {file}: {e}")

    print(f"\nLogical organization complete. Categorized {move_count} files into structured hierarchy.")

    # ── Clean up intermediate consolidated folder ──
    if os.path.exists(SOURCE_DATABASE):
        print(f"Cleaning up consolidated directory: {SOURCE_DATABASE}...")
        try:
            shutil.rmtree(SOURCE_DATABASE)
        except Exception as e:
            print(f"Could not remove source database: {e}")

    # ── Update extract_data.py scan path to new LOGICAL_DATABASE ──
    extract_script = os.path.join(WORKSPACE_DIR, "extract_data.py")
    if os.path.exists(extract_script):
        print("\nUpdating extract_data.py target to the new EduQuest_Syllabus_Database...")
        with open(extract_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace scanning folder target
        updated_content = content.replace("EduQuest_Curriculum_Database", "EduQuest_Syllabus_Database")
        with open(extract_script, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        print("Executing clean data extraction...")
        old_json = os.path.join(WORKSPACE_DIR, "extracted_syllabus_data.json")
        if os.path.exists(old_json):
            os.remove(old_json)
        
        subprocess.run([os.path.join(WORKSPACE_DIR, ".venv/bin/python3"), extract_script], check=True)

    # ── Rebuild Chroma database collection ──
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
    print("WORKSPACE LOGICALLY ORGANIZED AND INDEXED!")
    print("=============================================")

if __name__ == "__main__":
    main()
