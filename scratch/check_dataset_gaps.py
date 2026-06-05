import os
from pathlib import Path

BASE_DIR = Path("/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database")

def audit_curriculum():
    report = []
    
    # 1. Pre-Primary Audit
    pre_primary_path = BASE_DIR / "1. Pre_Primary"
    report.append("### 1. Pre-Primary (Nursery) Data Distribution")
    if pre_primary_path.exists():
        for item in sorted(pre_primary_path.iterdir()):
            if item.is_dir():
                # Count files recursively
                files = list(item.glob("**/*"))
                file_count = sum(1 for f in files if f.is_file() and not f.name.startswith("."))
                subjects = sorted(list(set(f.parent.name for f in files if f.is_file() and not f.name.startswith("."))))
                report.append(f"- **{item.name}**: {file_count} files (Subjects: {', '.join(subjects) if subjects else 'None'})")
    else:
        report.append("  - Pre_Primary folder is missing!")
        
    report.append("\n" + "="*40 + "\n")
    
    # 2. Primary Audit
    primary_path = BASE_DIR / "2. Primary"
    report.append("### 2. Primary (P1 - P7) Data Distribution")
    standard_primary_subjects = ["Mathematics", "English", "Science", "Social Studies", "Literacy"]
    if primary_path.exists():
        for item in sorted(primary_path.iterdir()):
            if item.is_dir():
                files = list(item.glob("**/*"))
                file_count = sum(1 for f in files if f.is_file() and not f.name.startswith("."))
                
                # Group files by subject folders
                subject_counts = {}
                for f in files:
                    if f.is_file() and not f.name.startswith("."):
                        # Inferred subject name is the parent folder or next-parent
                        rel_path = f.relative_to(item)
                        parts = rel_path.parts
                        subj = parts[0] if parts else "Unclassified"
                        subject_counts[subj] = subject_counts.get(subj, 0) + 1
                        
                subj_strs = [f"{s} ({c} files)" for s, c in sorted(subject_counts.items())]
                report.append(f"- **{item.name}**: Total {file_count} files")
                for sub, count in sorted(subject_counts.items()):
                    report.append(f"  * {sub}: {count} files")
                
                # Check for standard subject gaps
                missing = [s for s in standard_primary_subjects if s not in subject_counts]
                if missing:
                    report.append(f"  * ⚠️ **MISSING SUBJECTS**: {', '.join(missing)}")
    else:
        report.append("  - Primary folder is missing!")
        
    report.append("\n" + "="*40 + "\n")
    
    # 3. Secondary Audit
    secondary_path = BASE_DIR / "3. Secondary"
    report.append("### 3. Secondary (S1 - S6) Data Distribution")
    standard_secondary_subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Geography", "History", "CRE", "Agriculture"]
    if secondary_path.exists():
        for item in sorted(secondary_path.iterdir()):
            if item.is_dir():
                files = list(item.glob("**/*"))
                file_count = sum(1 for f in files if f.is_file() and not f.name.startswith("."))
                
                subject_counts = {}
                for f in files:
                    if f.is_file() and not f.name.startswith("."):
                        rel_path = f.relative_to(item)
                        parts = rel_path.parts
                        subj = parts[0] if parts else "Unclassified"
                        subject_counts[subj] = subject_counts.get(subj, 0) + 1
                        
                report.append(f"- **{item.name}**: Total {file_count} files")
                for sub, count in sorted(subject_counts.items()):
                    report.append(f"  * {sub}: {count} files")
                
                missing = [s for s in standard_secondary_subjects if s not in subject_counts]
                if missing:
                    report.append(f"  * ⚠️ **MISSING SUBJECTS**: {', '.join(missing)}")
    else:
        report.append("  - Secondary folder is missing!")
        
    print("\n".join(report))

if __name__ == "__main__":
    audit_curriculum()
