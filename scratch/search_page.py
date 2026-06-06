with open(r"c:\Users\Ki\Desktop\kizito\eduquestai\eduquest_2_stabler2_new\sys\src\frontend\app\page.tsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- VIEW SEARCH ---")
for i, line in enumerate(lines):
    if "function AnalyticsView" in line or "function IngestionView" in line or "function SyllabusGraphView" in line:
        print(f"Line {i+1}: {line.strip()}")
