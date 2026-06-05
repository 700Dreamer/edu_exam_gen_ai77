import os
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/1. Pre_Primary")

def align_folders_to_ui():
    print("Aligning Nursery folders to UI Learning Area mapping...")
    
    for grade_dir in sorted(BASE_DIR.iterdir()):
        if grade_dir.is_dir():
            la1_dir = grade_dir / "LA1_Social_and_Health_Habits"
            la5_dir = grade_dir / "LA5_Language_and_Literacy"
            
            # Temporary folders to avoid collision
            temp_la1 = grade_dir / "TEMP_LA1"
            temp_la5 = grade_dir / "TEMP_LA5"
            
            # 1. Rename to temp
            if la1_dir.exists():
                shutil.move(str(la1_dir), str(temp_la1))
            if la5_dir.exists():
                shutil.move(str(la5_dir), str(temp_la5))
                
            # 2. Rename to target mapped locations
            if temp_la1.exists():
                shutil.move(str(temp_la1), str(grade_dir / "LA5_Social_and_Health_Habits"))
                print(f"  [{grade_dir.name}] Renamed: LA1_Social_and_Health_Habits -> LA5_Social_and_Health_Habits")
            if temp_la5.exists():
                shutil.move(str(temp_la5), str(grade_dir / "LA1_Language_and_Literacy"))
                print(f"  [{grade_dir.name}] Renamed: LA5_Language_and_Literacy -> LA1_Language_and_Literacy")
                
    print("\nAlignment Completed successfully!")

if __name__ == "__main__":
    align_folders_to_ui()
