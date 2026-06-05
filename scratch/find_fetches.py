import re

file_path = r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\frontend\app\page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "fetch" in line:
        print(f"Line {i+1}: {line.strip()}")
