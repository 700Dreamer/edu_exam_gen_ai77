import os
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/2. Primary")

def reorganize_primary_science():
    print("Starting programmatical database reorganization...")
    
    total_moved = 0
    folders_cleaned = 0
    
    for grade_dir in sorted(BASE_DIR.iterdir()):
        if grade_dir.is_dir() and grade_dir.name.startswith("P"):
            chemistry_dir = grade_dir / "Chemistry"
            integrated_science_dir = grade_dir / "Integrated_Science"
            
            if chemistry_dir.exists() and chemistry_dir.is_dir():
                print(f"\nProcessing {grade_dir.name}:")
                
                # Ensure Integrated_Science folder exists
                integrated_science_dir.mkdir(exist_ok=True)
                
                # Move all files from Chemistry to Integrated_Science
                files_moved = 0
                for file_path in chemistry_dir.iterdir():
                    if file_path.is_file() and not file_path.name.startswith("."):
                        dest_path = integrated_science_dir / file_path.name
                        
                        # Handle collision if file already exists in dest
                        if dest_path.exists():
                            # Append a suffix to differentiate
                            base, ext = os.path.splitext(file_path.name)
                            dest_path = integrated_science_dir / f"{base}_moved{ext}"
                            
                        print(f"  -> Moving: '{file_path.name}' -> 'Integrated_Science/{dest_path.name}'")
                        shutil.move(str(file_path), str(dest_path))
                        files_moved += 1
                        total_moved += 1
                        
                # Clean up any leftover hidden files in Chemistry
                for file_path in chemistry_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        
                # Delete the now empty Chemistry directory
                print(f"  -> Deleting empty directory: {chemistry_dir.relative_to(BASE_DIR.parent)}")
                chemistry_dir.rmdir()
                folders_cleaned += 1
                
    print("\n" + "="*45)
    print(f"Reorganization Completed successfully!")
    print(f"Total Science files merged: {total_moved}")
    print(f"Total Chemistry folders cleaned: {folders_cleaned}")
    print("="*45)

if __name__ == "__main__":
    reorganize_primary_science()
