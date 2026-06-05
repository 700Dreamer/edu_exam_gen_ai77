import os
import shutil
import re
from pathlib import Path
from sync_metadata import sync_syllabus_metadata

UNCATEGORIZED_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/Uncategorized")
DATABASE_ROOT = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database")

def analyze_level_and_class(filename, folder_name):
    filename_upper = filename.upper()
    folder_upper = folder_name.upper()
    
    # ── A-LEVEL DETECTION ──
    if any(keyword in filename_upper or keyword in folder_upper for keyword in [
        "S.5", "S5", "S.6", "S6", "SENIOR FIVE", "SENIOR SIX", "A-LEVEL", "A LEVEL", "A_LEVEL", "PRINCIPAL", "SUBSIDIARY"
    ]):
        return "3. Secondary/A_Level_S5_S6"
        
    # ── O-LEVEL DETECTION ──
    if any(keyword in filename_upper or keyword in folder_upper for keyword in [
        "S.1", "S1", "S.2", "S2", "S.3", "S3", "S.4", "S4", 
        "SENIOR ONE", "SENIOR TWO", "SENIOR THREE", "SENIOR FOUR", 
        "O-LEVEL", "O LEVEL", "O_LEVEL", "UCE"
    ]):
        return "3. Secondary/O_Level_S1_S4"
        
    if re.search(r'\b(456|535|545|553)\b', filename_upper):
        return "3. Secondary/O_Level_S1_S4"

    # ── PRIMARY DETECTION (P1 to P7) ──
    if any(keyword in filename_upper for keyword in ["P.7", "P7", "PRIMARY SEVEN", "PRIMARY 7", "PLE"]):
        return "2. Primary/P7_Upper_Primary"
    if any(keyword in filename_upper for keyword in ["P.6", "P6", "PRIMARY SIX", "PRIMARY 6"]):
        return "2. Primary/P6_Upper_Primary"
    if any(keyword in filename_upper for keyword in ["P.5", "P5", "PRIMARY FIVE", "PRIMARY 5"]):
        return "2. Primary/P5_Upper_Primary"
    if any(keyword in filename_upper for keyword in ["P.4", "P4", "PRIMARY FOUR", "PRIMARY 4"]):
        return "2. Primary/P4_Upper_Primary"
    if any(keyword in filename_upper for keyword in ["P.3", "P3", "PRIMARY THREE", "PRIMARY 3"]):
        return "2. Primary/P3_Lower_Primary"
    if any(keyword in filename_upper for keyword in ["P.2", "P2", "PRIMARY TWO", "PRIMARY 2"]):
        return "2. Primary/P2_Lower_Primary"
    if any(keyword in filename_upper for keyword in ["P.1", "P1", "PRIMARY ONE", "PRIMARY 1"]):
        return "2. Primary/P1_Lower_Primary"

    # Fallback to secondary if appropriate subject
    if folder_name in ["Agriculture", "Biology", "Chemistry", "Entrepreneurship", "Food_and_Nutrition", "Geography", "History", "Physics"]:
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

def migrate():
    if not UNCATEGORIZED_DIR.exists():
        print(f"Uncategorized directory does not exist: {UNCATEGORIZED_DIR}")
        return
        
    print("Starting file-by-file database reorganization...")
    
    files_to_move = []
    
    # 1. Collect all files to move
    for root, dirs, files in os.walk(UNCATEGORIZED_DIR):
        for file in files:
            if file.startswith("~$") or file.startswith("."):
                continue
                
            src_path = Path(root) / file
            relative_path = src_path.relative_to(UNCATEGORIZED_DIR)
            parts = relative_path.parts
            folder_name = parts[0] if len(parts) > 1 else "General"
            
            level_dest = analyze_level_and_class(file, folder_name)
            subj_dest = clean_subject_name(folder_name, file)
            
            dest_dir = DATABASE_ROOT / level_dest / subj_dest
            dest_path = dest_dir / file
            
            files_to_move.append((src_path, dest_dir, dest_path))
            
    print(f"Total files identified for migration: {len(files_to_move)}\n")
    
    # 2. Move file by file
    moved_count = 0
    for idx, (src, dest_dir, dest) in enumerate(files_to_move, 1):
        print(f"[{idx}/{len(files_to_move)}] Moving:")
        print(f"   From: {src.relative_to(DATABASE_ROOT.parent)}")
        
        # Create destination directory if not exists
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle filename collisions gracefully
        final_dest = dest
        collision_idx = 1
        while final_dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            final_dest = dest_dir / f"{stem}_{collision_idx}{suffix}"
            collision_idx += 1
            
        print(f"   To:   {final_dest.relative_to(DATABASE_ROOT.parent)}")
        
        try:
            shutil.move(str(src), str(final_dest))
            moved_count += 1
            print("   Status: SUCCESS\n")
        except Exception as e:
            print(f"   Status: FAILED ({e})\n")
            
    print(f"Successfully migrated {moved_count} of {len(files_to_move)} files.\n")
    
    # 3. Clean up empty directories under Uncategorized
    print("Cleaning up empty uncategorized folders...")
    for root, dirs, files in os.walk(UNCATEGORIZED_DIR, topdown=False):
        for d in dirs:
            dir_path = Path(root) / d
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"Removed empty folder: {dir_path.relative_to(DATABASE_ROOT.parent)}")
            except Exception:
                pass
                
    # If the Uncategorized folder itself is now empty, remove it too
    try:
        if not any(UNCATEGORIZED_DIR.iterdir()):
            UNCATEGORIZED_DIR.rmdir()
            print("Removed empty Uncategorized root directory.")
    except Exception:
        pass
        
    print("\nFile migrations completed! Initializing database synchronization...\n")
    
    # 4. Run the master sync process
    sync_syllabus_metadata()

if __name__ == "__main__":
    migrate()
