import re

def process_tikz_safeguard(raw_text):
    if not raw_text:
        return raw_text
    
    if "\\begin{tikzpicture}" not in raw_text:
        if any(cmd in raw_text for cmd in ["\\draw", "\\node", "\\fill", "\\path", "\\coordinate"]):
            clean_text = re.sub(r'```(?:tikz|latex)?(.*?)```', r'\1', raw_text, flags=re.DOTALL)
            raw_text = f"\\begin{{tikzpicture}}\n{clean_text.strip()}\n\\end{{tikzpicture}}"

    clean_text = re.sub(r'```(?:tikz|latex)?\s*(\\begin\{tikzpicture\})', r'\1', raw_text)
    clean_text = re.sub(r'(\\end\{tikzpicture\})\s*```', r'\1', clean_text)
    clean_text = re.sub(r'<script type="text/tikz">\s*(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\s*</script>', r'\1', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})', r'<script type="text/tikz">\n\1\n</script>', clean_text, flags=re.DOTALL)
    return clean_text

print(process_tikz_safeguard("\\draw (0,0) circle (1); \\node at (0.7,0.7) {7};"))
