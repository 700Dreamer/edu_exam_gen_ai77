import json
from core.paper_structure import get_paper_structure


def build_full_html(mode, exam_type, level, subject, term_roman, exam_year, duration, school_name, brand_name, question_count, content_raw, topic="", logo_b64=None, paper_style="uneb_standard", view_mode="scroll"):
    """
    Constructs the full HTML document string, utilizing strict JSON outputs to guarantee formatting.
    """
    
    title_text = f"{exam_type} {term_roman} Examination {exam_year}" if mode == "Exams" else f"{subject} | {topic}"
    
    # ── BUILD SCORING TABLE ──
    rows = ["1-10", "11-20", "21-30", "31-40", "41-45", "46-50", "51-55", "TOTAL"]
    exam_rows = "".join([f"<tr><td>{r}</td><td></td><td></td></tr>" for r in rows])

    right_col = f"""<div class="ex-panel"><table><tr><th>Question</th><th>Marks</th><th>EXR'S</th></tr>{exam_rows}</table></div>"""
    
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
        <div style="text-align:center; text-decoration:underline; font-weight:900; margin-bottom:10px; font-size:11px;">READ THE FOLLOWING INSTRUCTIONS CAREFULLY BEFORE OPENING</div>
        <ul class="instr-list">
            <li>This paper has {'two sections: A and B' if has_two_sections else 'one section (Section A)'}.</li>
            <li>Section A has {sec_a_count} questions ({sec_a_marks} marks).</li>
            {sec_b_line}
            <li>Total marks for this paper: <strong>{total_marks}</strong>.</li>
            <li>Attempt all questions in both sections.</li>
            <li>All answers must be written in black or blue ink.</li>
            <li>Only diagrams must be drawn in pencil.</li>
            <li>Any handwriting that cannot be easily read may lead to loss of marks.</li>
            <li>Unnecessary alteration of work will lead to loss of marks.</li>
            <li>Do not fill in boxes reserved for examiner's use only.</li>
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
        answer_key_html = ""
        
        # ── SCENARIO NARRATIVE (If Present) ──
        scenario = data.get("scenario_text")
        if scenario:
            parsed_html += f"<div style='background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 16px; padding: 25px; margin-bottom: 40px; line-height: 1.8; font-style: italic; color: var(--s); box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);'>"
            parsed_html += f"  <div style='font-size: 10px; font-weight: 900; color: var(--p); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 2px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;'>Competency Scenario Context</div>"
            parsed_html += f"  <div style='font-size: 16px; font-weight: 500;'>{scenario}</div>"
            parsed_html += f"</div>"

        if mode == "Exams":
            for q in data.get("questions", []):
                num = q.get("number", "")
                text = q.get("text", "")
                marks = q.get("marks", "")
                tikz = q.get("tikz_code")
                ans = q.get("answer", "")
                
                # Build Question UI — wrapped in interactive container
                safe_text = text.replace('"', '&quot;').replace("'", "&#39;")
                parsed_html += f"<div class='q-wrap' data-qtext='{safe_text}' data-subject='{subject}' data-level='{level}' style='margin-bottom:25px; clear:both; position:relative; border-radius:6px; transition: box-shadow 0.2s;'>"
                parsed_html += f"  <div style='font-size:15px; display:flex; align-items:flex-start; margin-bottom:10px;'><span>{num}. &nbsp;</span><span style='flex:1;'>{text}</span></div>"
                
                # AI-Assessed Semantic Drawing Flag
                is_drawing_question = q.get("needs_student_drawing", False)
                
                if is_drawing_question:
                    parsed_html += f"  <div style='border:1px solid #000; height:350px; margin:15px 0 25px 0; position:relative;'><span style='position:absolute; top:5px; left:5px; font-size:8px; opacity:0.3; text-transform:uppercase;'>STUDENT DRAWING SPACE</span></div>"
                else:
                    if tikz:
                        if "<img" in str(tikz).lower() or "<svg" in str(tikz).lower():
                            parsed_html += f"  <div class='ill-box' style='width:100%; text-align:center; margin:20px auto; display:block;'>{tikz}</div>"
                        else:
                            parsed_html += f"  <div class='ill-box' style='text-align:center; padding:15px; width:100%;'>{tikz}</div>"
                    parsed_html += f"  <div style='border-bottom:1px dotted #000; margin:15px 0 10px 25px; height:1px;'></div>"
                
                # Image injection target zone
                parsed_html += f"  <div class='q-img-zone' ></div>"
                parsed_html += f"</div>"
                
                # Append to Hidden Answer Key
                answer_key_html += f"<tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 10px; font-weight:900;'>Q{num}</td><td style='padding: 10px;'>{ans}</td><td style='padding: 10px; font-weight:900; color:var(--p); text-align:center;'>{marks}</td></tr>"
                
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
        answer_key_html = "<tr><td colspan='3'>JSON Error. Manual marking required.</td></tr>"

    # ── SAFEGUARD FOR JAVASCRIPT INJECTION ──
    js_content = parsed_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("</script>", "<\\/script>")
    js_answers = answer_key_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("</script>", "<\\/script>")

    template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=Playfair+Display:ital,wght@1,900&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css" rel="stylesheet">
<link rel="stylesheet" type="text/css" href="https://tikzjax.com/v1/fonts.css">
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
  line-height: 1.5;
  font-family: "Times New Roman", Times, serif;
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
.cand-line {{ border-bottom: 1px dashed #94a3b8; flex: 1; margin-left: 10px; height: 18px; }}

.col-l {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 30px; margin-bottom: 30px; }}
.instr-panel {{ font-size: 11.5px; color: #475569; line-height: 1.6; }}
.ex-panel table {{ width: 100%; border-collapse: collapse; font-size: 10px; border-radius: 8px; overflow: hidden; }}
.ex-panel th {{ background: var(--p); color: white; padding: 6px; text-transform: uppercase; }}
.ex-panel td {{ border: 1px solid #e2e8f0; padding: 6px; text-align: center; height: 26px; }}

.body-c {{ font-size: 15.5px; line-height: 2.2; white-space: pre-wrap; font-family: "Times New Roman", Times, serif !important; }}
.pgn {{ position: absolute; bottom: 15mm; left: 0; width: 100%; text-align: center; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; }}

/* ── ILLUSTRATION & DIAGRAM STYLING ── */
.ill-box img {{ max-width: 400px; height: auto; border-radius: 8px; margin: 0 auto; display: block; }}
.ill-box svg {{ max-width: 400px; height: auto; display: block; margin: 0 auto; }}
.ill-box svg * {{ stroke-width: 2px !important; }}

/* ── REAL PAPER (UNEB) PROTOCOL ── */
.tmpl-uneb {{ font-family: "Times New Roman", serif !important; }}
.tmpl-uneb.page {{ border: 6px double #000 !important; box-shadow: none !important; border-radius: 0 !important; }}
.tmpl-uneb .brand-h {{ flex-direction: column !important; align-items: center !important; text-align: center !important; border-bottom: 2px solid #000 !important; }}
.tmpl-uneb .brand-name {{ font-family: serif !important; text-transform: uppercase !important; font-size: 32px !important; font-style: normal !important; color: #000 !important; }}
.tmpl-uneb .doc-t {{ color: #000 !important; font-size: 14px !important; letter-spacing: 4px !important; margin-top: 10px !important; }}
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
  .style-panel, .panel-toggle, #preview-toolbar {{ display: none !important; }} 
  body {{ padding: 0; background: white; }}
  .page {{ box-shadow: none !important; border: none !important; margin: 0 !important; page-break-after: always !important; }}
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
    <div class="doc-t" style="margin-bottom:2px;">{title_text}</div>
    <div class="brand-name">{level} - {subject}</div>
    <div style="width:100%; text-align:right; font-weight:900; font-size:16px; margin-top:5px;">TIME: {duration}</div>
  </div>

  <div style="display:flex; align-items:center; gap:10px; margin-top:10px;">
    <div style="font-weight:900; font-size:14px;">INDEX NO:</div>
    <div class="idx-grid">
        <div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div>
        <div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div><div class="idx-box"></div>
    </div>
  </div>

  <div class="cand-box">
    <div style="display:flex; align-items:flex-end;"><b>NAME</b> <span style="margin-left:25px;">:</span> <div class="cand-line"></div></div>
    <div style="display:flex; align-items:flex-end;"><b>SCHOOL</b> <span style="margin-left:15px;">:</span> <div class="cand-line"></div></div>
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
    <b style="text-decoration:underline; font-size:14px;">SECTION A (40 Marks)</b>
  </div>

  <div class="body-c" id="content-body">
    {parsed_html}
  </div>
  <div class="pgn">Page 2 of 2 — End of Release</div>
</div>

<!-- PAGE 3: MARKING GUIDE (TEACHER ONLY) -->
<div class="page" id="marking-guide-page" style="display: none;">
  <div class="brand-h">
    <div>
      <div class="brand-name">{brand_name}</div>
      <div style="font-size:11px; font-weight:900; letter-spacing:5px;">CONFIDENTIAL</div>
    </div> 
  </div>
  <div class="doc-t" style="background:#800020;">TEACHER'S MARKING GUIDE</div>
  <div style="color:var(--p); font-weight:900; text-align:center; margin-bottom:20px; font-size:12px;">THIS DOCUMENT CONTAINS OFFICIAL ANSWERS. DO NOT DISTRIBUTE TO CANDIDATES.</div>
  
  <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
    <thead>
      <tr style="background:var(--s); color:white;">
        <th style="padding: 10px; width:50px;">QN</th>
        <th style="padding: 10px; text-align:left;">EXPECTED ANSWER / WORKING</th>
        <th style="padding: 10px; width:80px;">SCORE</th>
      </tr>
    </thead>
    <tbody id="answer-body">
      {answer_key_html}
    </tbody>
  </table>
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
  const tz = document.createElement('script');
  tz.src = 'https://tikzjax.com/v1/tikzjax.js';
  document.head.appendChild(tz);
  
  // 3. Force KaTeX math rendering
  if (window.renderMathInElement) {{
    renderMathInElement(document.body, {{
      delimiters: [ 
        {{left: "$$", right: "$$", display: true}},
        {{left: "$", right: "$", display: false}} 
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
    
    // Virtual A4 height in pixels (roughly 297mm at 96dpi)
    const A4_HEIGHT = 1050; // Slightly less than 1122 to allow for some breathing room
    
    let currentPage = contentP;
    let currentBody = bodyC;
    
    // Clear the original body to redistribute
    bodyC.innerHTML = '';
    
    for(let i=0; i<items.length; i++) {{
        let item = items[i];
        currentBody.appendChild(item);
        
        // Check if current page overflows
        if (currentPage.scrollHeight > A4_HEIGHT) {{
            // If this is the only item on the page and it's too big, we have to keep it here 
            // but we'll still start a new page for the next item.
            if (currentBody.children.length > 1) {{
                // Create new page
                const newPage = document.createElement('div');
                newPage.className = mainPage.className;
                newPage.style.marginTop = '40px';
                
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
            }}
        }}
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
    wrap.style.boxShadow = '';
  }}
}});
</script>
</body>
</html>
"""
    return template
