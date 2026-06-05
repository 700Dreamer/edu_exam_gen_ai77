import os
from docx import Document

def read_sample_docx():
    path = "/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/1. Pre_Primary/Middle_Class/LA1_Language_and_Literacy/term I lesson notes  for  middle for Reading  2026.docx"
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return
        
    print(f"Reading Docx: {path}")
    doc = Document(path)
    
    # Print the first 50 paragraphs
    for idx, p in enumerate(doc.paragraphs[:60]):
        text = p.text.strip()
        if text:
            print(f"{idx}: {text}")

if __name__ == "__main__":
    read_sample_docx()
