import os
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/1. Pre_Primary")

def reorganize_nursery_classes():
    print("Starting programmatical Nursery (ECD) reorganization...")
    
    total_moved = 0
    folders_cleaned = 0
    
    for grade_dir in sorted(BASE_DIR.iterdir()):
        if grade_dir.is_dir() and ("Class" in grade_dir.name or grade_dir.name.startswith("Baby") or grade_dir.name.startswith("Middle") or grade_dir.name.startswith("Top")):
            print(f"\nProcessing Nursery level: {grade_dir.name}")
            
            # 1. Create target Learning Area (LA) directories
            la1_dir = grade_dir / "LA1_Social_and_Health_Habits"
            la2_dir = grade_dir / "LA2_Environment_and_Science"
            la3_dir = grade_dir / "LA3_Creative_and_Psychomotor_Skills"
            la4_dir = grade_dir / "LA4_Mathematical_Concepts"
            la5_dir = grade_dir / "LA5_Language_and_Literacy"
            
            for d in [la1_dir, la2_dir, la3_dir, la4_dir, la5_dir]:
                d.mkdir(exist_ok=True)
                
            # 2. Iterate through old folders and classify files
            for old_folder in sorted(grade_dir.iterdir()):
                # Only look at old subdirectories that are NOT our new LA folders
                if old_folder.is_dir() and not old_folder.name.startswith("LA"):
                    print(f"  * Reading from old directory: {old_folder.name}")
                    
                    for file_path in old_folder.iterdir():
                        if file_path.is_file() and not file_path.name.startswith("."):
                            filename_lower = file_path.name.lower()
                            
                            # Default destination based on old folder name
                            dest_dir = la1_dir  # Fallback
                            
                            if old_folder.name == "Mathematics":
                                dest_dir = la4_dir
                            elif old_folder.name in ["English_Grammar", "Literacy_and_Reading"]:
                                # Check for specific overrides in filenames
                                if "social" in filename_lower or "relation" in filename_lower:
                                    dest_dir = la1_dir
                                elif "science" in filename_lower or "environment" in filename_lower:
                                    dest_dir = la2_dir
                                elif "math" in filename_lower or "concept" in filename_lower or "number" in filename_lower:
                                    dest_dir = la4_dir
                                else:
                                    dest_dir = la5_dir
                            elif old_folder.name in ["Christian_Religious_Education", "Social_Studies"]:
                                dest_dir = la1_dir
                            elif old_folder.name == "Integrated_Science":
                                dest_dir = la2_dir
                            elif old_folder.name == "General":
                                if "social" in filename_lower or "habit" in filename_lower or "hygiene" in filename_lower or "religion" in filename_lower or "cre" in filename_lower:
                                    dest_dir = la1_dir
                                elif "science" in filename_lower or "environment" in filename_lower or "nature" in filename_lower or "animal" in filename_lower:
                                    dest_dir = la2_dir
                                elif "math" in filename_lower or "concept" in filename_lower or "number" in filename_lower or "count" in filename_lower:
                                    dest_dir = la4_dir
                                elif "english" in filename_lower or "read" in filename_lower or "grammar" in filename_lower or "lit" in filename_lower:
                                    dest_dir = la5_dir
                                elif "art" in filename_lower or "creative" in filename_lower or "play" in filename_lower or "draw" in filename_lower:
                                    dest_dir = la3_dir
                                else:
                                    dest_dir = la1_dir # default general
                                    
                            dest_path = dest_dir / file_path.name
                            if dest_path.exists():
                                base, ext = os.path.splitext(file_path.name)
                                dest_path = dest_dir / f"{base}_moved{ext}"
                                
                            print(f"    -> Moving: '{file_path.name}' -> '{dest_dir.name}/{dest_path.name}'")
                            shutil.move(str(file_path), str(dest_path))
                            total_moved += 1
                            
                    # Clean up hidden files
                    for file_path in old_folder.iterdir():
                        if file_path.is_file():
                            file_path.unlink()
                            
                    # Delete the old folder
                    print(f"    -> Deleting empty old directory: {old_folder.relative_to(BASE_DIR.parent)}")
                    old_folder.rmdir()
                    folders_cleaned += 1
                    
            # 3. Clean up any empty LA folders (in case some LAs got 0 files)
            for d in [la1_dir, la2_dir, la3_dir, la4_dir, la5_dir]:
                if d.exists() and len(list(d.iterdir())) == 0:
                    d.rmdir()
                    
    print("\n" + "="*45)
    print(f"Nursery Reorganization Completed successfully!")
    print(f"Total Nursery files mapped to LAs: {total_moved}")
    print(f"Total old directories pruned: {folders_cleaned}")
    print("="*45)

if __name__ == "__main__":
    reorganize_nursery_classes()
