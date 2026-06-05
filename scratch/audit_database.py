import os
import re

UNCATEGORIZED_DIR = "/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/Uncategorized"
DATABASE_ROOT = "/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database"

def analyze_level_and_class(filename, folder_name):
    filename_upper = filename.upper()
    folder_upper = folder_name.upper()
    
    # ── A-LEVEL DETECTION ──
    if any(keyword in filename_upper or keyword in folder_upper for keyword in [
        "S.5", "S5", "S.6", "S6", "SENIOR FIVE", "SENIOR SIX", "A-LEVEL", "A LEVEL", "A_LEVEL", "PRINCIPAL", "SUBSIDIARY"
    ]):
        return "3. Secondary/A_Level_S5_S6"
        
    # ── O-LEVEL DETECTION ──
    # Senior 1 to Senior 4 (S.1, S1, S.2, S2, S.3, S3, S.4, S4, Senior One, Senior Two, Senior Three, Senior Four, O-Level, O Level)
    if any(keyword in filename_upper or keyword in folder_upper for keyword in [
        "S.1", "S1", "S.2", "S2", "S.3", "S3", "S.4", "S4", 
        "SENIOR ONE", "SENIOR TWO", "SENIOR THREE", "SENIOR FOUR", 
        "O-LEVEL", "O LEVEL", "O_LEVEL", "UCE"
    ]):
        return "3. Secondary/O_Level_S1_S4"
        
    # Check for O-Level code patterns (e.g., "553" for Biology, "456" for Math, "545" for Chemistry, "535" for Physics)
    if re.search(r'\b(456|535|545|553)\b', filename_upper):
        return "3. Secondary/O_Level_S1_S4"

    # ── PRIMARY DETECTION (P1 to P7) ──
    # Check for Primary 7 / P.7 / P7 / PLE
    if any(keyword in filename_upper for keyword in ["P.7", "P7", "PRIMARY SEVEN", "PRIMARY 7", "PLE"]):
        return "2. Primary/P7_Upper_Primary"
    # Check for Primary 6 / P.6 / P6
    if any(keyword in filename_upper for keyword in ["P.6", "P6", "PRIMARY SIX", "PRIMARY 6"]):
        return "2. Primary/P6_Upper_Primary"
    # Check for Primary 5 / P.5 / P5
    if any(keyword in filename_upper for keyword in ["P.5", "P5", "PRIMARY FIVE", "PRIMARY 5"]):
        return "2. Primary/P5_Upper_Primary"
    # Check for Primary 4 / P.4 / P4
    if any(keyword in filename_upper for keyword in ["P.4", "P4", "PRIMARY FOUR", "PRIMARY 4"]):
        return "2. Primary/P4_Upper_Primary"
    # Check for Primary 3 / P.3 / P3
    if any(keyword in filename_upper for keyword in ["P.3", "P3", "PRIMARY THREE", "PRIMARY 3"]):
        return "2. Primary/P3_Lower_Primary"
    # Check for Primary 2 / P.2 / P2
    if any(keyword in filename_upper for keyword in ["P.2", "P2", "PRIMARY TWO", "PRIMARY 2"]):
        return "2. Primary/P2_Lower_Primary"
    # Check for Primary 1 / P.1 / P1
    if any(keyword in filename_upper for keyword in ["P.1", "P1", "PRIMARY ONE", "PRIMARY 1"]):
        return "2. Primary/P1_Lower_Primary"

    # Fallback to general secondary if it contains secondary topics (e.g. Agriculture, Biology, Chemistry, Entrepreneurship, Food & Nutrition, Geography, History, ICT, Physics)
    if folder_name in ["Agriculture", "Biology", "Chemistry", "Entrepreneurship", "Food_and_Nutrition", "Geography", "History", "Physics"]:
        # Default O-Level if not specified, since most syllabus files are O-Level
        return "3. Secondary/O_Level_S1_S4"
        
    return "2. Primary/Uncategorized_Primary"

def clean_subject_name(folder_name, filename):
    folder_upper = folder_name.upper()
    filename_upper = filename.upper()
    
    if "MATH" in folder_upper or "MATH" in filename_upper or "MTC" in folder_upper or "MTC" in filename_upper:
        return "Mathematics"
    elif "ENG" in folder_upper or "ENG" in filename_upper or "GRAMMAR" in folder_upper or "READING" in folder_upper:
        return "English"
    elif "SCI" in folder_upper or "SCI" in filename_upper:
        return "Integrated_Science"
    elif "SST" in folder_upper or "SST" in filename_upper or "SOCIAL" in folder_upper:
        return "Social_Studies"
    elif "CRE" in folder_upper or "CRE" in filename_upper or "CHRISTIAN" in folder_upper or "RELIGIOUS" in folder_upper:
        return "Christian_Religious_Education"
    elif "IRE" in folder_upper or "IRE" in filename_upper or "ISLAMIC" in folder_upper:
        return "Islamic_Religious_Education"
    elif "CHEM" in folder_upper or "CHEM" in filename_upper:
        return "Chemistry"
    elif "PHYS" in folder_upper or "PHYS" in filename_upper:
        return "Physics"
    elif "BIOL" in folder_upper or "BIOL" in filename_upper:
        return "Biology"
    elif "HIST" in folder_upper or "HIST" in filename_upper:
        return "History"
    elif "GEOG" in folder_upper or "GEOG" in filename_upper:
        return "Geography"
    elif "AGRIC" in folder_upper or "AGRIC" in filename_upper:
        return "Agriculture"
    elif "ENTR" in folder_upper or "ENTR" in filename_upper:
        return "Entrepreneurship"
    elif "FOOD" in folder_upper or "FOOD" in filename_upper or "NUTRITION" in folder_upper:
        return "Food_and_Nutrition"
    elif "ICT" in folder_upper or "ICT" in filename_upper or "COMP" in folder_upper or "COMP" in filename_upper:
        return "ICT_and_Computer_Studies"
        
    return folder_name

def audit():
    if not os.path.exists(UNCATEGORIZED_DIR):
        print(f"Uncategorized folder not found at: {UNCATEGORIZED_DIR}")
        return
        
    print("Auditing mixed files in Uncategorized...")
    proposal = {}
    
    for root, dirs, files in os.walk(UNCATEGORIZED_DIR):
        for file in files:
            if file.startswith("~$"): # skip word lock files
                continue
                
            relative_path = os.path.relpath(os.path.join(root, file), UNCATEGORIZED_DIR)
            parts = relative_path.split(os.sep)
            folder_name = parts[0] if len(parts) > 1 else "General"
            
            src_path = os.path.join(root, file)
            level_dest = analyze_level_and_class(file, folder_name)
            subj_dest = clean_subject_name(folder_name, file)
            
            dest_rel = os.path.join(level_dest, subj_dest, file)
            dest_abs = os.path.join(DATABASE_ROOT, dest_rel)
            
            if level_dest not in proposal:
                proposal[level_dest] = {}
            if subj_dest not in proposal[level_dest]:
                proposal[level_dest][subj_dest] = []
                
            proposal[level_dest][subj_dest].append({
                "file": file,
                "src": src_path,
                "dest": dest_abs,
                "current_folder": folder_name
            })
            
    # Output statistics
    print("\nPROPOSED MOVEMENT BLUEPRINT:\n")
    for level, subjs in sorted(proposal.items()):
        print(f"=== LEVEL: {level} ===")
        for subj, items in sorted(subjs.items()):
            print(f"  Subject: {subj} ({len(items)} files)")
            # Print first 3 files as sample
            for item in items[:4]:
                print(f"    - From: Uncategorized/{item['current_folder']} -> To: {level}/{subj}/{item['file']}")
            if len(items) > 4:
                print(f"    - ... and {len(items)-4} more files")
        print()

if __name__ == "__main__":
    audit()
