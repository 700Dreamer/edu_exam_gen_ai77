import requests
import json

def test_api():
    url = "http://localhost:8000/api/nursery-exam"
    payload = {
        "class_level": "Middle Class",
        "learning_area": "LA1", # Language & Literacy
        "term": "Term 1",
        "period": "EOT",
        "school_name": "Test Kindergarten",
        "year": "2026"
    }
    
    print(f"Sending POST request to {url} with payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            resp_data = response.json()
            exam_data = resp_data.get("exam_data", {})
            integrity = resp_data.get("integrity", {})
            html = resp_data.get("html", "")
            
            print("\n✅ Success! Exam generated successfully.")
            print(f"School Name: {exam_data.get('school')}")
            print(f"Class Level: {exam_data.get('class_level')}")
            print(f"Learning Area: {exam_data.get('learning_area')}")
            
            questions = exam_data.get("questions", [])
            print(f"Total Questions Generated: {len(questions)}")
            for idx, q in enumerate(questions):
                print(f"\n[Question {idx+1}]")
                print(f"  Type: {q.get('type')}")
                print(f"  Instruction: {q.get('instruction')}")
                print(f"  Content: {q.get('content')}")
                
            # Verify if HTML compiles nicely and check if there are circular option classes
            print("\nHTML Preview (First 500 chars):")
            print(html[:500] + "...")
            
            print("\nChecking circle-opt rendered markup elements:")
            import re
            opt_matches = re.findall(r'<div class="nq-circle-opt"[^>]*>.*?</div>', html)
            print(f"Found {len(opt_matches)} circle options rendered in HTML.")
            for match in opt_matches[:5]:
                print(f"  Rendered tag: {match}")
                
        else:
            print("❌ Failed. Response body:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_api()
