import json
import os
from jinja2 import Environment, FileSystemLoader
from core.paper_structure import get_paper_structure

# Set up Jinja2 Environment
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
if os.path.exists(templates_dir):
    jinja_env = Environment(loader=FileSystemLoader(templates_dir))
else:
    jinja_env = None


def build_full_html(mode, exam_type, level, subject, term_roman, exam_year, duration, school_name, brand_name, question_count, content_raw, topic="", logo_b64=None, paper_style="uneb_standard", view_mode="scroll"):
    """
    Constructs the full HTML document string, utilizing strict JSON outputs to guarantee formatting.
    """
    
    title_text = f"{exam_type} {term_roman} EXAMINATIONS {exam_year}".upper() if mode == "Exams" else f"{subject} | {topic}".upper()
    
    # ── BUILD SCORING TABLE ──
    rows = ["1-10", "11-20", "21-30", "31-40", "41-45", "46-50", "51-55", "TOTAL"]
    exam_rows = "".join([f"<tr><td>{r}</td><td></td><td></td></tr>" for r in rows])

    right_col = f"""<div class="ex-panel">
        <div style="font-size:11px; font-weight:bold; text-align:center; border:1px solid #000; border-bottom:none; padding:4px;">FOR EXAMINER'S USE ONLY</div>
        <table><tr><th>Qn No.</th><th>MARKS</th><th>EXR'S NO.</th></tr>{exam_rows}</table>
    </div>"""
    
    # ── OFFICIAL PAPER STRUCTURE (from UNEB registry) ──
    ps = get_paper_structure(subject, level)
    sec_a_count = ps["sec_a_count"]
    sec_a_marks = ps["sec_a_marks"]
    sec_b_count = ps["sec_b_count"]
    sec_b_marks = ps["sec_b_marks"]
    total_marks = ps["total_marks"]
    # Use registry duration if caller didn't specify a custom one
    official_duration = ps.get("duration", duration) if duration in ("", "2 HR 30 MIN", None) else duration
    sec_b_note = ps.get("sec_b_note", "Attempt all questions in Section B.")
    has_two_sections = sec_b_count > 0

    sec_b_line = (
        f"<li>Section B has {sec_b_count} questions ({sec_b_marks} marks). {sec_b_note}</li>"
        if has_two_sections else ""
    )

    left_col = f"""<div class="instr-panel">
        <div style="font-weight:900; margin-bottom:10px; font-size:11px;">Read the following instructions carefully:</div>
        <ul class="instr-list" style="list-style-type: decimal; padding-left: 20px;">
            <li>The paper has {'two sections: A and B' if has_two_sections else 'one section (Section A)'}.</li>
            <li>Section A has {sec_a_count} questions ({sec_a_marks} marks).</li>
            {sec_b_line}
            <li>Answer all questions. All answers to both Sections A and B must be written in the spaces provided.</li>
            <li>All answers must be written using a blue or black ball point pen or ink. Diagrams should be drawn in pencil.</li>
            <li>Unnecessary alteration of work may lead to loss of marks.</li>
            <li>Any handwriting that can not easily be read may lead to loss of marks.</li>
            <li>Do not fill any thing in the boxes. They are for examiners’ use.</li>
        </ul>
    </div>"""

    # ── BUILD SYLLABUS ANALYSIS ──
    topic_map = {}
    if mode == "Exams":
        try:
            data_raw = json.loads(content_raw)
            for q in data_raw.get("questions", []):
                t = q.get("topic", "General Core")
                num = q.get("number", "?")
                if t not in topic_map: topic_map[t] = []
                topic_map[t].append(f"Q{num}")
        except: pass
    
    syllabus_rows = "".join([f"<tr><td style='padding:4px; border-bottom:0.5px solid #eee;'>{t}</td><td style='text-align:center; padding:4px; border-bottom:0.5px solid #eee;'>{len(qs)}</td><td style='padding:4px; border-bottom:0.5px solid #eee; font-weight:700;'>{', '.join(qs)}</td></tr>" for t, qs in topic_map.items()])
    syllabus_table = f"""
    <div style="margin-top: 30px; border: 1px solid #000; border-radius:0; padding: 15px;">
        <div style="font-size: 11px; font-weight: 900; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 10px; display:flex; justify-content:space-between;">
            <span>Syllabus Saturation Audit</span>
            <span style="opacity:0.6;">Pedagogical Transparency Report</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <thead>
                <tr style="background:#f8fafc; border-bottom: 1px solid #000;">
                    <th style="text-align: left; padding: 6px;">Curriculum Topic / Theme</th>
                    <th style="width: 80px; padding: 6px;">Questions</th>
                    <th style="text-align: left; padding: 6px;">Reference Map</th>
                </tr>
            </thead>
            <tbody>
                {syllabus_rows if syllabus_rows else "<tr><td colspan='3' style='text-align:center; padding:20px; color:#94a3b8;'>Processing Coverage Data...</td></tr>"}
            </tbody>
        </table>
    </div>
    """

    # ── PARSE JSON TO HTML & EXTRACT ANSWER KEY ──
    try:
        data = json.loads(content_raw)
        parsed_html = ""
        marking_guide_parsed_html = ""
        answer_key_html = ""
        
        # ── SCENARIO NARRATIVE (If Present) ──
        scenario = data.get("scenario_text")
        if scenario:
            scenario_block = f"<div style='background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 16px; padding: 25px; margin-bottom: 40px; line-height: 1.8; font-style: italic; color: var(--s); box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);'>"
            scenario_block += f"  <div style='font-size: 10px; font-weight: 900; color: var(--p); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 2px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;'>Competency Scenario Context</div>"
            scenario_block += f"  <div style='font-size: 16px; font-weight: 500;'>{scenario}</div>"
            scenario_block += f"</div>"
            parsed_html += scenario_block
            marking_guide_parsed_html += scenario_block

        if mode == "Exams":
            questions = data.get("questions", [])

            # Separate into Section A and Section B lists
            sec_a_qs = [q for q in questions if int(q.get("number", 0)) <= sec_a_count]
            sec_b_qs = [q for q in questions if int(q.get("number", 0)) > sec_a_count]

            if sec_a_qs:
                current_instruction = None
                for q in sec_a_qs:
                    instr = q.get("instruction_group")
                    if instr and instr != current_instruction:
                        instr_block = f"<div style='font-weight:bold; margin-top:20px; margin-bottom:10px; font-size:15px; color:#000;'>{instr}</div>"
                        parsed_html += instr_block
                        marking_guide_parsed_html += instr_block
                        current_instruction = instr
                    parsed_html += build_question_html(mode, q, subject, level)
                    marking_guide_parsed_html += build_question_html(mode, q, subject, level, is_marking_guide=True)
                    answer_key_html += build_answer_row_html(q)

            # Section B — always full width, compact override
            if sec_b_qs:
                sec_b_header = f"<div style='text-align:center; margin-top:30px; border-bottom: 2px solid #000; padding-bottom:5px; margin-bottom:20px;'><b style='text-decoration:underline; font-size:14px;'>SECTION B ({sec_b_marks} Marks)</b></div>"
                parsed_html += sec_b_header
                marking_guide_parsed_html += sec_b_header
                
                current_instruction = None
                for q in sec_b_qs:
                    instr = q.get("instruction_group")
                    if instr and instr != current_instruction:
                        instr_block = f"<div style='font-weight:bold; margin-top:20px; margin-bottom:10px; font-size:15px; color:#000;'>{instr}</div>"
                        parsed_html += instr_block
                        marking_guide_parsed_html += instr_block
                        current_instruction = instr
                    parsed_html += build_question_html(mode, q, subject, level)
                    marking_guide_parsed_html += build_question_html(mode, q, subject, level, is_marking_guide=True)
                    answer_key_html += build_answer_row_html(q)

        elif mode == "Lesson Notes":
            for s in data.get("sections", []):
                h = s.get("heading", "")
                c = s.get("content", "")
                tikz = s.get("tikz_code")
                
                parsed_html += f"<div style='margin-bottom: 35px;'>"
                parsed_html += f"  <h3 style='color: var(--p); border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 15px;'>{h}</h3>"
                parsed_html += f"  <div style='font-size: 15.5px; line-height: 1.8; margin-bottom: 15px;'>{c}</div>"
                if tikz:
                    parsed_html += f"  <div style='text-align:center; padding: 15px;'>{tikz}</div>"
                parsed_html += f"</div>"

        elif mode == "Schemes of Work":
            parsed_html += "<table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 20px;'>"
            parsed_html += "<thead><tr style='background: var(--p); color: white;'>"
            parsed_html += "<th style='padding: 12px; border: 1px solid #e2e8f0; width: 80px;'>Week</th>"
            parsed_html += "<th style='padding: 12px; border: 1px solid #e2e8f0; width: 150px;'>Topic</th>"
            parsed_html += "<th style='padding: 12px; border: 1px solid #e2e8f0;'>Objectives</th>"
            parsed_html += "<th style='padding: 12px; border: 1px solid #e2e8f0;'>Activities</th>"
            parsed_html += "<th style='padding: 12px; border: 1px solid #e2e8f0; width: 120px;'>Resources</th>"
            parsed_html += "</tr></thead><tbody>"
            
            for w in data.get("weeks", []):
                wk = w.get("week_number", "")
                top = w.get("topic", "")
                obj = w.get("objectives", "")
                act = w.get("activities", "")
                res = w.get("resources", "")
                
                parsed_html += f"<tr>"
                parsed_html += f"<td style='padding: 12px; border: 1px solid #e2e8f0; font-weight: bold; vertical-align: top;'>{wk}</td>"
                parsed_html += f"<td style='padding: 12px; border: 1px solid #e2e8f0; font-weight: bold; color: var(--s); vertical-align: top;'>{top}</td>"
                parsed_html += f"<td style='padding: 12px; border: 1px solid #e2e8f0; vertical-align: top;'>{obj}</td>"
                parsed_html += f"<td style='padding: 12px; border: 1px solid #e2e8f0; vertical-align: top;'>{act}</td>"
                parsed_html += f"<td style='padding: 12px; border: 1px solid #e2e8f0; font-style: italic; vertical-align: top; color: #64748b;'>{res}</td>"
                parsed_html += f"</tr>"
                
            parsed_html += "</tbody></table>"
    except json.JSONDecodeError:
        parsed_html = content_raw
        marking_guide_parsed_html = content_raw
        answer_key_html = "<tr><td colspan='3'>JSON Error. Manual marking required.</td></tr>"

    # ── SAFEGUARD FOR JAVASCRIPT INJECTION ──
    js_content = parsed_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("</script>", "<\\/script>")
    js_answers = answer_key_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("</script>", "<\\/script>")

    # ── DYNAMIC FONT FOR LOWER PRIMARY ──
    import re
    is_lower_primary = False
    if "Primary" in level:
        m = re.search(r'\d+', level)
        if m and int(m.group()) <= 4:
            is_lower_primary = True
    elif any(x in level for x in ["Nursery", "ECD", "Baby", "Middle", "Top"]):
        is_lower_primary = True
        
    font_css = '"Comic Sans MS", "Chalkboard SE", "Comic Neue", sans-serif' if is_lower_primary else '"Times New Roman", Times, serif'
    line_height = '1.9' if is_lower_primary else '1.5'

    template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Playfair+Display:ital,wght@1,900&family=Patrick+Hand&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<style>
:root {{
  --p: #800020;
  --s: #1e293b;
  --bg: #f8fafc;
  --br-l: 12px;
}}

* {{ box-sizing: border-box; transition: background 0.3s ease; margin: 0; padding: 0; }}

body {{ 
  background: var(--bg); 
  font-family: 'Outfit', sans-serif; 
  padding: 40px 0 120px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
  min-height: 100vh;
}}

/* 📄 PREMIUM PAPER ENGINE */
.page {{
  background: white;
  width: 210mm;
  min-height: 297mm;
  padding: 20mm;
  position: relative;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05);
  border-radius: 2px;
  overflow: hidden;
  color: #1e293b;
  line-height: {line_height};
  font-family: {font_css};
}}

/* Dynamic Institutional Watermark */
.page::after {{
  content: "{brand_name}";
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  font-size: 8rem;
  font-weight: 900;
  color: #000;
  opacity: var(--watermark, 0.02);
  pointer-events: none;
  z-index: 0;
  white-space: nowrap;
}}

.brand-h {{ position: relative; z-index: 1; border-bottom: 4px solid var(--p); padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
.brand-name {{ font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 900; font-style: italic; color: var(--p); letter-spacing: -0.02em; }}
.doc-t {{ text-transform: uppercase; font-weight: 900; letter-spacing: 0.2em; font-size: 10px; color: #64748b; }}

.idx-grid {{ display: flex; gap: 4px; margin-top: 10px; }}
.idx-box {{ width: 24px; height: 32px; border: 1.5px solid #1e293b; border-radius: 4px; }}

.cand-box {{ background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 25px 0; font-size: 13px; }}
.cand-line {{ border-bottom: 2px dotted #000; flex: 1; margin-left: 10px; height: 18px; }}

.col-l {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 30px; margin-bottom: 30px; }}
.instr-panel {{ font-size: 11.5px; color: #475569; line-height: 1.6; }}
.ex-panel table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
.ex-panel th {{ border: 1px solid #000; padding: 6px; font-weight:bold; }}
.ex-panel td {{ border: 1px solid #000; padding: 6px; text-align: center; height: 26px; }}

.body-c {{ font-size: 15.5px; line-height: 2.2; white-space: pre-wrap; font-family: "Times New Roman", Times, serif !important; }}
.pgn {{ position: absolute; bottom: 15mm; left: 0; width: 100%; text-align: center; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; }}

/* ── ANSWER LINES ── */
.ans-lines {{ margin-left: 15px; margin-top: 8px; margin-bottom: 22px; }}
.ans-line {{ border-bottom: 1px solid #000; height: 28px; margin-bottom: 8px; display: block; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}

/* ── ILLUSTRATION & DIAGRAM STYLING ── */
.ill-box img {{ max-width: 400px; height: auto; border-radius: 8px; margin: 0 auto; display: block; }}
.ill-box svg {{ max-width: 400px; height: auto; display: block; margin: 0 auto; }}
.ill-box svg * {{ stroke-width: 2px !important; }}

/* ── REAL PAPER (UNEB) PROTOCOL ── */
.tmpl-uneb {{ font-family: "Times New Roman", serif !important; }}
.tmpl-uneb.page {{ border: 6px double #000 !important; box-shadow: none !important; border-radius: 0 !important; }}
.tmpl-uneb .brand-h {{ flex-direction: column !important; align-items: center !important; text-align: center !important; border-bottom: 2px solid #000 !important; }}
.tmpl-uneb .brand-name {{ font-family: serif !important; text-transform: uppercase !important; font-size: 24px !important; font-weight:bold !important; font-style: normal !important; color: #000 !important; margin-top:5px !important; }}
.tmpl-uneb .doc-t {{ color: #000 !important; font-size: 18px !important; font-weight:bold !important; letter-spacing: 1px !important; margin-top: 10px !important; }}
.tmpl-uneb .cand-box {{ background: transparent !important; border: 1px solid #000 !important; border-radius: 0 !important; }}
.tmpl-uneb .idx-box {{ border-color: #000 !important; border-radius: 0 !important; }}

/* ── UI ELEMENTS ── */
.panel-toggle {{ position: fixed; top: 20px; right: 20px; z-index: 1000; width: 44px; height: 44px; background: var(--p); color: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 10px 15px -3px rgba(128,0,32,0.3); }}
.style-panel {{ position: fixed; top: 80px; right: 20px; width: 280px; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(20px); border-radius: 24px; padding: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); transform: translateX(320px); transition: 0.4s; z-index: 999; }}
.style-panel.open {{ transform: translateX(0); }}
.tmpl-btn {{ width: 100%; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; background: white; font-size: 11px; font-weight: 700; margin-bottom: 8px; cursor: pointer; text-align: left; }}
.tmpl-btn:hover {{ border-color: var(--p); background: #fff1f2; color: var(--p); }}

#preview-toolbar {{ position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); background: rgba(30, 41, 59, 0.9); backdrop-filter: blur(10px); border-radius: 20px; padding: 8px 16px; display: flex; align-items: center; gap: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); z-index: 1001; }}
#preview-toolbar button {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 800; color: white; cursor: pointer; }}
#preview-toolbar button:hover {{ background: var(--p); border-color: var(--p); }}
#zoom-level {{ color: white; font-size: 12px; font-weight: 900; min-width: 40px; text-align: center; }}

@media print {{ 
  @page {{ margin: 0; }}
  .style-panel, .panel-toggle, #preview-toolbar {{ display: none !important; }} 
  body {{ padding: 0; background: white; }}
  .page {{ box-shadow: none !important; border: none !important; margin: 0 auto !important; page-break-after: always !important; }}
  .tmpl-uneb.page {{ border: 6px double #000 !important; }}
}}
</style>
</head>
<body>

<div class="panel-toggle" onclick="toggleP()"><i class="lucide-layout"></i></div>
<div class="style-panel" id="pS">
  <div class="p-title">Appearance Templates</div>
  <div class="style-group">
    <button class="tmpl-btn" onclick="applyT('elite_dark')">Elite Dark Bar</button>
    <button class="tmpl-btn" onclick="applyT('pro_protocol')">Official Protocol</button>
    <button class="tmpl-btn" onclick="applyT('academic_clean')">Academic Clean</button>
    <button class="tmpl-btn" onclick="applyT('classic')">Classical Image 4</button>
    <button class="tmpl-btn" style="background:#000; color:#fff;" onclick="applyT('uneb_standard')">Real Paper (B&W Standard)</button>
  </div>
  <div style="font-size:10px; color:#64748b; margin-bottom:10px; font-weight:700;">WATERMARK INTENSITY</div>
  <input type="range" min="0" max="0.1" step="0.01" value="0.02" style="width:100%;" oninput="sv('--watermark',this.value)">
  <button class="tmpl-btn" style="background:var(--p); color:white; padding:15px; border:none; border-radius:8px; margin-top:20px; font-weight:900;" onclick="window.print()">PRINT FINAL DOCUMENT</button>
</div>
"""
    if mode in ["Lesson Notes", "Schemes of Work"]:
        document_title = "LESSON NOTES" if mode == "Lesson Notes" else "SCHEME OF WORK"
        document_body = f"""
<!-- PAGE 1: CONTENT -->
<div class="page" id="contentP">
  <div class="brand-logo" style="opacity:0.2; position:absolute; top:20px; right:20px; height:40px;">
    {'<img src="data:image/png;base64,' + logo_b64 + '" style="height:100%">' if logo_b64 else ''}
  </div>

  <div class="brand-h">
    <div>
      <div class="doc-t" style="margin-bottom:2px; font-size:12px;">{document_title} | {title_text}</div>
      <div class="brand-name" style="font-size:36px;">{level} - {subject}</div>
    </div>
  </div>
  
  <div class="body-c" id="content-body" style="margin-top:20px;">
    {parsed_html}
  </div>
  <div class="pgn">EduQuest Core | {document_title} Module</div>
</div>
"""
    else:
        document_body = f"""
<!-- PAGE 1: HEADER -->
<div class="page" id="mainP">
  <div class="brand-h">
    <div class="doc-t" style="margin-bottom:2px; text-align:center;">{title_text}</div>
    <div class="brand-name" style="text-align:center;">{subject.upper()} FOR {level.upper()}</div>
    <div style="width:100%; text-align:center; font-weight:bold; font-size:16px; margin-top:10px;">Time allowed: {duration}</div>
  </div>

  <div class="cand-box" style="margin: 20px 0; font-family: 'Times New Roman', serif;">
    <div style="display:flex; align-items:flex-end; margin-bottom:15px; font-size: 16px;">
        <span>Name:</span> 
        <div style="flex: 1; border-bottom: 2px dotted #000; margin-left: 10px; height: 18px;"></div>
    </div>
    <div style="display:flex; gap: 20px; align-items:flex-end; font-size: 16px;">
        <div style="display:flex; flex: 2; align-items:flex-end;">
            <span>District:</span> 
            <div style="flex: 1; border-bottom: 2px dotted #000; margin-left: 10px; height: 18px;"></div>
        </div>
        <div style="display:flex; flex: 1; align-items:flex-end;">
            <span>Stream:</span> 
            <div style="flex: 1; border-bottom: 2px dotted #000; margin-left: 10px; height: 18px;"></div>
        </div>
    </div>
  </div>

  <div class="col-l" style="margin-top:20px;">{left_col}{right_col}</div>
  
  <div class="pgn">Page 1</div>
</div>

<!-- REFERENCE MAP PAGE (NEW) -->
<div class="page" id="refMapP" style="display: none;">
  <div class="brand-h">
    <div>
      <div class="brand-name">{brand_name}</div>
      <div style="font-size:11px; font-weight:900; letter-spacing:5px;">CURRICULUM ALIGNMENT</div>
    </div> 
  </div>
  {syllabus_table}
  <div class="pgn">Reference Map — Neural Audit</div>
</div>

<!-- PAGE 2: CONTENT -->
<div class="page" id="contentP">
  <div class="brand-logo" style="opacity:0.2; position:absolute; top:20px; right:20px; height:40px;">
    {'<img src="data:image/png;base64,' + logo_b64 + '" style="height:100%">' if logo_b64 else ''}
  </div>

  <div style="text-align:center; margin-top:10px; border-bottom: 2px solid #000; padding-bottom:5px; margin-bottom:20px;">
    <b style="text-decoration:underline; font-size:14px;">SECTION A ({sec_a_marks} Marks)</b>
  </div>

  <div class="body-c" id="content-body">
    {parsed_html}
  </div>
  <div class="pgn">Page 2 of 2 — End of Release</div>
</div>

<!-- PAGE 3: MARKING GUIDE (TEACHER ONLY) -->
<div class="page" id="marking-guide-page" style="display: none;">
  <div class="brand-logo" style="opacity:0.2; position:absolute; top:20px; right:20px; height:40px;">
    {'<img src="data:image/png;base64,' + logo_b64 + '" style="height:100%">' if logo_b64 else ''}
  </div>
  <div class="brand-h" style="border-bottom: 4px solid #0066cc;">
    <div>
      <div class="brand-name" style="color: #0066cc;">{brand_name}</div>
      <div style="font-size:11px; font-weight:900; letter-spacing:5px; color: #0066cc;">PEDAGOGICAL MARKING GUIDE</div>
    </div> 
  </div>
  <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
      <div class="doc-t" style="background:#0066cc; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block;">CONFIDENTIAL EXAMINER'S COPY</div>
      <div style="color:#0066cc; font-weight:900; font-size:12px;">THIS DOCUMENT CONTAINS OFFICIAL ANSWERS AND MARK ALLOCATIONS.</div>
  </div>
  
  <div style="text-align:center; margin-top:10px; border-bottom: 2px solid #000; padding-bottom:5px; margin-bottom:20px;">
    <b style="text-decoration:underline; font-size:14px;">SECTION A ({sec_a_marks} Marks)</b>
  </div>

  <div class="body-c" id="marking-content-body">
    {marking_guide_parsed_html}
  </div>
  
  <div class="pgn">Page 3 of 3 — Secure Marking Key</div>
</div>
"""

    template += document_body

    template += f"""

<!-- ── PREVIEW TOOLBAR ── -->
<div id="preview-toolbar">
  <button onclick="zoomOut()">−</button>
  <span id="zoom-level">100%</span>
  <button onclick="zoomIn()">+</button>
  <div class="tb-sep" style="width:1px; height:20px; background:rgba(0,0,0,0.1); margin:0 10px;"></div>
  <button onclick="window.print()">Print Final</button>
</div>

<!-- ── ENGINEERING SCRIPTS ── -->
<script>
function sv(n,v) {{ document.documentElement.style.setProperty(n,v); }}
function toggleP() {{ document.getElementById('pS').classList.toggle('open'); }}

// ── ZOOM CONTROLS ──
let _zoom = 1.0;
function updateZoom() {{
  document.querySelectorAll('.page').forEach(p => {{
    p.style.transform = `scale(${{_zoom}})`;
    p.style.transformOrigin = 'top center';
  }});
  document.getElementById('zoom-level').textContent = Math.round(_zoom * 100) + '%';
}}
function zoomIn() {{ _zoom = Math.min(2.0, _zoom + 0.1); updateZoom(); }}
function zoomOut() {{ _zoom = Math.max(0.4, _zoom - 0.1); updateZoom(); }}

const tmpls = {{
  elite_dark: {{ '--p':'#800020','--s':'#1e293b','class':'' }},
  pro_protocol: {{ '--p':'#1e293b','--s':'#64748b','class':'' }},
  uneb_standard: {{ '--p':'#000','--s':'#000','class':'tmpl-uneb' }},
}};

function applyT(t) {{
  const theme = tmpls[t] || tmpls['elite_dark'];
  const p = document.getElementById('mainP');
  p.className = 'page ' + (theme.class || '');
  Object.entries(theme).forEach(([k,v]) => {{ if(k!=='class') sv(k,v); }});
}}

document.addEventListener("DOMContentLoaded", function() {{
  applyT('{paper_style}');
  
  // 1. Safely Refresh TikZ Scripts
  const scripts = document.querySelectorAll('script');
  scripts.forEach(s => {{
    if(s.type === 'text/tikz') {{
      const newS = document.createElement('script');
      Array.from(s.attributes).forEach(attr => newS.setAttribute(attr.name, attr.value));
      newS.textContent = s.textContent;
      s.parentNode.replaceChild(newS, s);
    }}
  }});

  // 2. Trigger TikZ Engine
  
  // 3. Force KaTeX math rendering
  if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [ 
        {{left: "$$", right: "$$", display: true}},
        {{left: "$", right: "$", display: false}},
        {{left: "\\\\(", right: "\\\\)", display: false}},
        {{left: "\\\\[", right: "\\\\]", display: true}}
      ],
      throwOnError: false
    }});
  }}

  // 4. Auto-Paginate Content for 1:1.414 (A4) Aspect Ratio
  function paginateContent() {{
    const contentP = document.getElementById('contentP');
    if (!contentP) return;
    const bodyC = contentP.querySelector('.body-c');
    if (!bodyC) return;
    const items = Array.from(bodyC.children);
    const mainPage = document.getElementById('mainP');
    
    // Maximum height for the content area (A4 1122px - 2x20mm padding)
    const MAX_CONTENT_HEIGHT = 950; 
    
    let currentPage = contentP;
    let currentBody = bodyC;
    let allPages = [currentPage];
    
    // Clear the original body to redistribute
    bodyC.innerHTML = '';
    
    for(let i=0; i<items.length; i++) {{
        let item = items[i];
        currentBody.appendChild(item);
        
        // Check if current page overflows
        if (currentBody.offsetHeight > MAX_CONTENT_HEIGHT) {{
            // If this is the only item on the page and it's too big, we have to keep it here 
            // but we'll still start a new page for the next item.
            if (currentBody.children.length > 1) {{
                // Create new page
                const newPage = document.createElement('div');
                newPage.className = mainPage.className;
                newPage.style.marginTop = '40px';
                newPage.style.position = 'relative'; // for absolute footer
                
                const breakIndicator = document.createElement('div');
                breakIndicator.className = 'page-break-indicator';
                breakIndicator.innerHTML = '<hr style="flex:1; border:none; border-top: 2px dashed #cbd5e1;"><span style="color: #94a3b8; font-weight: 800; font-size: 10px; letter-spacing: 2px;">✂ PAGE BREAK</span><hr style="flex:1; border:none; border-top: 2px dashed #cbd5e1;">';
                breakIndicator.style.display = 'flex';
                breakIndicator.style.alignItems = 'center';
                breakIndicator.style.gap = '15px';
                breakIndicator.style.width = '210mm';
                breakIndicator.style.margin = '30px auto';
                
                if (!document.getElementById('pb-style')) {{
                    const style = document.createElement('style');
                    style.id = 'pb-style';
                    style.innerHTML = '@media print {{ .page-break-indicator {{ display: none !important; }} }}';
                    document.head.appendChild(style);
                }}
                
                const newBody = document.createElement('div');
                newBody.className = 'body-c';
                newPage.appendChild(newBody);
                
                // Insert after current page
                currentPage.parentNode.insertBefore(breakIndicator, currentPage.nextSibling);
                currentPage.parentNode.insertBefore(newPage, breakIndicator.nextSibling);
                
                // Move the overflowing item to the new page
                newBody.appendChild(item);
                
                currentPage = newPage;
                currentBody = newBody;
                allPages.push(newPage);
            }}
        }}
    }}
    
    // Add "Turn Over" and "END" tags
    for(let i=0; i<allPages.length; i++) {{
        const page = allPages[i];
        const oldPgn = page.querySelector('.pgn');
        if (oldPgn) oldPgn.remove(); // clear generic pagination
        
        const footerDiv = document.createElement('div');
        footerDiv.style.position = 'absolute';
        footerDiv.style.bottom = '20px';
        footerDiv.style.left = '40px';
        footerDiv.style.right = '40px';
        footerDiv.style.display = 'flex';
        footerDiv.style.justifyContent = 'space-between';
        footerDiv.style.fontFamily = '"Times New Roman", Times, serif';
        
        if (i < allPages.length - 1) {{
            // Intermediate pages get "Turn Over" on the right
            footerDiv.innerHTML = `<span></span><span style="font-style:italic; font-weight:bold; font-size:16px;">Turn Over</span>`;
        }} else {{
            // Last page gets END
            // footerDiv.innerHTML = `<span style="flex:1;"></span><span style="flex:1; text-align:center; font-size:18px; font-weight:bold;">....SUCCESS!....</span><span style="flex:1;"></span>`;
        }}
        page.appendChild(footerDiv);
    }}
  }}
  
  // Run pagination after a short delay to ensure layout is ready
  window.addEventListener('load', () => setTimeout(paginateContent, 500));
  setTimeout(paginateContent, 1500); // Fallback for dynamic content

  // 📡 READY SIGNAL
  window.parent.postMessage({{ type: 'EDUQUEST_READY' }}, '*');

  // ── UNIVERSAL IMAGE DRAG & RESIZE ──
  let activeDragImg = null;
  let startX=0, startY=0, initLeft=0, initTop=0;

  document.addEventListener('mousedown', (e) => {{
    let t = e.target;
    if (t.closest && t.closest('svg')) t = t.closest('svg');
    
    if (t.tagName?.toLowerCase() === 'img' || t.tagName?.toLowerCase() === 'svg' || (t.closest && t.closest('.q-img-zone'))) {{
      const rect = t.getBoundingClientRect();
      if (e.clientX > rect.right - 25 && e.clientY > rect.bottom - 25) return; // Allow native resize corner
      
      activeDragImg = t;
      if(window.getComputedStyle(t).position === 'static') {{
        t.style.position = 'relative';
      }}
      t.style.cursor = 'move';
      t.style.resize = 'both';
      t.style.overflow = 'hidden';
      t.style.zIndex = '1000';
      
      startX = e.clientX;
      startY = e.clientY;
      initLeft = parseInt(t.style.left || 0, 10);
      initTop = parseInt(t.style.top || 0, 10);
      e.preventDefault();
    }}
  }});

  document.addEventListener('mousemove', (e) => {{
    if (activeDragImg) {{
      const dx = (e.clientX - startX) / (window._zoom || 1);
      const dy = (e.clientY - startY) / (window._zoom || 1);
      activeDragImg.style.left = `${{initLeft + dx}}px`;
      activeDragImg.style.top = `${{initTop + dy}}px`;
    }}
  }});

  document.addEventListener('mouseup', () => {{
    if(activeDragImg) activeDragImg.style.cursor = 'default';
    activeDragImg = null;
  }});

  // ── QUESTION CLICK → postMessage to React parent (avoids srcDoc CORS) ──
  let activeWrapId = null;

  // Assign stable IDs and attach click handlers to every question
  document.querySelectorAll('.q-wrap').forEach(function(wrap, idx) {{
    const id = 'qw-' + idx;
    wrap.setAttribute('data-wid', id);

    wrap.addEventListener('click', function(e) {{
      e.stopPropagation();

      // Reset previous highlight
      document.querySelectorAll('.q-wrap').forEach(function(w) {{
        w.style.boxShadow = '';
        w.style.borderRadius = '6px';
      }});

      activeWrapId = id;
      wrap.style.boxShadow = '0 0 0 2.5px #800020';
      wrap.style.borderRadius = '6px';

      // Tell the React parent which question was clicked
      window.parent.postMessage({{
        type: 'QUESTION_CLICKED',
        wid: id,
        qtext: wrap.getAttribute('data-qtext'),
        subject: wrap.getAttribute('data-subject') || 'General',
        level: wrap.getAttribute('data-level') || 'Primary 4'
      }}, '*');
    }});
  }});

  // Deselect when clicking blank area
  document.addEventListener('click', function() {{
    document.querySelectorAll('.q-wrap').forEach(function(w) {{ w.style.boxShadow = ''; }});
    activeWrapId = null;
    window.parent.postMessage({{ type: 'QUESTION_DESELECTED' }}, '*');
  }});
}});

// 📡 MESSAGE RELAY FROM REACT PARENT
window.addEventListener('message', (event) => {{
  const d = event.data;

  // ─ View mode toggle ─
  if (d.type === 'EDUQUEST_VIEW_MODE') {{
    const mode = d.mode;
    const allPages = document.querySelectorAll('.page');
    const markingPage = document.getElementById('marking-guide-page');
    const refMapPage = document.getElementById('refMapP');
    const breakIndicators = document.querySelectorAll('.page-break-indicator');
    
    // Hide everything first
    allPages.forEach(p => {{ if(p) p.style.display = 'none'; }});
    breakIndicators.forEach(b => {{ if(b) b.style.display = 'none'; }});

    if (mode === 'marking') {{
      if(markingPage) markingPage.style.display = 'block';
    }} else if (mode === 'ref_map') {{
      if(refMapPage) refMapPage.style.display = 'block';
    }} else {{
      // Show all pages EXCEPT marking and ref_map
      allPages.forEach(p => {{
        if (p !== markingPage && p !== refMapPage) {{
            p.style.display = 'block';
        }}
      }});
      // Show break indicators only in student mode
      breakIndicators.forEach(b => {{ if(b) b.style.display = 'flex'; }});
    }}
  }}

  // ─ Inject image from React parent into the right question zone ─
  if (d.type === 'INJECT_IMAGE') {{
    const wrap = document.querySelector(`.q-wrap[data-wid="${{d.wid}}"]`);
    if (!wrap) return;
    
    // Inject custom styles for the interactive image container once
    if (!document.getElementById('interactive-img-styles')) {{
        const style = document.createElement('style');
        style.id = 'interactive-img-styles';
        style.innerHTML = `
            .img-wrapper {{ position: relative; transition: all 0.2s; z-index: 10; display: block; clear: both; margin: 10px auto; }}
            .img-wrapper.float-right {{ float: right; margin: 5px 0 5px 20px; clear: none; }}
            .img-wrapper.float-left {{ float: left; margin: 5px 20px 5px 0; clear: none; }}
            .img-wrapper.align-center {{ margin: 15px auto; display: flex; justify-content: center; width: max-content; }}
            
            .img-toolbar {{ position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: white; border: 1px solid #ccc; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border-radius: 8px; padding: 4px; display: flex; gap: 4px; opacity: 0; pointer-events: none; transition: opacity 0.2s, transform 0.2s; white-space: nowrap; z-index: 20; }}
            .img-wrapper:hover .img-toolbar {{ opacity: 1; pointer-events: auto; transform: translateX(-50%) translateY(5px); }}
            
            .img-toolbar button {{ background: none; border: none; cursor: pointer; font-size: 11px; padding: 4px 8px; border-radius: 4px; display: flex; align-items: center; gap: 4px; font-weight: bold; color: #333; }}
            .img-toolbar button:hover {{ background: #f1f5f9; }}
            
            .img-resizable {{ resize: both; overflow: hidden; min-width: 150px; min-height: 150px; max-width: 100%; padding: 8px; border: 2px dashed transparent; border-radius: 6px; background: #fff; }}
            .img-wrapper:hover .img-resizable {{ border-color: #cbd5e1; background: #f8fafc; }}
            
            .img-resizable svg, .img-resizable img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
        `;
        document.head.appendChild(style);
    }}

    let zone = wrap.querySelector('.q-img-zone');
    if (!zone) {{
      zone = document.createElement('div');
      zone.className = 'q-img-zone';
      // Insert at the top so float left/right text wrapping works perfectly
      wrap.insertBefore(zone, wrap.firstChild);
    }}
    
    const imgId = 'img-' + Math.random().toString(36).substr(2, 9);
    
    zone.innerHTML = `
      <div id="${{imgId}}" class="img-wrapper align-center">
        <div class="img-toolbar">
            <button onclick="document.getElementById('${{imgId}}').className='img-wrapper float-left'" title="Move Left">◧ Left</button>
            <button onclick="document.getElementById('${{imgId}}').className='img-wrapper align-center'" title="Center">◫ Center</button>
            <button onclick="document.getElementById('${{imgId}}').className='img-wrapper float-right'" title="Move Right">◨ Right</button>
            <div style="width:1px; background:#e2e8f0; margin:0 2px;"></div>
            <button onclick="document.getElementById('${{imgId}}').remove()" style="color:#ef4444;" title="Delete Image">🗑️</button>
        </div>
        <div class="img-resizable" style="width: 300px; height: 250px;">
            ${{d.image_html}}
        </div>
      </div>
    `;
    
    // Safely refresh any newly injected TikZ scripts so the TikzJax MutationObserver processes them
    const newScripts = zone.querySelectorAll('script[type="text/tikz"]');
    newScripts.forEach(s => {{
      const newS = document.createElement('script');
      Array.from(s.attributes).forEach(attr => newS.setAttribute(attr.name, attr.value));
      newS.textContent = s.textContent;
      s.parentNode.replaceChild(newS, s);
    }});

    wrap.style.boxShadow = '';
  }}

  // ─ Image Needs Agent: Mark questions that need visual aids ─
  if (d.type === 'MARK_NEEDS_IMAGE') {{
    const wids = d.wids || [];
    // Inject style once
    if (!document.getElementById('needs-image-styles')) {{
      const s = document.createElement('style');
      s.id = 'needs-image-styles';
      s.innerHTML = `
        .q-wrap.needs-image-flag {{
          # border-left: 4px solid #ef4444 !important;
          # background: linear-gradient(to right, rgba(239,68,68,0.04), transparent 120px) !important;
          # border-radius: 0 6px 6px 0 !important;
        }}
        .q-wrap.needs-image-flag::before {{
          content: '📷 IMAGE SUGGESTED';
          position: absolute;
          top: 4px; right: 8px;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1.5px;
          color: #ef4444;
          text-transform: uppercase;
          opacity: 0.7;
          pointer-events: none;
        }}
      `;
      document.head.appendChild(s);
    }}
    wids.forEach(wid => {{
      const wrap = document.querySelector(`.q-wrap[data-wid="${{wid}}"]`);
      if (wrap) wrap.classList.add('needs-image-flag');
    }});
  }}
}});
</script>
</body>
</html>
"""
    return template

def build_header_html(mode, exam_type, level, subject, term_roman, exam_year, duration, school_name, brand_name, question_count, topic="", logo_b64=None, paper_style="uneb_standard", view_mode="scroll"):
    # Attempt to load using Jinja2
    if jinja_env:
        template = jinja_env.get_template("header.html")
        ps = get_paper_structure(subject, level)
        return template.render(
            mode=mode, exam_type=exam_type, level=level, subject=subject, 
            term_roman=term_roman, exam_year=exam_year, duration=duration, 
            school_name=school_name, brand_name=brand_name, 
            ps=ps, topic=topic, logo_b64=logo_b64
        )
    
    # Fallback legacy implementation
    title_text = f"{exam_type} {term_roman} Examination {exam_year}" if mode == "Exams" else f"{subject} | {topic}"
    
    rows = ["1-10", "11-20", "21-30", "31-40", "41-45", "46-50", "51-55", "TOTAL"]
    exam_rows = "".join([f"<tr><td>{r}</td><td></td><td></td></tr>" for r in rows])
    right_col = f"""<div class="ex-panel"><table><tr><th>Question</th><th>Marks</th><th>EXR'S</th></tr>{exam_rows}</table></div>"""
    
    ps = get_paper_structure(subject, level)
    sec_a_count = ps["sec_a_count"]
    sec_a_marks = ps["sec_a_marks"]
    sec_b_count = ps["sec_b_count"]
    sec_b_marks = ps["sec_b_marks"]
    total_marks = ps["total_marks"]
    official_duration = ps.get("duration", duration) if duration in ("", "2 HR 30 MIN", None) else duration
    sec_b_note = ps.get("sec_b_note", "Attempt all questions in Section B.")
    has_two_sections = sec_b_count > 0

    sec_b_line = f"<li>Section B has {sec_b_count} questions ({sec_b_marks} marks). {sec_b_note}</li>" if has_two_sections else ""

    left_col = f"""<div class="instr-panel">
        <div style="text-align:center; text-decoration:underline; font-weight:900; margin-bottom:10px; font-size:11px;">READ THE FOLLOWING INSTRUCTIONS CAREFULLY BEFORE OPENING</div>
        <ul class="instr-list">
            <li>This paper has {'two sections: A and B' if has_two_sections else 'one section (Section A)'}.</li>
            <li>Section A has {sec_a_count} questions ({sec_a_marks} marks).</li>
            {sec_b_line}
            <li>Total marks for this paper: <strong>{total_marks}</strong>.</li>
            <li>Attempt all questions in both sections.</li>
        </ul>
    </div>"""

    # We skip syllabus table in streaming header to avoid needing all questions beforehand, or we just render an empty one.
    syllabus_table = ""

    # ── DYNAMIC FONT FOR LOWER PRIMARY ──
    import re
    is_lower_primary = False
    if "Primary" in level:
        m = re.search(r'\d+', level)
        if m and int(m.group()) <= 4:
            is_lower_primary = True
    elif any(x in level for x in ["Nursery", "ECD", "Baby", "Middle", "Top"]):
        is_lower_primary = True
        
    font_css = '"Comic Sans MS", "Chalkboard SE", "Comic Neue", sans-serif' if is_lower_primary else '"Times New Roman", Times, serif'
    line_height = '1.9' if is_lower_primary else '1.5'

    header_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<style>
:root {{
  --p: #800020;
  --s: #1e293b;
  --bg: #f8fafc;
  --br-l: 12px;
}}
* {{ box-sizing: border-box; transition: background 0.3s ease; margin: 0; padding: 0; }}
body {{ background: var(--bg); font-family: 'Outfit', sans-serif; padding: 40px 0 120px 0; display: flex; flex-direction: column; align-items: center; gap: 30px; min-height: 100vh; }}
.page {{ background: white; width: 210mm; min-height: 297mm; padding: 20mm; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05); border-radius: 2px; overflow: hidden; color: #1e293b; line-height: {line_height}; font-family: {font_css}; }}
.brand-h {{ position: relative; z-index: 1; border-bottom: 4px solid var(--p); padding-bottom: 15px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: flex-end; }}
.brand-name {{ font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 900; font-style: italic; color: var(--p); letter-spacing: -0.02em; }}
.doc-t {{ text-transform: uppercase; font-weight: 900; letter-spacing: 0.2em; font-size: 10px; color: #64748b; }}
.idx-grid {{ display: flex; gap: 4px; margin-top: 10px; }}
.idx-box {{ width: 24px; height: 32px; border: 1.5px solid #1e293b; border-radius: 4px; }}
.cand-box {{ background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 25px 0; font-size: 13px; }}
.cand-line {{ border-bottom: 2px dotted #000; flex: 1; margin-left: 10px; height: 18px; }}
.top-sec {{ display: grid; grid-template-columns: 1fr 280px; gap: 30px; margin-bottom: 30px; }}
.instr-panel {{ background: #fff; border: 2px solid #000; padding: 15px; border-radius: 0px; font-size: 11px; }}
.instr-list {{ margin-left: 15px; }}
.instr-list li {{ margin-bottom: 4px; padding-left: 5px; }}
.ex-panel table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
.ex-panel th, .ex-panel td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
.ex-panel th {{ background: #f8fafc; text-transform: uppercase; font-weight: 900; }}
/* Add printing styles */
@media print {{
    body {{ background: none; padding: 0; margin: 0; align-items: flex-start; display: block; }}
    .page {{ box-shadow: none; margin: 0; padding: 15mm; min-height: 100%; width: 100%; page-break-after: always; }}
    #ans-key-container {{ display: none !important; }}
}}
.marking-mode #ans-key-container {{ display: block !important; }}
.ref-mode #syllabus-container {{ display: block !important; }}
</style>
</head>
<body>
<div class="page" id="page-1">
<div class="brand-h">
    <div>
        <div class="brand-name">{brand_name}</div>
        <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; margin-top: 5px;">Quality Assessment Engine</div>
    </div>
    <div style="text-align: right;">
        <div class="doc-t">{title_text}</div>
        <div style="font-size: 14px; font-weight: 700; margin-top: 5px; color: var(--s);">{subject}</div>
        <div style="font-size: 12px; color: #64748b;">Duration: {official_duration}</div>
    </div>
</div>
<div class="top-sec">
    {left_col}
    {right_col}
</div>
<div class="cand-box">
    <div style="display:flex; align-items:flex-end; margin-bottom:15px;">
        <span style="font-weight:900; text-transform:uppercase; font-size:11px; letter-spacing:1px; color:#64748b;">Index No:</span>
        <div class="idx-grid" style="margin-left:15px; margin-top:0;">
            {"<div class='idx-box'></div>"*9}
        </div>
    </div>
    <div style="display:flex; gap:20px; align-items:flex-end;">
        <div style="display:flex; flex:1; align-items:flex-end;"><span style="font-weight:900; text-transform:uppercase; font-size:11px; letter-spacing:1px; color:#64748b;">Candidate's Name:</span><div class="cand-line"></div></div>
        <div style="display:flex; flex:1; align-items:flex-end;"><span style="font-weight:900; text-transform:uppercase; font-size:11px; letter-spacing:1px; color:#64748b;">Candidate's Signature:</span><div class="cand-line"></div></div>
    </div>
</div>
<div id="syllabus-container" style="display:none;">{syllabus_table}</div>
"""
    return header_html

def build_question_html(mode, q, subject, level, is_two_col_math=False, is_marking_guide=False):
    if mode != "Exams":
        return ""
        
    num = q.get("number", "")
    text = q.get("text") or ""
    marks = q.get("marks", "")
    tikz = q.get("tikz_code")
    ans = q.get("answer", "")
    
    # ── HOTFIX: Extract inadvertently injected TikZ from answer ──
    if "**Expected Construction:**" in str(ans):
        parts = ans.split("**Expected Construction:**")
        ans = parts[0].strip()
        if len(parts) > 1 and not q.get("marking_tikz_code"):
            q["marking_tikz_code"] = parts[1].strip()
    
    q_type = q.get("type", "short_answer")
    options = q.get("options", [])
    sub_questions = q.get("sub_questions", [])
    fill_words = q.get("fill_words", [])
    match_left = q.get("match_left", [])
    match_right = q.get("match_right", [])
    math_top = q.get("math_top", "")
    math_bottom = q.get("math_bottom", "")
    math_op = q.get("math_op", "+")
    
    working_columns = q.get("working_columns", [])
    if not working_columns and q.get("working_steps"):
        # Fallback for old schema
        working_columns = [[{"text": step.get("text", step) if isinstance(step, dict) else step, "mark_code": step.get("mark_code") if isinstance(step, dict) else None, "is_heading": False} for step in q.get("working_steps", [])]]
    
    key_phrases_to_underline = q.get("key_phrases_to_underline", [])
    alternative_answers = q.get("alternative_answers", [])
    examiner_notes = q.get("examiner_notes", "")
    marking_tikz_code = q.get("marking_tikz_code")
    
    safe_text = text.replace('"', '&quot;').replace("'", "&#39;")
    
    if is_marking_guide and key_phrases_to_underline:
        for phrase in key_phrases_to_underline:
            if phrase in text:
                underlined_phrase = f'<span style="border-bottom: 2px solid #0066cc;">{phrase}</span>'
                text = text.replace(phrase, underlined_phrase)
    is_drawing_question = q.get("needs_student_drawing", False)
    diagram_url = q.get("diagram_url", None)
    
    if jinja_env:
        try:
            marks_int = int(marks)
        except:
            marks_int = 1
            
        is_math = any(s in subject.lower() for s in ["math", "mathematics", "numeracy"])
        
        tmpl_name = "marking_guide_question.html" if is_marking_guide else "question.html"
        template = jinja_env.get_template(tmpl_name)
        return template.render(
            num=num,
            text=text,
            safe_text=safe_text,
            subject=subject,
            level=level,
            q_type=q_type,
            options=options,
            sub_questions=sub_questions,
            fill_words=fill_words,
            match_left=match_left,
            match_right=match_right,
            math_top=math_top,
            math_bottom=math_bottom,
            math_op=math_op,
            is_drawing_question=is_drawing_question,
            tikz=tikz,
            marks=marks_int,
            is_two_col_math=is_two_col_math,
            is_math=is_math,
            diagram_url=diagram_url,
            answer=ans,
            working_columns=working_columns,
            alternative_answers=alternative_answers,
            examiner_notes=examiner_notes,
            marking_tikz_code=marking_tikz_code
        )
    else:
        # Fallback if templates directory is missing
        parsed_html = f"<div class='q-wrap' data-qtext='{safe_text}' data-subject='{subject}' data-level='{level}' style='margin-bottom:25px; clear:both; position:relative; border-radius:6px; transition: box-shadow 0.2s;'>"
        parsed_html += f"  <div style='font-size:15px; display:flex; align-items:flex-start; margin-bottom:10px;'><span>{num}. &nbsp;</span><span style='flex:1;'>{text}</span></div>"
        
        if q_type == "mcq" and options:
            parsed_html += f"<div style='margin-left: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 14px;'>"
            for opt in options:
                parsed_html += f"<div>{opt}</div>"
            parsed_html += "</div>"
            
        if q_type == "fill_blank" and fill_words:
            parsed_html += f"<div style='margin-left: 20px; display: flex; flex-direction: column; gap: 10px; margin-top: 10px; font-size: 16px; font-family: monospace; letter-spacing: 2px;'>"
            for fw in fill_words:
                parsed_html += f"<div>{fw}</div>"
            parsed_html += "</div>"
            
        if q_type == "matching" and match_left and match_right:
            parsed_html += f"<div style='margin-left: 20px; display: flex; justify-content: space-around; margin-top: 20px; margin-bottom: 20px; font-size: 15px;'>"
            parsed_html += "<div style='display: flex; flex-direction: column; gap: 25px;'>"
            for left in match_left:
                parsed_html += f"<div>{left}</div>"
            parsed_html += "</div>"
            parsed_html += "<div style='display: flex; flex-direction: column; gap: 25px;'>"
            for right in match_right:
                parsed_html += f"<div>{right}</div>"
            parsed_html += "</div>"
            parsed_html += "</div>"
            
        if q_type == "vertical_math" and math_top and math_bottom:
            parsed_html += f"<div style='margin-left: 40px; margin-top: 15px; font-size: 18px; font-family: monospace;'>"
            parsed_html += f"<div style='text-align: right; width: 60px;'>{math_top}</div>"
            parsed_html += f"<div style='text-align: right; width: 60px; position: relative;'> <span style='position: absolute; left: 0;'>{math_op}</span> {math_bottom}</div>"
            parsed_html += f"<div style='border-top: 2px solid #000; border-bottom: 2px solid #000; width: 60px; height: 30px; margin-top: 5px;'></div>"
            parsed_html += "</div>"
        
        if q_type == "structured" and sub_questions:
            parsed_html += f"<div style='margin-left: 20px; margin-top: 10px; font-size: 14px;'>"
            for sub in sub_questions:
                sub_label = sub.get("label", "")
                sub_text = sub.get("text", "")
                sub_marks = sub.get("marks", "")
                parsed_html += f"<div style='display: flex; margin-bottom: 8px;'><span>{sub_label} &nbsp;</span><span style='flex:1;'>{sub_text}</span><span style='font-weight:bold;'>({sub_marks} marks)</span></div>"
                parsed_html += f"<div style='border-bottom:2px dotted #000; margin: 20px 0 20px 0; height: 1px;'></div>"
            parsed_html += "</div>"

        if is_drawing_question:
            parsed_html += f"  <div style='border:1px solid #000; height:350px; margin:15px 0 25px 0; position:relative;'><span style='position:absolute; top:5px; left:5px; font-size:8px; opacity:0.3; text-transform:uppercase;'>STUDENT DRAWING SPACE</span></div>"
        else:
            if tikz:
                if "begin{tikzpicture}" in tikz:
                    parsed_html += f"  <div class='ill-box' style='width:100%; text-align:center; margin:20px auto; display:block;'>{tikz}</div>"
                else:
                    parsed_html += f"  <div class='ill-box' style='text-align:center; padding:15px; width:100%;'>{tikz}</div>"
            if not (q_type == "structured" and sub_questions) and q_type not in ["vertical_math", "matching", "fill_blank"]:
                parsed_html += f"  <div style='border-bottom:2px dotted #000; margin:25px 0 15px 25px; height:1px;'></div>"
        
        parsed_html += f"  <div class='q-img-zone'></div>"
        parsed_html += f"</div>"
        return parsed_html

def build_answer_row_html(q):
    num = q.get("number", "")
    ans = q.get("answer", "")
    marks = q.get("marks", "")
    return f"<tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 10px; font-weight:900;'>Q{num}</td><td style='padding: 10px;'>{ans}</td><td style='padding: 10px; font-weight:900; color:var(--p); text-align:center;'>{marks}</td></tr>"

def build_footer_html(answer_key_rows_html):
    footer_html = f"""
</div> <!-- End of Page 1 -->

<div id="ans-key-container" style="display:none; width: 210mm; margin: 0 auto; background: white; padding: 20mm; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-radius: 2px;">
    <h2 style="color: var(--p); border-bottom: 2px solid var(--p); padding-bottom: 10px; margin-bottom: 20px;">Confidential Marking Guide</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
            <tr>
                <th style="padding: 12px; text-align: left; width: 60px;">No.</th>
                <th style="padding: 12px; text-align: left;">Expected Answer / Value Points</th>
                <th style="padding: 12px; text-align: center; width: 80px;">Marks</th>
            </tr>
        </thead>
        <tbody id="answer-tbody">
            {answer_key_rows_html}
        </tbody>
    </table>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {{
    renderMathInElement(document.body, {{
      delimiters: [
          {{left: '$$', right: '$$', display: true}},
          {{left: '$', right: '$', display: false}},
          {{left: '\\\\(', right: '\\\\)', display: false}},
          {{left: '\\\\[', right: '\\\\]', display: true}}
      ],
      throwOnError : false
    }});

    // ── Assign stable wids to all q-wrap elements (for MARK_NEEDS_IMAGE targeting) ──
    document.querySelectorAll('.q-wrap').forEach(function(wrap, idx) {{
      if (!wrap.getAttribute('data-wid')) {{
        wrap.setAttribute('data-wid', 'qw-' + idx);
      }}
    }});

    // ── Signal parent that page is ready ──
    window.parent.postMessage({{ type: 'EDUQUEST_READY' }}, '*');
}});

// 📡 FULL MESSAGE RELAY FROM REACT PARENT
window.addEventListener('message', (event) => {{
  const d = event.data;

  // ─ Inject image into question zone ─
  if (d.type === 'INJECT_IMAGE') {{
    const wrap = document.querySelector(`.q-wrap[data-wid="${{d.wid}}"]`);
    if (!wrap) return;

    if (!document.getElementById('interactive-img-styles')) {{
      const style = document.createElement('style');
      style.id = 'interactive-img-styles';
      style.innerHTML = `
        .img-wrapper {{ position: relative; transition: all 0.2s; z-index: 10; display: block; clear: both; margin: 10px auto; }}
        .img-wrapper.float-right {{ float: right; margin: 5px 0 5px 20px; clear: none; }}
        .img-wrapper.float-left {{ float: left; margin: 5px 20px 5px 0; clear: none; }}
        .img-wrapper.align-center {{ margin: 15px auto; display: flex; justify-content: center; width: max-content; }}
        .img-toolbar {{ position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: white; border: 1px solid #ccc; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border-radius: 8px; padding: 4px; display: flex; gap: 4px; opacity: 0; pointer-events: none; transition: opacity 0.2s, transform 0.2s; white-space: nowrap; z-index: 20; }}
        .img-wrapper:hover .img-toolbar {{ opacity: 1; pointer-events: auto; transform: translateX(-50%) translateY(5px); }}
        .img-toolbar button {{ background: none; border: none; cursor: pointer; font-size: 11px; padding: 4px 8px; border-radius: 4px; display: flex; align-items: center; gap: 4px; font-weight: bold; color: #333; }}
        .img-toolbar button:hover {{ background: #f1f5f9; }}
        .img-resizable {{ resize: both; overflow: hidden; min-width: 150px; min-height: 150px; max-width: 100%; padding: 8px; border: 2px dashed transparent; border-radius: 6px; background: #fff; }}
        .img-wrapper:hover .img-resizable {{ border-color: #cbd5e1; background: #f8fafc; }}
        .img-resizable svg, .img-resizable img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
      `;
      document.head.appendChild(style);
    }}

    let zone = wrap.querySelector('.q-img-zone');
    if (!zone) {{
      zone = document.createElement('div');
      zone.className = 'q-img-zone';
      wrap.insertBefore(zone, wrap.firstChild);
    }}

    const imgId = 'img-' + Math.random().toString(36).substr(2, 9);
    zone.innerHTML = `
      <div id="${{imgId}}" class="img-wrapper align-center">
        <div class="img-toolbar">
          <button onclick="document.getElementById('${{imgId}}').className='img-wrapper float-left'" title="Move Left">◧ Left</button>
          <button onclick="document.getElementById('${{imgId}}').className='img-wrapper align-center'" title="Center">◫ Center</button>
          <button onclick="document.getElementById('${{imgId}}').className='img-wrapper float-right'" title="Move Right">◨ Right</button>
          <div style="width:1px; background:#e2e8f0; margin:0 2px;"></div>
          <button onclick="document.getElementById('${{imgId}}').remove()" style="color:#ef4444;" title="Delete">🗑️</button>
        </div>
        <div class="img-resizable" style="width:300px; height:250px;">
          ${{d.image_html}}
        </div>
      </div>
    `;

    // Re-process any TikZ scripts in the injected content
    zone.querySelectorAll('script[type="text/tikz"]').forEach(s => {{
      const newS = document.createElement('script');
      Array.from(s.attributes).forEach(attr => newS.setAttribute(attr.name, attr.value));
      newS.textContent = s.textContent;
      s.parentNode.replaceChild(newS, s);
    }});

    wrap.style.boxShadow = '';
    // Remove the needs-image flag once an image has been injected
    wrap.classList.remove('needs-image-flag');
  }}

  // ─ View mode toggle ─
  if (d.type === 'EDUQUEST_VIEW_MODE') {{
    const mode = d.mode;
    const allPages = document.querySelectorAll('.page');
    const markingEl = document.getElementById('ans-key-container');
    allPages.forEach(p => {{ if(p) p.style.display = 'none'; }});
    if (mode === 'marking') {{
      if (markingEl) markingEl.style.display = 'block';
    }} else {{
      allPages.forEach(p => {{ if(p) p.style.display = 'block'; }});
      if (markingEl) markingEl.style.display = 'none';
    }}
  }}

  // ─ Image Needs Agent: mark questions needing visuals ─
  if (d.type === 'MARK_NEEDS_IMAGE') {{
    const wids = d.wids || [];
    if (!document.getElementById('needs-image-styles')) {{
      const s = document.createElement('style');
      s.id = 'needs-image-styles';
      s.innerHTML = `
        .q-wrap.needs-image-flag {{
          border-left: 4px solid #ef4444 !important;
          background: linear-gradient(to right, rgba(239,68,68,0.04), transparent 120px) !important;
          border-radius: 0 6px 6px 0 !important;
        }}
        .q-wrap.needs-image-flag::before {{
          content: '📷 IMAGE SUGGESTED';
          position: absolute;
          top: 4px; right: 8px;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1.5px;
          color: #ef4444;
          text-transform: uppercase;
          opacity: 0.7;
          pointer-events: none;
        }}
      `;
      document.head.appendChild(s);
    }}
    wids.forEach(wid => {{
      const wrap = document.querySelector(`.q-wrap[data-wid="${{wid}}"]`);
      if (wrap) wrap.classList.add('needs-image-flag');
    }});
  }}
}});
</script>
</body>
</html>
"""
    return footer_html

