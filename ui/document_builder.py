import json


def build_full_html(mode, exam_type, level, subject, term_roman, exam_year, duration, school_name, brand_name, question_count, content_raw, topic="", logo_b64=None):
    """
    Constructs the full HTML document string, utilizing strict JSON outputs to guarantee formatting.
    """
    
    title_text = f"{exam_type} {term_roman} Examination {exam_year}" if mode == "Exams" else f"{subject} | {topic}"
    
    # ── BUILD SCORING TABLE ──
    exam_rows = ""
    for i in range(1, question_count + 1, 10):
        end = min(i + 9, question_count)
        exam_rows += f"<tr><td>{i}-{end}</td><td></td><td></td></tr>"
    exam_rows += "<tr class='total-row'><td><strong>TOTAL</strong></td><td></td><td></td></tr>"

    right_col = f"""<div class="ex-panel"><div class="time-badge">{duration}</div><div class="ex-label">OFFICIAL SCORING</div><table><tr><th>RANGE</th><th>MARKS</th><th>EXR</th></tr>{exam_rows}</table></div>"""
    sa, sb = round(question_count*0.6), round(question_count*0.4)
    left_col = f"""<div class="instr-panel"><div class="psec-title">CANDIDATE INSTRUCTIONS</div><ul><li>Section A: {sa} QNs. Section B: {sb} QNs.</li><li>All textual responses must use Dark Ink.</li></ul></div>"""

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
                
                # Build Question UI
                parsed_html += f"<div style='margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1.5px dashed #e2e8f0;'>"
                parsed_html += f"  <div style='font-weight: 900; font-size: 16px; margin-bottom: 12px; display: flex; justify-content: space-between;'><span>Q{num}. <span style='font-weight: 400;'>{text}</span></span><span style='font-size:12px; font-weight:900; color:var(--p); padding-left:15px; white-space:nowrap;'>[{marks} Marks]</span></div>"
                if tikz:
                    parsed_html += f"  <div style='text-align:center; padding: 15px;'>{tikz}</div>"
                
                # Dynamic drawing space for "Draw/Construct" questions
                draw_keywords = ["draw", "construct", "sketch", "graph", "plot"]
                if any(k in text.lower() for k in draw_keywords) and not tikz:
                    parsed_html += f"  <div style='border: 1px solid #cbd5e1; height: 250px; margin: 15px 0; border-radius: 8px; position: relative;'><span style='position:absolute; top:10px; left:10px; font-size:10px; color:#94a3b8; font-weight:900;'>DRAWING / CONSTRUCTION SPACE</span></div>"
                else:
                    parsed_html += f"  <div style='letter-spacing: 3px; overflow:hidden; white-space:nowrap; margin-top:20px;'>.......................................................................................................................................................................</div>"
                
                parsed_html += f"</div>"
                
                # Append to Hidden Answer Key
                answer_key_html += f"<tr style='border-bottom: 1px solid #e2e8f0;'><td style='padding: 10px; font-weight:900;'>Q{num}</td><td style='padding: 10px;'>{ans}</td><td style='padding: 10px; font-weight:900; color:var(--p); text-align:center;'>{marks}</td></tr>"
                
        else:
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
  --p: #800020; --s: #1e293b; --g: #f8fafc;
  --logo-f: 'Outfit'; --br-l: 0px; --logo-s: 42px; --h-size: 20px; --watermark: 0.02;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Outfit', sans-serif; background: transparent; padding-right: 50px; color: #1e293b; }}

/* ── STUDIO SIDEBAR UI ── */
.style-panel {{ position: fixed; top: 0; right: -350px; width: 330px; height: 100vh; background: #0f172a; color: white; transition: right 0.4s; padding: 30px 20px; z-index: 99999; box-shadow: -10px 0 40px rgba(0,0,0,0.5); overflow-y: auto; }}
.style-panel.open {{ right: 0; }}
.panel-toggle {{ position: fixed; top: 20px; right: 20px; background: var(--p); color: white; width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 100000; }}
.p-title {{ font-weight: 900; font-size: 13px; text-transform: uppercase; margin-bottom: 25px; border-left: 4px solid var(--p); padding-left: 10px; }}
.style-group {{ margin-bottom: 25px; background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; }}
.tmpl-btn {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: white; cursor: pointer; width: 100%; margin-bottom: 8px; }}

/* ── DOCUMENT PAGE STRUCTURE ── */
.page {{ width: 100%; max-width: 820px;  margin: 40px auto; padding: 16mm; position: relative; border-left: var(--br-l) solid var(--p); }}
.page::after {{ content: "{brand_name}"; position: absolute; top:50%; left:50%; transform:translate(-50%,-50%) rotate(-45deg); font-size: 10rem; font-weight: 900; opacity: var(--watermark); pointer-events: none; }}
.brand-h {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; }}
.tmpl-classic .brand-h {{ flex-direction: column; align-items: center; border-bottom: 4px double #000; padding-bottom: 5px; }}
.brand-name {{ font-family: var(--logo-f); font-size: var(--logo-s); font-weight: 900; color: var(--p); line-height: 1; }}
.brand-logo {{ height: 60px; max-width: 150px; object-fit: contain; margin-bottom: 10px; }}
.brand-h-left {{ display: flex; flex-direction: column; }}
.sh-box {{ background: var(--p); color: white; padding: 12px 20px; border-radius: 12px; text-align: center; }}
.tmpl-classic .sh-box {{ display: none; }}
.doc-t {{ background: var(--s); color: white; padding: 16px; border-radius: 12px; font-size: var(--h-size); font-weight: 900; text-align: center; margin-bottom: 30px; }}
.tmpl-classic .doc-t {{ background: none; color: #000; font-size: 24px; text-decoration: underline; margin: 15px 0; }}
.nc-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
.nc-card {{ border: 2px solid #e2e8f0; border-radius: 12px; padding: 15px; }}
.col-l {{ display: flex; gap: 30px; margin-bottom: 40px; }}
.instr-panel {{ flex: 1.2; background: #fffcf0; border: 2px solid #fde68a; padding: 20px; border-radius: 16px; font-size: 13.5px; }}
.ex-panel {{ flex: 0.8; background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 16px; padding: 15px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
th, td {{ border: 2px solid #cbd5e1; padding: 8px; text-align: center; }}
.body-c {{ font-size: 15.5px; line-height: 2.2; white-space: pre-wrap; }}
.body-c svg {{ max-width: 100%; max-height: 350px; width: auto; height: auto; display: block; margin: 25px auto; overflow: hidden; object-fit: contain; }}
.pgn {{ position: absolute; bottom: 10mm; left: 0; right: 0; text-align: center; color: #94a3b8; font-size: 10px; font-weight: 900; letter-spacing: 3px; }}
.qrc {{ position: absolute; bottom: 12mm; right: 18mm; width: 60px; height: 60px; filter: grayscale(1); opacity: 0.3; }}
@media print {{ .style-panel, .panel-toggle {{ display: none; }} .page {{ border-top: none; box-shadow: none; }} }}
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
  </div>
  <div style="font-size:10px; color:#64748b; margin-bottom:10px; font-weight:700;">WATERMARK INTENSITY</div>
  <input type="range" min="0" max="0.1" step="0.01" value="0.02" style="width:100%;" oninput="sv('--watermark',this.value)">
  <button class="tmpl-btn" style="background:var(--p); color:white; padding:15px; border:none; border-radius:8px; margin-top:20px; font-weight:900;" onclick="window.print()">PRINT FINAL DOCUMENT</button>
</div>

<!-- PAGE 1: HEADER -->
<div class="page" id="mainP">
  <div class="brand-h">
    <div class="brand-h-left">
      {f'<img src="data:image/png;base64,{logo_b64}" class="brand-logo">' if logo_b64 else ''}
      <div class="brand-name" id="liveB">{brand_name}</div>
      <div style="font-size:11px; font-weight:900; letter-spacing:5px; margin-top:5px;">EXAMINATIONS SERVICES</div>
    </div> 
    <div class="sh-box"><div>YEAR</div><div style="font-size:24px; font-weight:900;">{exam_year}</div></div>
  </div>
  <div class="doc-t">{title_text}</div>
  <div style="display:flex; justify-content:space-between; font-weight:900; font-size:16px; margin-bottom:15px;">
    <span>{level} &nbsp;–&nbsp; {subject}</span>
    <span>TIME: 2 HR 30 MINUTES</span>
  </div>
  <div class="nc-grid">
    <div class="nc-card"><b>NAME</b></div>
    <div class="nc-card"><b>BRANCH / SCHOOL</b></div>
  </div>
  <div class="col-l">{left_col}{right_col}</div>
  <div class="pgn">Page 1 of 2 — Official release certified by EduQuest</div>
  <img class="qrc" src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Verify-{brand_name}">
</div>

<!-- PAGE 2: CONTENT -->
<div class="page">
  <div class="brand-logo" style="opacity:0.2; position:absolute; top:20px; right:20px; height:40px;">
    {f'<img src="data:image/png;base64,{logo_b64}" style="height:100%">' if logo_b64 else ''}
  </div>
  <div class="body-c" id="content-body"></div>
  <div class="pgn">Page 2 of 2 — End of Release</div>
</div>

<!-- PAGE 3: MARKING GUIDE (TEACHER ONLY) -->
<div class="page" id="marking-guide-page" style="display: {'block' if mode == 'Exams' else 'none'};">
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
    </tbody>
  </table>
  <div class="pgn">Page 3 of 3 — Secure Marking Key</div>
</div>

<!-- ── ENGINEERING SCRIPTS ── -->
<script>
const rawText = `{js_content}`;
const rawAnswers = `{js_answers}`;

function sv(n,v) {{ document.documentElement.style.setProperty(n,v); }}
function toggleP() {{ document.getElementById('pS').classList.toggle('open'); }}

const tmpls = {{
  elite_dark: {{ '--h-bg':'#1e293b','--h-tx':'#fff','--br-l':'0px','--logo-f':"'Outfit'",'class':'' }},
  pro_protocol: {{ '--h-bg':'#fff','--h-tx':'#1e293b','--br-l':'20px','--logo-f':"'Playfair Display'",'class':'' }},
  academic_clean: {{ '--h-bg':'#fff','--h-tx':'#64748b','--br-l':'0px','--logo-f':"'Outfit'",'class':'' }},
  classic: {{ 'class':'tmpl-classic' }},
}};

function applyT(t) {{
  const p = document.getElementById('mainP');
  p.className = 'page ' + (tmpls[t].class || '');
  Object.entries(tmpls[t]).forEach(([k,v]) => {{ if(k!=='class') sv(k,v); }});
}}

document.addEventListener("DOMContentLoaded", function() {{
  const target = document.getElementById('content-body');
  const answerTarget = document.getElementById('answer-body');
  
  // 1. Process Markdown Context
  target.innerHTML = marked.parse(rawText);
  if (answerTarget) answerTarget.innerHTML = marked.parse(rawAnswers);

  // 2. Safely Refresh Inserted Scripts for Browser Evaluation (Crucial for TikZ plugin)
  const scripts = document.querySelectorAll('script');
  scripts.forEach(s => {{
    if(s.type === 'text/tikz') {{
      const newS = document.createElement('script');
      Array.from(s.attributes).forEach(attr => newS.setAttribute(attr.name, attr.value));
      newS.textContent = s.textContent;
      s.parentNode.replaceChild(newS, s);
    }}
  }});

  // 3. Dynamically Trigger external TikZ Engine AFTER injection
  const tz = document.createElement('script');
  tz.src = 'https://tikzjax.com/v1/tikzjax.js';
  document.head.appendChild(tz);
  
  // 4. Force KaTeX math rendering
  renderMathInElement(document.body, {{
    delimiters: [ 
      {{left: "$$", right: "$$", display: true}},
      {{left: "$", right: "$", display: false}} 
    ],
    throwOnError: false
  }});

  // 📡 SELECTION RELAY: Connect to Parent Studio
  document.addEventListener('selectionchange', () => {{
    const sel = window.getSelection();
    if (sel.toString().trim()) {{
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      window.parent.postMessage({{
        type: 'EDUQUEST_SELECTION',
        text: sel.toString(),
        rect: {{
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height
        }}
      }}, '*');
    }} else {{
      window.parent.postMessage({{ type: 'EDUQUEST_SELECTION_CLEAR' }}, '*');
    }}
  }});
}});
</script>
</body>
</html>
"""
    return template
