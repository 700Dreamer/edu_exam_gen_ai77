"""
nursery_builder.py
Renders authentic Ugandan nursery/ECD exam HTML from AI-generated question data.
Matches real Baby/Middle/Top class exam style from the NURSERY ITEMS folder.
"""

# SVG clip-art for common objects (black outline, white fill — matches real exam style)
OBJECT_SVGS = {
    "ball":    '<svg viewBox="0 0 50 50" width="38" height="38"><circle cx="25" cy="25" r="20" stroke="#000" stroke-width="2" fill="white"/><path d="M10 18 Q25 28 40 18" stroke="#000" stroke-width="1.5" fill="none"/><path d="M25 5 Q15 25 25 45" stroke="#000" stroke-width="1.5" fill="none"/></svg>',
    "apple":  '<svg viewBox="0 0 50 55" width="36" height="40"><ellipse cx="25" cy="32" rx="18" ry="20" stroke="#000" stroke-width="2" fill="white"/><path d="M25 12 Q28 6 34 8" stroke="#000" stroke-width="1.5" fill="none"/><path d="M25 12 L25 15" stroke="#000" stroke-width="1.5"/></svg>',
    "chair":  '<svg viewBox="0 0 50 55" width="36" height="40"><rect x="8" y="20" width="34" height="4" stroke="#000" stroke-width="2" fill="white"/><rect x="8" y="10" width="4" height="14" stroke="#000" stroke-width="2" fill="white"/><line x1="10" y1="24" x2="10" y2="50" stroke="#000" stroke-width="2"/><line x1="40" y1="24" x2="40" y2="50" stroke="#000" stroke-width="2"/><line x1="18" y1="24" x2="18" y2="50" stroke="#000" stroke-width="2"/><line x1="32" y1="24" x2="32" y2="50" stroke="#000" stroke-width="2"/></svg>',
    "cup":    '<svg viewBox="0 0 50 55" width="36" height="40"><path d="M12 15 L10 45 Q10 50 16 50 L34 50 Q40 50 40 45 L38 15 Z" stroke="#000" stroke-width="2" fill="white"/><path d="M38 22 Q48 22 46 32 Q44 40 38 36" stroke="#000" stroke-width="1.5" fill="none"/></svg>',
    "book":   '<svg viewBox="0 0 55 50" width="40" height="36"><rect x="5" y="8" width="45" height="34" rx="2" stroke="#000" stroke-width="2" fill="white"/><line x1="27" y1="8" x2="27" y2="42" stroke="#000" stroke-width="1.5"/><line x1="12" y1="18" x2="22" y2="18" stroke="#000" stroke-width="1"/><line x1="12" y1="24" x2="22" y2="24" stroke="#000" stroke-width="1"/></svg>',
    "pencil": '<svg viewBox="0 0 55 16" width="55" height="16"><rect x="5" y="4" width="40" height="8" stroke="#000" stroke-width="1.5" fill="white"/><polygon points="45,4 55,8 45,12" stroke="#000" stroke-width="1.5" fill="#eee"/><rect x="3" y="4" width="4" height="8" stroke="#000" stroke-width="1.5" fill="#ddd"/></svg>',
    "tree":   '<svg viewBox="0 0 50 60" width="36" height="44"><polygon points="25,4 45,36 5,36" stroke="#000" stroke-width="2" fill="white"/><polygon points="25,18 42,44 8,44" stroke="#000" stroke-width="2" fill="white"/><rect x="20" y="44" width="10" height="12" stroke="#000" stroke-width="2" fill="white"/></svg>',
    "flower": '<svg viewBox="0 0 50 55" width="36" height="40"><circle cx="25" cy="24" r="7" stroke="#000" stroke-width="1.5" fill="white"/><ellipse cx="25" cy="12" rx="5" ry="8" stroke="#000" stroke-width="1.5" fill="white"/><ellipse cx="25" cy="36" rx="5" ry="8" stroke="#000" stroke-width="1.5" fill="white"/><ellipse cx="13" cy="24" rx="8" ry="5" stroke="#000" stroke-width="1.5" fill="white"/><ellipse cx="37" cy="24" rx="8" ry="5" stroke="#000" stroke-width="1.5" fill="white"/><line x1="25" y1="44" x2="25" y2="55" stroke="#000" stroke-width="2"/></svg>',
    "star":   '<svg viewBox="0 0 50 50" width="36" height="36"><polygon points="25,4 30,18 46,18 33,27 38,43 25,34 12,43 17,27 4,18 20,18" stroke="#000" stroke-width="1.5" fill="white"/></svg>',
    "egg":    '<svg viewBox="0 0 40 50" width="30" height="38"><ellipse cx="20" cy="26" rx="14" ry="20" stroke="#000" stroke-width="2" fill="white"/></svg>',
    "tin":    '<svg viewBox="0 0 44 50" width="32" height="38"><rect x="6" y="12" width="32" height="34" stroke="#000" stroke-width="2" fill="white"/><ellipse cx="22" cy="12" rx="16" ry="5" stroke="#000" stroke-width="2" fill="white"/></svg>',
    "mango":  '<svg viewBox="0 0 46 55" width="34" height="40"><ellipse cx="22" cy="32" rx="16" ry="20" transform="rotate(-15 22 32)" stroke="#000" stroke-width="2" fill="white"/><path d="M22 12 Q26 4 32 6" stroke="#000" stroke-width="1.5" fill="none"/></svg>',
    "banana": '<svg viewBox="0 0 55 38" width="50" height="30"><path d="M5 30 Q20 5 50 10" stroke="#000" stroke-width="4" fill="none" stroke-linecap="round"/></svg>',
    "pot":    '<svg viewBox="0 0 54 50" width="40" height="36"><path d="M10 18 L8 42 Q8 46 14 46 L40 46 Q46 46 46 42 L44 18 Z" stroke="#000" stroke-width="2" fill="white"/><rect x="8" y="14" width="38" height="6" rx="2" stroke="#000" stroke-width="2" fill="white"/><line x1="8" y1="18" x2="2" y2="14" stroke="#000" stroke-width="2"/><line x1="46" y1="18" x2="52" y2="14" stroke="#000" stroke-width="2"/></svg>',
    "stool":  '<svg viewBox="0 0 50 50" width="36" height="36"><rect x="5" y="12" width="40" height="6" rx="1" stroke="#000" stroke-width="2" fill="white"/><line x1="12" y1="18" x2="10" y2="46" stroke="#000" stroke-width="2"/><line x1="38" y1="18" x2="40" y2="46" stroke="#000" stroke-width="2"/><line x1="22" y1="18" x2="20" y2="46" stroke="#000" stroke-width="2"/><line x1="28" y1="18" x2="30" y2="46" stroke="#000" stroke-width="2"/></svg>',
    "sweet":  '<svg viewBox="0 0 50 40" width="36" height="28"><ellipse cx="25" cy="20" rx="14" ry="10" stroke="#000" stroke-width="2" fill="white"/><line x1="4" y1="20" x2="11" y2="20" stroke="#000" stroke-width="2"/><line x1="39" y1="20" x2="46" y2="20" stroke="#000" stroke-width="2"/></svg>',
    "house":  '<svg viewBox="0 0 54 54" width="40" height="40"><polygon points="27,4 50,24 4,24" stroke="#000" stroke-width="2" fill="white"/><rect x="10" y="24" width="34" height="26" stroke="#000" stroke-width="2" fill="white"/><rect x="20" y="36" width="14" height="14" stroke="#000" stroke-width="2" fill="white"/></svg>',
    "stick":  '<svg viewBox="0 0 10 50" width="10" height="44"><line x1="5" y1="2" x2="5" y2="48" stroke="#000" stroke-width="3" stroke-linecap="round"/></svg>',
}
# Fallback for unknown objects — simple dot
def _obj_svg(name, count):
    key = name.lower().rstrip('s')  # try singular
    svg = OBJECT_SVGS.get(name.lower()) or OBJECT_SVGS.get(key, 
          '<svg viewBox="0 0 30 30" width="24" height="24"><circle cx="15" cy="15" r="12" stroke="#000" stroke-width="2" fill="white"/></svg>')
    return ''.join(f'<span style="display:inline-block;margin:1px">{svg}</span>' for _ in range(min(count, 10)))

SHAPE_SVGS = {
    "circle":    '<svg viewBox="0 0 60 60" width="50" height="50"><circle cx="30" cy="30" r="24" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "square":    '<svg viewBox="0 0 60 60" width="50" height="50"><rect x="8" y="8" width="44" height="44" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "triangle":  '<svg viewBox="0 0 60 60" width="50" height="50"><polygon points="30,6 54,52 6,52" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "rectangle": '<svg viewBox="0 0 80 55" width="70" height="50"><rect x="4" y="8" width="72" height="38" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "oval":      '<svg viewBox="0 0 80 55" width="70" height="50"><ellipse cx="40" cy="27" rx="34" ry="20" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "cone":      '<svg viewBox="0 0 60 70" width="50" height="60"><polygon points="30,4 54,60 6,60" stroke="#000" stroke-width="2.5" fill="none"/><ellipse cx="30" cy="60" rx="24" ry="7" stroke="#000" stroke-width="2" fill="none"/></svg>',
    "diamond":   '<svg viewBox="0 0 60 60" width="50" height="50"><polygon points="30,4 56,30 30,56 4,30" stroke="#000" stroke-width="2.5" fill="none"/></svg>',
    "star":      '<svg viewBox="0 0 60 60" width="50" height="50"><polygon points="30,4 36,22 56,22 40,34 46,54 30,42 14,54 20,34 4,22 24,22" stroke="#000" stroke-width="2" fill="none"/></svg>',
}

PICTURE_EMOJIS = {
    "apple": "🍎", "apples": "🍎", "ball": "⚽", "balls": "⚽",
    "chair": "🪑", "chairs": "🪑", "cup": "☕", "cups": "☕",
    "book": "📚", "books": "📚", "pen": "✏️", "pens": "✏️",
    "pencil": "✏️", "pencils": "✏️", "tree": "🌳", "trees": "🌳",
    "flower": "🌸", "flowers": "🌸", "cat": "🐱", "dog": "🐶",
    "bird": "🐦", "birds": "🐦", "fish": "🐟", "fishes": "🐟",
    "banana": "🍌", "bananas": "🍌", "mango": "🥭", "mangoes": "🥭",
    "egg": "🥚", "eggs": "🥚", "star": "⭐", "stars": "⭐",
    "house": "🏠", "houses": "🏠", "car": "🚗", "cars": "🚗",
    "bus": "🚌", "cow": "🐄", "cows": "🐄", "goat": "🐐", "goats": "🐐",
    "tin": "🥫", "tins": "🥫", "pot": "🍳", "pots": "🍳",
    "stool": "🪑", "stools": "🪑", "sweet": "🍬", "sweets": "🍬",
    "stick": "🦯", "sticks": "🦯",
}

def _dot_line(width="260px"):
    return f'<div style="display:inline-block;width:{width};border-bottom:2px dotted #555;margin-left:6px;vertical-align:bottom;">&nbsp;</div>'

def _big_blank(width="80px"):
    return f'<span style="display:inline-block;width:{width};border-bottom:2px solid #000;margin:0 8px;vertical-align:bottom;">&nbsp;</span>'

def _build_circle_opt_html(opt):
    opt_str = str(opt).strip()
    font_sz = "38px"
    circle_wd = "82px"
    circle_ht = "82px"
    border_rad = "50%"
    padding_str = "0"
    
    if len(opt_str) > 2:
        # If it's a word, scale down the font and change the shape to an oval/pill border to prevent overlaps
        font_sz = "20px" if len(opt_str) > 5 else "24px"
        circle_wd = "auto"
        circle_ht = "64px"
        border_rad = "32px"
        padding_str = "0 20px"
        
    return f'<div class="nq-circle-opt" style="font-size: {font_sz}; width: {circle_wd}; height: {circle_ht}; border-radius: {border_rad}; padding: {padding_str};">{opt}</div>'


def _render_question(q: dict, idx: int, images: dict = None) -> str:
    images = images or {}
    num = q.get("number", idx + 1)
    instruction = q.get("instruction", "")
    qtype = q.get("type", "")
    content = q.get("content", {})

    # Intelligently rephrase draw/colour instructions if an SVG asset is pre-rendered in the box
    if qtype == "draw_colour":
        items = (content.get("items") or [])
        if items:
            label = str(items[0])
            key = label.lower().replace("a ", "").replace("an ", "").strip().split()[0]
            b64 = images.get(key) or images.get(key.rstrip('s')) or images.get(key + 's')
            if b64 and ("draw" in instruction.lower()):
                instruction = instruction.replace("Draw and colour", "Colour").replace("draw and colour", "colour")
                instruction = instruction.replace("Draw and Color", "Color").replace("draw and color", "color")
                instruction = instruction.replace("Draw and color", "Color").replace("draw and color", "color")
                instruction = instruction.replace("Draw and", "Colour and").replace("draw and", "colour and")
                instruction = instruction.replace("Draw", "Colour").replace("draw", "colour")

    html = f'''
<div class="nq-block">
  <div class="nq-num">{num}.</div>
  <div class="nq-body">
    <div class="nq-instruction">{instruction}</div>
    <div class="nq-content">
'''

    def _pic_content(pic: str, count: int) -> str:
        """Return either a real image grid or SVG fallback for a given object."""
        try:
            count = int(count)
        except:
            count = 3
            
        if count <= 0:
            return f'<div class="nq-pic-box" style="font-size: 16px; font-weight: bold; color: #888; text-align: center;">(empty set)</div>'
            
        key = pic.lower()
        b64 = images.get(key) or images.get(key.rstrip('s')) or images.get(key + 's')
        if b64:
            # We must map to the exact clean key that was found
            found_key = key if images.get(key) else (key.rstrip('s') if images.get(key.rstrip('s')) else key + 's')
            clean_key = "".join(c for c in found_key if c.isalnum())
            imgs = ''.join(
                f'<div class="dyn-bg-{clean_key}" '
                f'style="width: 70px; height: 70px; background-size: contain; background-repeat: no-repeat; background-position: center; display: inline-block;"></div>'
                for _ in range(min(count, 8))
            )
            return f'<div class="nq-pic-img-row">{imgs}</div>'
        else:
            return f'<div class="nq-pic-box">{_obj_svg(pic, count)}</div>'

    # ── COUNT & WRITE ──
    if qtype == "count_write":
        items = (content.get("items") or [])
        html += '<div class="nq-count-row">'
        for item in items:
            pic = item.get("picture", "objects")
            count = item.get("count", 3)
            pic_html = _pic_content(pic, count)
            html += f'''
<div class="nq-count-item">
  {pic_html}
  <div class="nq-write-line">= {_big_blank("70px")}</div>
</div>'''
        html += '</div>'

    # ── SEQUENCE ──
    elif qtype == "sequence":
        seqs = (content.get("sequences") or [])
        if not seqs and content.get("sequence_str"):
            seqs = [{"sequence_str": content["sequence_str"]}]
        html += '<div class="nq-seq-list">'
        for s in seqs:
            if "sequence_str" in s:
                line = s["sequence_str"].replace("___", _big_blank("55px"))
                html += f'<div class="nq-seq-line">{line}</div>'
            else:
                given = s.get("given", [])
                after = s.get("after", [])
                parts = [f'<span class="nq-seq-num">{n}</span>' for n in given]
                parts.append(_big_blank("55px"))
                parts += [f'<span class="nq-seq-num">{n}</span>' for n in after]
                html += f'<div class="nq-seq-line">{", ".join(parts)}</div>'
        html += '</div>'

    # ── DRAW FOR NUMBER ── (number + elegant dashed drawing box next to it, matching real exams)
    elif qtype == "draw_for_number":
        numbers = (content.get("numbers") or [1, 2, 3])
        html += '<div class="nq-draw-grid" style="display:flex; flex-direction:column; gap:20px;">'
        for n in numbers:
            html += f'''
<div class="nq-draw-box" style="display:flex; align-items:center; gap:20px;">
  <span class="nq-draw-num" style="font-size:36px; font-weight:900; min-width:40px;">{n}</span>
  <div class="nq-dc-box" style="width:200px; height:100px; border:2px dashed #aaa; border-radius:8px; background-color:#fafafa;"></div>
</div>'''
        html += '</div>'

    # ── ADD NUMBERS ── (bordered grid table like real exams)
    elif qtype == "add_numbers":
        sums = (content.get("sums") or [])
        html += '<table class="nq-add-table"><tbody>'
        for s in sums:
            a = s.get("a", 1)
            b = s.get("b", 1)
            html += f'<tr><td class="nq-add-cell">{a}</td><td class="nq-add-op">+</td><td class="nq-add-cell">{b}</td><td class="nq-add-op">=</td><td class="nq-add-ans">&nbsp;</td></tr>'
        html += '</tbody></table>'

    # ── MATCH WORDS (show image on left when available) ──
    elif qtype in ("match_words", "match_numbers", "match_pictures"):
        left = (content.get("left") or [])
        right = (content.get("right") or [])

        # Shuffle/Derange right-side items so answers aren't aligned side-by-side
        import random
        shuffled_right = list(right)
        if len(shuffled_right) > 1:
            for _ in range(100):
                random.shuffle(shuffled_right)
                if all(shuffled_right[idx] != right[idx] for idx in range(min(len(right), len(shuffled_right)))):
                    break
            else:
                # Fallback: simple cyclic shift if random shuffling fails to produce a derangement
                shuffled_right = right[1:] + [right[0]]

        html += '<div class="nq-match-table">'
        max_len = max(len(left), len(shuffled_right))
        for i in range(max_len):
            l_item = str(left[i]) if i < len(left) else ""
            r_item = str(shuffled_right[i]) if i < len(shuffled_right) else ""
            # Check if left item is a known object with an image
            l_key = l_item.lower()
            l_clean = l_key.replace("a picture of an ", "").replace("a picture of a ", "").replace("a picture of ", "").strip()
            b64 = images.get(l_clean) or images.get(l_clean.rstrip('s')) or images.get(l_clean + 's')
            if b64:
                found_key = l_clean if images.get(l_clean) else (l_clean.rstrip('s') if images.get(l_clean.rstrip('s')) else l_clean + 's')
                clean_key = "".join(c for c in found_key if c.isalnum())
                l_html = f'<div class="dyn-bg-{clean_key}" style="width: 60px; height: 60px; background-size: contain; background-repeat: no-repeat; background-position: center; display: inline-block;"></div>'
            else:
                l_html = l_item
            html += f'''
<div class="nq-match-row">
  <div class="nq-match-left">{l_html}</div>
  <span class="nq-match-bullet">•</span>
  <div class="nq-match-line"></div>
  <span class="nq-match-bullet">•</span>
  <div class="nq-match-right">{r_item}</div>
</div>'''
        html += '</div>'

    # ── NAME SHAPES ──
    elif qtype == "name_shapes":
        shapes = (content.get("shapes") or ["circle", "square", "triangle"])
        html += '<div class="nq-shapes-row">'
        for shape in shapes:
            svg = SHAPE_SVGS.get(shape.lower(), SHAPE_SVGS["circle"])
            html += f'''
<div class="nq-shape-item">
  <div class="nq-shape-svg">{svg}</div>
  <div class="nq-shape-name">{_big_blank("80px")}</div>
</div>'''
        html += '</div>'

    # ── WRITE IN WORDS ──
    elif qtype == "write_in_words":
        numbers = (content.get("numbers") or [1, 2, 3])
        word_hints = (content.get("word_hints") or [])
        html += '<div class="nq-words-grid">'
        for n in numbers:
            html += f'<div class="nq-words-item"><span class="nq-num-big">{n}</span> {_big_blank("120px")}</div>'
        if word_hints:
            html += f'<div class="nq-hint">({", ".join(word_hints)})</div>'
        html += '</div>'

    # ── NUMBER BETWEEN ──
    elif qtype == "number_between":
        pairs = (content.get("pairs") or [])
        html += '<div class="nq-between-grid">'
        for p in pairs:
            left_n = p.get("left", 0)
            right_n = p.get("right", 2)
            html += f'<div class="nq-between-item">{left_n} {_big_blank("60px")} {right_n}</div>'
        html += '</div>'

    # ── CIRCLE CORRECT ──
    elif qtype == "circle_correct":
        options = (content.get("options") or [])
        task = content.get("task", "").strip()
        if task:
            # Semantic safeguard to prevent double-concatenating standard verbs
            if any(task.lower().startswith(v) for v in ["circle", "choose", "draw", "identify", "find", "match"]):
                html += f'<div class="nq-task-label">{task}</div>'
            else:
                html += f'<div class="nq-task-label">Circle the {task}.</div>'
        html += '<div class="nq-circle-row" style="display:flex; flex-wrap:wrap; justify-content:space-around; align-items:flex-end;">'
        for opt in options:
            opt_str = str(opt).strip()
            key = opt_str.lower().replace("a ", "").replace("an ", "").strip().split()[0]
            b64 = images.get(key)
            html += '<div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">'
            html += _build_circle_opt_html(opt)
            if b64:
                html += f'<div style="width: 120px; height: 120px; background-image: url(data:image/png;base64,{b64}); background-size: contain; background-repeat: no-repeat; background-position: center;"></div>'
            html += '</div>'
        html += '</div>'

    # ── NAME PICTURE ──
    elif qtype == "name_picture":
        pictures = content.get("items") or content.get("words") or []
        html += '<div class="nq-name-pic-row" style="display:flex; flex-wrap:wrap; justify-content:space-around; gap: 30px; margin-top:20px;">'
        for pic in pictures:
            p_val = pic.get("picture") if isinstance(pic, dict) else str(pic)
            key = p_val.lower().replace("a ", "").replace("an ", "").strip().split()[0]
            b64 = images.get(key)
            if b64:
                img_html = f'<div style="width: 180px; height: 180px; background-image: url(data:image/png;base64,{b64}); background-size: contain; background-repeat: no-repeat; background-position: center; margin-bottom: 15px;"></div>'
            else:
                img_html = f'<div style="width: 180px; height: 180px; border: 2px dashed #999; display:flex; align-items:center; justify-content:center; color:#999; margin-bottom: 15px;">{p_val}</div>'
            html += f'<div style="display:flex; flex-direction:column; align-items:center;">{img_html}<div style="width:180px; border-bottom: 3px dotted #555; height:20px;"></div></div>'
        html += '</div>'

    # ── FILL MISSING LETTER ──
    elif qtype == "fill_missing_letter":
        words = (content.get("words") or [])
        html += '<div class="nq-fill-grid">'
        for w in words:
            display = w.replace("_", _big_blank("30px"))
            html += f'<div class="nq-fill-item">{display}</div>'
        html += '</div>'

    # ── DRAW & COLOUR (show image to colour if available) ──
    elif qtype == "draw_colour":
        items = (content.get("items") or [])
        html += '<div class="nq-draw-colour-grid">'
        for item in items:
            if isinstance(item, dict):
                label = str(item.get("picture") or item.get("object") or "")
            else:
                label = str(item)
            key = label.lower().replace("a picture of ", "").strip()
            b64 = images.get(key) or images.get(key.rstrip('s')) or images.get(key + 's')
            if b64:
                box_html = f'<img src="{b64}" width="200" height="200" style="object-fit:contain;border:1px dashed #aaa;border-radius:6px;padding:6px" />'
            else:
                box_html = '<div class="nq-dc-box"></div>'
            html += f'''
<div class="nq-dc-item">
  {box_html}
  <div class="nq-dc-label">{label}</div>
</div>'''
        html += '</div>'

    # ── COPY WORD ──
    elif qtype == "copy_word":
        words = (content.get("words") or [])
        html += '<div class="nq-copy-list">'
        for w in words:
            html += f'<div class="nq-copy-item"><span class="nq-copy-word">{w}</span> {_dot_line("200px")}</div>'
        html += '</div>'

    # ── ODD ONE OUT ──
    elif qtype == "odd_one_out":
        groups = (content.get("groups") or [])
        for g in groups:
            words = g.get("words", [])
            html += '<div class="nq-odd-row">'
            for w in words:
                key = str(w).lower().replace("a ", "").replace("an ", "").strip().split()[0]
                if key in images:
                    html += f'<div class="nq-odd-word" style="display:inline-block; margin: 10px; width: 120px; height: 120px; background-image: url(data:image/png;base64,{images[key]}); background-size: contain; background-repeat: no-repeat; background-position: center; border: 2px solid #ddd; border-radius: 8px;"></div>'
                else:
                    html += f'<span class="nq-odd-word">{w}</span>'
            html += '</div>'

    # ── MAKE SENTENCE ──
    elif qtype == "make_sentence":
        words = (content.get("words") or [])
        html += '<div class="nq-sentence-words">'
        for w in words:
            html += f'<span class="nq-sent-word">{w}</span>'
        html += '</div>'
        html += _dot_line("100%")

    # ── TRACE LETTER ──
    elif qtype == "trace_letter":
        letters = (content.get("letters") or ["A", "B", "C"])
        html += '<div class="nq-trace-row">'
        for letter in letters:
            html += f'<div class="nq-trace-box"><span class="nq-trace-letter" style="opacity:0.18;font-size:72px;font-weight:900;color:#000;">{letter}</span></div>'
        html += '</div>'

    # ── SHADE FOR NUMBER (grid of small squares) ──
    elif qtype == "shade_for_number":
        items = (content.get("items") or [])
        html += '<div class="nq-shade-grid">'
        for item in items:
            n = item if isinstance(item, int) else item.get("number", 3)
            max_boxes = max(n + 2, 8)
            boxes = ''.join(
                f'<div class="nq-shade-box{" filled" if i < n else ""}" ></div>'
                for i in range(max_boxes)
            )
            html += f'<div class="nq-shade-row"><span class="nq-shade-num">{n}</span><div class="nq-shade-boxes">{boxes}</div></div>'
        html += '</div>'

    # ── NAME THE SETS ──
    elif qtype == "name_sets":
        sets = (content.get("sets") or [])
        
        # Build an authentic shuffled Word Bank from targets
        word_bank = []
        for s in sets:
            obj = s.get("object", "balls")
            hint = s.get("hint", "")
            word_bank.append(hint or obj)
            
        import random
        shuffled_bank = list(word_bank)
        if len(shuffled_bank) > 1:
            random.shuffle(shuffled_bank)
            
        html += '<div class="nq-sets-list" style="display:flex; flex-direction:column; gap:24px;">'
        
        # Beautiful, authentic pre-primary Word Bank box
        if shuffled_bank:
            bank_html = ', &nbsp; '.join(f'<strong>{w}</strong>' for w in shuffled_bank)
            html += f'<div style="border: 2px dashed #aaa; padding: 10px 16px; border-radius: 8px; font-size: 20px; text-align: center; margin-bottom: 12px; background-color: #fafafa; font-style: italic; letter-spacing: 1px;">Word Bank: &nbsp; {bank_html}</div>'
            
        for s in sets:
            count_word = s.get("count_word", "three")
            obj = s.get("object", "balls")
            
            # Map count word to integer for SVG rendering
            word_to_int = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
            }
            c_val = word_to_int.get(count_word.lower(), 3)
            pic_html = _pic_content(obj, c_val)
            
            # Render clean, premium question row WITHOUT the answer leak
            if c_val == 1 or count_word.lower() == "one":
                text_html = f'{_big_blank("140px")}'
            else:
                text_html = f'A set of <span class="nq-set-word" style="font-weight:900;">{count_word}</span> {_big_blank("140px")}.'
                
            html += f'''
<div class="nq-set-item" style="display:flex; align-items:center; gap:20px; margin-bottom:12px;">
  {pic_html}
  <div class="nq-set-row" style="font-size:24px; flex:1;">{text_html}</div>
</div>'''
        html += '</div>'

    # ── DAYS OF WEEK ──
    elif qtype == "days_of_week":
        days = (content.get("days") or [
            ("S___nday","Sunday"), ("M__nday","Monday"), ("T__esday","Tuesday"),
            ("W___dnesday","Wednesday"), ("Th___rsday","Thursday"),
            ("Fr___day","Friday"), ("Sat___rday","Saturday")
        ])
        html += '<div class="nq-days-grid">'
        for pair in days:
            jumbled = pair[0] if isinstance(pair, (list,tuple)) else pair
            html += f'<div class="nq-day-item">{jumbled}</div>'
        html += '</div>'

    # ── WRITE NUMBER NAMES (two-column grid) ──
    elif qtype == "write_number_names":
        pairs = (content.get("pairs") or [])
        hint_words = (content.get("hint_words") or [])
        html += '<div class="nq-numnames-grid">'
        for p in pairs:
            num = p.get("number", 1)
            html += f'<div class="nq-numname-item"><span class="nq-numname-num">{num}</span> {_big_blank("110px")}</div>'
        if hint_words:
            html += f'<div class="nq-hint nq-numnames-hint">({" , ".join(hint_words)})</div>'
        html += '</div>'

    # ── ORAL QUESTIONS ──
    elif qtype == "oral_questions":
        questions_list = (content.get("questions") or [])
        html += '<div class="nq-oral-list">'
        for qi, oq in enumerate(questions_list, 1):
            html += f'<div class="nq-oral-item">{qi}. {oq}</div>'
        html += '</div>'

    # ── COUNT AND CIRCLE CORRECT NUMBER ──
    elif qtype == "count_circle":
        items = (content.get("items") or [])
        html += '<div class="nq-ccircle-grid">'
        for item in items:
            pic = item.get("picture", "balls")
            count = item.get("count", 3)
            options = item.get("options") or [count-1, count, count+1]
            pic_html = _pic_content(pic, count)
            opts_html = ''.join(_build_circle_opt_html(o) for o in options)
            html += f'<div class="nq-ccircle-item">{pic_html}<div class="nq-circle-row">{opts_html}</div></div>'
        html += '</div>'

    # ── READ AND DRAW ──
    elif qtype == "read_and_draw":
        items = (content.get("items") or [])
        html += '<div class="nq-draw-colour-grid" style="display:grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top:10px;">'
        for item in items:
            label = str(item)
            html += f'''
<div class="nq-dc-item" style="text-align:center;">
  <div class="nq-dc-box" style="width:100%; height:130px; border:2px dashed #aaa; border-radius:8px; background-color:#fafafa; margin-bottom:8px;"></div>
  <div class="nq-dc-label" style="font-size:20px; font-weight:700;">{label}</div>
</div>'''
        html += '</div>'

    # ── FALLBACK ──
    else:
        html += _dot_line("100%") + "<br/>" + _dot_line("100%")

    html += '''
    </div>
  </div>
</div>'''
    return html


def build_nursery_html(exam_data: dict, images: dict = None) -> str:
    """Build a complete nursery exam HTML page from AI-generated exam_data dict."""
    images = images or {}

    class_level = exam_data.get("class_level", "Middle Class")
    learning_area = exam_data.get("learning_area", "LA4")
    la_name = exam_data.get("la_name", "MATHEMATICAL CONCEPTS")
    period_full = exam_data.get("period_full", "END OF TERM")
    term_roman = exam_data.get("term_roman", "I")
    year = exam_data.get("year", "2025")
    school_name = exam_data.get("school_name", "EduQuest Academy")
    age_range = exam_data.get("age_range", "4 – 5")
    questions = exam_data.get("questions", [])

    # Retrieve visual layout patch if present
    layout_css = exam_data.get("layout_css_patch") or ""

    # Generate deduped CSS classes for Base64 Data URIs to prevent HTML bloat
    css_classes = []
    b64_to_class = {}
    for key, b64 in images.items():
        clean_key = "".join(c for c in key if c.isalnum())
        if not clean_key: continue
        if b64 not in b64_to_class:
            b64_to_class[b64] = [clean_key]
        else:
            b64_to_class[b64].append(clean_key)
            
    for b64, keys in b64_to_class.items():
        selectors = ", ".join(f".dyn-bg-{k}" for k in keys)
        css_classes.append(f'{selectors} {{ background-image: url("{b64}"); }}')
        
    dynamic_bg_css = "\\n".join(css_classes)

    # Build question blocks, split into pages of 3
    pages_html = []
    page_qs = []
    for i, q in enumerate(questions):
        page_qs.append(_render_question(q, i, images=images))
        if len(page_qs) == 3 or i == len(questions) - 1:
            pages_html.append("\n".join(page_qs))
            page_qs = []

    # Footer line per page (real exam style)
    def _footer(school, cl, la, page_num, total):
        return f'<div class="nq-footer"><span>{school} &nbsp; {cl} {la}</span><span>Page{page_num}</span></div>'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&family=Patrick+Hand&family=Codystar&display=swap" rel="stylesheet">
<title>{school_name} – {class_level} {learning_area}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: "Comic Sans MS", "Chalkboard SE", "Comic Neue", "Nunito", sans-serif; background: #f5f7fa; padding: 20px; color: #111; font-size: 28px; }}
.nq-page {{ background: white; width: 210mm; min-height: 297mm; margin: 0 auto 30px auto; padding: 10mm 12mm 14mm 12mm; box-shadow: 0 4px 24px rgba(0,0,0,0.1); }}

/* DYNAMIC BASE64 BACKGROUNDS */
{dynamic_bg_css}

/* HEADER */
.nq-header {{ text-align: center; border-bottom: 3px solid #000; padding-bottom: 10px; margin-bottom: 14px; }}
.nq-school {{ font-size: 26px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px; }}
.nq-exam-title {{ font-size: 18px; font-weight: 700; text-transform: uppercase; margin-top: 3px; }}
.nq-class-info {{ font-size: 17px; font-weight: 700; margin-top: 2px; text-transform: uppercase; }}
.nq-la-title {{ font-size: 17px; font-weight: 900; margin-top: 2px; text-transform: uppercase; text-decoration: underline; }}

/* FIELDS */
.nq-fields {{ display: flex; flex-direction: column; gap: 24px; margin: 20px 0 36px 0; }}
.nq-field-row {{ display: flex; align-items: flex-end; gap: 8px; font-size: 22px; font-weight: 700; }}
.nq-field-line {{ flex: 1; border-bottom: 2px dotted #444; min-width: 200px; height: 28px; }}

/* QUESTION BLOCK */
.nq-block {{ display: flex; gap: 24px; margin-bottom: 90px; page-break-inside: avoid; background-color: #fff; border: 3px dashed #e5e7eb; border-radius: 40px; padding: 40px; }}
.nq-num {{ font-size: 34px; font-weight: 900; min-width: 60px; height: 60px; color: #fff; background: #222; border-radius: 20px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.nq-body {{ flex: 1; }}
.nq-instruction {{ font-size: 36px; font-weight: 900; margin-bottom: 40px; text-transform: capitalize; line-height: 1.4; color: #1f2937; }}
.nq-content {{ padding-left: 4px; }}

/* COUNT & WRITE */
.nq-count-row {{ display: flex; flex-direction: column; gap: 50px; align-items: flex-start; }}
.nq-count-item {{ display: flex; align-items: center; gap: 20px; }}
.nq-pic-box {{ border: 2px solid #bbb; border-radius: 8px; padding: 8px 10px; min-width: 110px; min-height: 110px; display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 3px; background: #fafafa; }}
.nq-write-line {{ font-size: 24px; font-weight: 700; }}

.nq-pic-img-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px;
  border: 2px solid #bbb;
  border-radius: 8px;
  min-width: 90px;
  min-height: 90px;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}}
.nq-pic-img-row img {{
  object-fit: contain;
}}

/* TRACE LETTER */
.nq-trace-row {{ display: flex; flex-direction: column; gap: 20px; }}
.nq-trace-item {{ font-family: 'Coming Soon', cursive; font-size: 60px; color: #555; font-weight: 400; display: flex; align-items: flex-end; gap: 12px; }}

/* SEQUENCE */
.nq-seq-list {{ display: flex; flex-direction: column; gap: 30px; }}
.nq-seq-line {{ font-size: 34px; font-weight: 700; display: flex; align-items: flex-end; flex-wrap: wrap; gap: 2px 6px; line-height: 2.4; }}

/* DRAW FOR NUMBER */
.nq-draw-grid {{ display: flex; flex-direction: column; gap: 28px; }}
.nq-draw-box {{ display: flex; align-items: flex-end; gap: 14px; }}
.nq-draw-num {{ font-size: 52px; font-weight: 900; min-width: 44px; line-height: 1; }}
.nq-draw-dotline {{ flex: 1; border-bottom: 2px dashed #888; min-width: 200px; height: 80px; margin-bottom: 2px; }}

/* ADD NUMBERS TABLE */
.nq-add-table {{ border-collapse: collapse; margin-top: 6px; border-spacing: 6px; }}
.nq-add-table tr {{ height: 80px; }}
.nq-add-cell {{ border: 2.5px solid #000; width: 72px; height: 72px; text-align: center; font-size: 36px; font-weight: 900; padding: 0; vertical-align: middle; }}
.nq-add-op {{ font-size: 36px; font-weight: 900; padding: 0 10px; text-align: center; vertical-align: middle; }}
.nq-add-ans {{ border: 2.5px solid #000; width: 110px; height: 72px; vertical-align: middle; }}

/* MATCH */
.nq-match-table {{ display: flex; flex-direction: column; gap: 40px; max-width: 500px; }}
.nq-match-row {{ display: flex; align-items: center; gap: 16px; }}
.nq-match-left, .nq-match-right {{ font-size: 28px; font-weight: 700; min-width: 130px; }}
.nq-match-right {{ text-align: right; }}
.nq-match-line {{ flex: 1; min-width: 100px; }}
.nq-match-bullet {{ font-size: 34px; color: #000; margin: 0 16px; display: flex; align-items: center; justify-content: center; }}

/* SHAPES */
.nq-shapes-row {{ display: flex; flex-direction: column; gap: 50px; align-items: flex-start; }}
.nq-shape-item {{ display: flex; align-items: center; gap: 24px; }}
.nq-shape-svg svg {{ width: 90px !important; height: 90px !important; }}
.nq-shape-name {{ font-size: 18px; font-weight: 700; }}

/* WRITE IN WORDS */
.nq-words-grid {{ display: flex; flex-wrap: wrap; gap: 20px 40px; }}
.nq-words-item {{ font-size: 26px; font-weight: 700; display: flex; align-items: flex-end; gap: 6px; }}
.nq-num-big {{ font-size: 36px; font-weight: 900; }}
.nq-hint {{ font-size: 14px; font-style: italic; margin-top: 8px; color: #555; width: 100%; }}

/* NUMBER BETWEEN */
.nq-between-grid {{ display: flex; flex-wrap: wrap; gap: 20px 40px; }}
.nq-between-item {{ font-size: 34px; font-weight: 700; display: flex; align-items: flex-end; gap: 6px; }}

/* CIRCLE CORRECT */
.nq-task-label {{ font-size: 17px; font-style: italic; margin-bottom: 10px; }}
.nq-circle-row {{ display: flex; flex-wrap: wrap; gap: 24px; }}
.nq-circle-opt {{ font-weight: 900; border: 2.5px solid #000; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }}

/* FILL MISSING LETTER */
.nq-fill-grid {{ display: flex; flex-wrap: wrap; gap: 20px 40px; }}
.nq-fill-item {{ font-size: 36px; font-weight: 900; display: flex; align-items: flex-end; gap: 2px; }}

/* DRAW & COLOUR */
.nq-draw-colour-grid {{ display: flex; flex-direction: column; gap: 50px; }}
.nq-dc-item {{ display: flex; align-items: center; gap: 24px; }}
.nq-dc-box {{ width: 180px; height: 170px; border: 2px dashed #aaa; border-radius: 8px; }}
.nq-dc-label {{ font-size: 22px; font-weight: 700; text-align: center; }}

/* COPY WORD */
.nq-copy-list {{ display: flex; flex-direction: column; gap: 40px; }}
.nq-copy-item {{ font-size: 32px; display: flex; align-items: flex-end; gap: 14px; line-height: 1.6; }}
.nq-copy-word {{ font-family: 'Coming Soon', cursive; font-size: 50px; font-weight: 400; min-width: 120px; color: #555; }}

/* ODD ONE OUT */
.nq-odd-row {{ display: flex; flex-wrap: wrap; gap: 14px; }}
.nq-odd-word {{ font-size: 28px; font-weight: 700; border: 2px solid #000; border-radius: 8px; padding: 6px 18px; }}

/* SENTENCE */
.nq-sentence-words {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 14px; }}
.nq-sent-word {{ font-size: 28px; font-weight: 700; border: 2px solid #000; border-radius: 8px; padding: 6px 16px; }}

/* TRACE */
.nq-trace-row {{ display: flex; flex-wrap: wrap; gap: 12px; }}
.nq-trace-box {{ width: 130px; height: 130px; border: 1.5px dashed #ccc; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}

/* SHADE FOR NUMBER */
.nq-shade-grid {{ display: flex; flex-direction: column; gap: 22px; }}
.nq-shade-row {{ display: flex; align-items: center; gap: 14px; }}
.nq-shade-num {{ font-size: 36px; font-weight: 900; min-width: 36px; }}
.nq-shade-boxes {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.nq-shade-box {{ width: 34px; height: 34px; border: 2px solid #000; }}
.nq-shade-box.filled {{ background: #000; }}

/* NAME THE SETS */
.nq-sets-list {{ display: flex; flex-direction: column; gap: 22px; }}
.nq-set-row {{ font-size: 26px; font-weight: 700; display: flex; align-items: flex-end; flex-wrap: wrap; gap: 6px; }}
.nq-set-word {{ font-weight: 900; }}
.nq-set-hint {{ font-size: 13px; font-style: italic; color: #666; width: 100%; margin-top: 2px; }}

/* DAYS OF WEEK */
.nq-days-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px 32px; }}
.nq-day-item {{ font-size: 28px; font-weight: 700; }}

/* WRITE NUMBER NAMES */
.nq-numnames-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px 36px; }}
.nq-numname-item {{ font-size: 28px; font-weight: 700; display: flex; align-items: flex-end; gap: 8px; }}
.nq-numname-num {{ font-size: 38px; font-weight: 900; min-width: 36px; }}
.nq-numnames-hint {{ grid-column: 1/-1; font-size: 14px; font-style: italic; color: #555; }}

/* ORAL QUESTIONS */
.nq-oral-list {{ display: flex; flex-direction: column; gap: 20px; }}
.nq-oral-item {{ font-size: 26px; font-weight: 700; }}

/* COUNT AND CIRCLE */
.nq-ccircle-grid {{ display: flex; flex-wrap: wrap; gap: 28px; }}
.nq-ccircle-item {{ display: flex; flex-direction: column; align-items: center; gap: 8px; }}

/* FOOTER */
.nq-footer {{ margin-top: 28px; padding-top: 6px; border-top: 1.5px solid #aaa; display: flex; justify-content: space-between; font-size: 11px; font-weight: 900; color: #333; text-transform: uppercase; letter-spacing: 0.5px; }}

@media print {{
  body {{ background: none; padding: 0; }}
  .nq-page {{ box-shadow: none; margin: 0; page-break-after: always; width: 100%; padding: 12mm 14mm; }}
}}

/* Dynamic VLM Visual layout patch overrides */
{layout_css}
</style>
</head>
<body>
"""

    for pi, page_content in enumerate(pages_html):
        page_num = pi + 1
        end_label = " END" if page_num == len(pages_html) else ""
        if pi == 0:
            # Clean double-term in title formatting
            title_period = period_full.strip()
            if title_period.upper().endswith("TERM"):
                title_text = f"{title_period} {term_roman}"
            else:
                title_text = f"{title_period} TERM {term_roman}"
                
            header_html = f"""  <div class="nq-header">
    <div class="nq-school">{school_name}</div>
    <div class="nq-exam-title">{title_text} EXAMINATION &ndash; {year}</div>
    <div class="nq-class-info">{class_level.upper()} ({age_range} YEARS)</div>
    <div class="nq-la-title">LEARNING AREA {learning_area[-1]}: {la_name}</div>
  </div>
  <div class="nq-fields">
    <div class="nq-field-row">My name is: <span class="nq-field-line">&nbsp;</span></div>
    <div class="nq-field-row">My School is: <span class="nq-field-line">&nbsp;</span></div>
    <div class="nq-field-row">I am in: <span style="min-width:120px" class="nq-field-line">&nbsp;</span>&nbsp;&nbsp;Date: <span style="min-width:100px" class="nq-field-line">&nbsp;</span></div>
  </div>"""
        else:
            header_html = ""
        footer_html = f'<div class="nq-footer"><span>{school_name} &nbsp; {class_level} {learning_area}</span><span>Page{page_num}{end_label}</span></div>'
        html += f'<div class="nq-page">\n{header_html}\n{page_content}\n{footer_html}\n</div>\n'

    html += "</body>\n</html>"
    return html
