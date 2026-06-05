import pdfplumber
import os

def read_sample_pdf():
    path = "/Users/luke/Downloads/docs/ eduquest 2 stabler/EduQuest_Syllabus_Database/1. Pre_Primary/Middle_Class/LA1_Language_and_Literacy/MIDDLE CLASS-LITERACY HOLIDAY WORK KINGS SCHOOL-KABOWA.pdf"
    if not os.path.exists(path):
        # Try finding a matches by prefix
        print(f"Path does not exist: {path}")
        return
        
    print(f"Reading PDF: {path}")
    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages[:10]):
            text = page.extract_text()
            if text:
                print(f"--- Page {idx+1} ---")
                # Print first 20 lines
                lines = text.split('\n')
                for line in lines[:40]:
                    print(line)

if __name__ == "__main__":
    read_sample_pdf()
