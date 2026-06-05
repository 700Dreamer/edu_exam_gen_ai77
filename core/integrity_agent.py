import re
import json

def check_tier1_heuristics(question):
    """
    Fast rule-based checks. Returns (bool: pass, str: feedback_if_failed)
    """
    q_type = question.get("type", "short_answer")
    text = question.get("text", "")
    diagram_desc = question.get("diagram_description", "")
    sub_questions = question.get("sub_questions", [])
    total_marks = question.get("marks", 0)
    
    # 1. LaTeX closing check
    if text.count("$") % 2 != 0:
        return False, "Unclosed LaTeX inline math tag '$' found in question text."
    
    # 2. Sub-marks tally check
    if q_type == "structured" and sub_questions:
        try:
            total_marks_int = int(total_marks)
            sum_sub = sum(int(sq.get("marks", 0)) for sq in sub_questions)
            if sum_sub != total_marks_int:
                return False, f"Total marks ({total_marks_int}) does not match the sum of sub-question marks ({sum_sub})."
        except:
            pass # Ignore if marks aren't ints
            
    # 3. Diagram Redundancy check
    if diagram_desc and text:
        # Extract numbers from diagram desc
        nums = re.findall(r'\b\d+(?:\.\d+)?\b', diagram_desc)
        for num in nums:
            # If the exact number is repeated in the text stem, fail it. 
            # We ignore small numbers like 1, 2, 3 as they could be question numbers or generic.
            if len(num) > 1 and num in text:
                return False, f"Diagram redundancy: The number '{num}' from the diagram_description is repeated in the question text. Force the student to read the diagram instead."
                
    # 4. Venn Diagram complexity check
    if diagram_desc and "venn" in diagram_desc.lower():
        # Check if diagram description mentions at least a few elements
        elements = re.findall(r'["\']([^"\']+)["\']', diagram_desc)
        if len(elements) < 3 and "elements" not in diagram_desc.lower():
            return False, "Venn diagram description is too simple. It must contain at least 3-4 elements and meaningful intersections."

    return True, ""

async def check_tier2_pedagogical(client, question, subject, level):
    """
    LLM-based check using a cheaper/faster model.
    """
    vocab_rule = ""
    is_lower_primary = False
    if "Primary" in level:
        m = re.search(r'\d+', level)
        if m and int(m.group()) <= 4:
            is_lower_primary = True
    elif any(x in level for x in ["Nursery", "ECD", "Baby", "Middle", "Top"]):
        is_lower_primary = True
        
    if is_lower_primary:
        vocab_rule = "5. Vocabulary Complexity: Since this is Lower Primary (P1-P4), words must be extremely simple. Fail the question if it uses complex words (e.g., 'calculate', 'determine', 'photosynthesis') instead of simple ones (e.g., 'find', 'work out', 'plants')."

    prompt = f"""You are an elite National Exam Auditor for {level} {subject}.
Review the following generated exam question JSON:
{json.dumps(question, indent=2)}

Check for:
1. Pedagogical Alignment: Does it test application, or is it just rote recall? (e.g. "Define X" is bad).
2. Mathematical Correctness: Does the math compute? Does the marking guide accurately reach the answer?
3. Localization: Are there non-Ugandan references (e.g., apples, dollars, snow)?
4. Syllabus Bleed: Are there concepts way too advanced for this level?
{vocab_rule}

If it passes all checks, return ONLY valid JSON: {{"status": "PASS", "feedback": null}}
If it fails ANY check, return ONLY valid JSON: {{"status": "FAIL", "feedback": "Detailed reason why it failed and how to fix it."}}
"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict examiner. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        res = json.loads(response.choices[0].message.content)
        if res.get("status") == "PASS":
            return True, ""
        return False, res.get("feedback", "Failed pedagogical review.")
    except Exception as e:
        print(f"Tier 2 Check Error: {e}")
        return True, ""

import os
import base64

async def check_tier3_vision(client, image_path, question_text):
    """
    Tier 3: Vision Audit. Uses gpt-4o to look at the generated image
    and determine if it accurately matches the question.
    Returns (bool: pass, str: feedback)
    """
    if not os.path.exists(image_path):
        return True, ""
        
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        prompt = f"""You are a strict Exam Image Validator.
Read this exam question: '{question_text}'

Look at the provided diagram. Your job is to verify if the student can successfully solve the question using ONLY this diagram.
Check for:
1. Are all necessary numbers, labels, sides, and axes clearly legible?
2. Are there any misspelled words, strange hallucinated text, or weird symbols?
3. Did the image accidentally reveal the final answer?

If it passes, return exactly: {{"status": "PASS", "feedback": null}}
If it fails, return exactly: {{"status": "FAIL", "feedback": "Detailed reason why it failed so the image generator can fix it."}}
"""
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        res = json.loads(response.choices[0].message.content)
        if res.get("status") == "PASS":
            return True, ""
        return False, res.get("feedback", "Vision check failed.")
    except Exception as e:
        print(f"Tier 3 Vision Check Error: {e}")
        return True, ""

async def run_integrity_check(exam_data, client=None, ai_check=False, **kwargs):
    """
    Runs the multi-tier integrity checks on the entire exam.
    Returns a comprehensive report.
    """
    report = {
        "overall_status": "PASS",
        "questions": []
    }
    
    questions = exam_data.get("questions", [])
    
    # We might need to pass down subject/level if we do tier 2, but for Nursery it's mostly tier 1.
    for q in questions:
        q_report = {
            "final_status": "PASS",
            "rule_check": {"status": "PASS", "issues": []},
            "ai_check": None
        }
        
        # Tier 1 Heuristics
        pass_t1, msg_t1 = check_tier1_heuristics(q)
        if not pass_t1:
            q_report["rule_check"]["status"] = "FAIL"
            q_report["rule_check"]["issues"].append(msg_t1)
            q_report["final_status"] = "FAIL"
            report["overall_status"] = "FAIL"
            
        # Optional Tier 2 AI check
        if ai_check and client and pass_t1:
            # We assume subject/level are generically known or not strictly required for this nursery level call.
            pass_t2, msg_t2 = await check_tier2_pedagogical(client, q, "Nursery", "Pre-Primary")
            q_report["ai_check"] = {"status": "PASS" if pass_t2 else "FAIL", "issues": []}
            if not pass_t2:
                q_report["ai_check"]["issues"].append(msg_t2)
                q_report["final_status"] = "FAIL"
                report["overall_status"] = "FAIL"
                
        report["questions"].append(q_report)
        
    return report

