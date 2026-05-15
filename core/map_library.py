"""
EduQuest SVG Map Library — Geographically Calibrated for Uganda's National Curriculum.
Maps are matched by keyword and embedded directly into exam papers.
Coordinate system: x = 10 + (lon-28)*41.4, y = 10 + (5-lat)*28.2
"""

# ─── KEYWORD ROUTING ────────────────────────────────────────────────────────
MAP_ROUTES = {
    "east_africa": [
        "east africa", "east african", "eac", "east african community",
        "great lakes", "great rift valley", "rift valley region"
    ],
    "uganda": [
        "map of uganda", "blank map of uganda", "outline of uganda",
        "regions of uganda", "districts of uganda", "uganda showing",
        "map showing uganda", "uganda map", "locate on uganda"
    ],
    "africa": [
        "map of africa", "african continent", "africa showing",
        "continent of africa", "blank map of africa"
    ],
}

from typing import Optional

def get_best_map(question_text: str) -> Optional[str]:
    """Returns the best-matching SVG for the question, or None to use Imagen 4."""
    text = question_text.lower()
    if any(k in text for k in MAP_ROUTES["east_africa"]):
        return EAST_AFRICA_SVG
    if any(k in text for k in MAP_ROUTES["uganda"]):
        return UGANDA_SVG
    if any(k in text for k in MAP_ROUTES["africa"]):
        return AFRICA_SVG
    return None


# ─── EAST AFRICA MAP ─────────────────────────────────────────────────────────
# Coord system: x=10+(lon-28)*41.4  y=10+(5-lat)*28.2
# Covers 28°E–42°E, 5°N–12°S
EAST_AFRICA_SVG = """
<svg viewBox="0 0 600 510" width="100%" xmlns="http://www.w3.org/2000/svg"
     style="border:1px solid #ccc; border-radius:4px; background:#e8f4f8; font-family:serif;">
  <defs>
    <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke="#aaa" stroke-width="1"/>
    </pattern>
  </defs>

  <!-- DRC (partial west) -->
  <polygon points="10,10 64,10 64,141 68,181 50,200 10,200"
           fill="#e8e0d0" stroke="#555" stroke-width="1.2"/>
  <text x="30" y="110" font-size="9" fill="#555" transform="rotate(-90,30,110)">D.R. Congo</text>

  <!-- South Sudan (partial south) -->
  <polygon points="64,10 260,10 272,44 169,52 123,52 64,52"
           fill="#ddeedd" stroke="#555" stroke-width="1.2"/>
  <text x="160" y="30" text-anchor="middle" font-size="10" fill="#333">South Sudan</text>

  <!-- Ethiopia (partial) -->
  <polygon points="260,10 400,10 390,80 320,100 272,95 272,44"
           fill="#f0e8c8" stroke="#555" stroke-width="1.2"/>
  <text x="330" y="55" text-anchor="middle" font-size="10" fill="#333">Ethiopia</text>

  <!-- Uganda -->
  <polygon points="123,52 169,52 260,44 272,95 255,130 186,141 144,169 68,181 64,141 81,124 114,101"
           fill="#b8ddb8" stroke="#333" stroke-width="2"/>
  <text x="168" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#1a4a1a">UGANDA</text>

  <!-- Kenya -->
  <polygon points="260,44 390,38 420,80 390,180 340,220 300,260 255,170 255,130 272,95"
           fill="#f5d9a0" stroke="#333" stroke-width="1.8"/>
  <text x="340" y="140" text-anchor="middle" font-size="12" font-weight="bold" fill="#5a3a00">KENYA</text>

  <!-- Rwanda -->
  <polygon points="68,181 100,181 108,210 80,218 60,205"
           fill="#c8d8f0" stroke="#333" stroke-width="1.5"/>
  <text x="82" y="200" text-anchor="middle" font-size="7" fill="#222">Rwanda</text>

  <!-- Burundi -->
  <polygon points="80,218 108,210 112,240 85,248 68,235"
           fill="#f0c8d8" stroke="#333" stroke-width="1.5"/>
  <text x="90" y="232" text-anchor="middle" font-size="7" fill="#222">Burundi</text>

  <!-- Tanzania -->
  <polygon points="144,169 255,170 300,260 290,310 260,360 210,400 140,405 100,370 80,310 80,248 112,240 108,210 100,181"
           fill="#fde8c0" stroke="#333" stroke-width="1.8"/>
  <text x="190" y="310" text-anchor="middle" font-size="12" font-weight="bold" fill="#5a3a00">TANZANIA</text>

  <!-- Lake Victoria -->
  <polygon points="186,141 255,155 248,190 210,215 165,218 144,197 144,169"
           fill="#87ceeb" stroke="#1a6a9a" stroke-width="1.5"/>
  <text x="198" y="185" text-anchor="middle" font-size="9" fill="#1a4f72">L. Victoria</text>

  <!-- Lake Albert -->
  <ellipse cx="82" cy="118" rx="10" ry="20" fill="#87ceeb" stroke="#1a6a9a" stroke-width="1"/>
  <text x="55" y="116" font-size="7" fill="#1a4f72">L.Albert</text>

  <!-- Lake Tanganyika -->
  <ellipse cx="85" cy="295" rx="8" ry="45" fill="#87ceeb" stroke="#1a6a9a" stroke-width="1"/>
  <text x="20" y="295" font-size="7" fill="#1a4f72">L.Tang.</text>

  <!-- Somalia (partial) -->
  <polygon points="390,38 580,10 560,180 420,230 390,180 420,80"
           fill="#f0e8c8" stroke="#555" stroke-width="1.2"/>
  <text x="470" y="120" text-anchor="middle" font-size="10" fill="#555">Somalia</text>

  <!-- Kampala marker -->
  <circle cx="185" cy="145" r="4" fill="red"/>
  <text x="192" y="142" font-size="8" fill="red">Kampala ★</text>

  <!-- Nairobi marker -->
  <circle cx="295" cy="185" r="4" fill="red"/>
  <text x="302" y="182" font-size="8" fill="red">Nairobi ★</text>

  <!-- Compass Rose -->
  <g transform="translate(555,75)">
    <text x="0" y="-18" text-anchor="middle" font-size="11" font-weight="bold">N</text>
    <polygon points="0,-15 -5,0 0,5 5,0" fill="#333"/>
    <polygon points="0,15 -5,0 0,-5 5,0" fill="#aaa"/>
    <text x="0" y="28" text-anchor="middle" font-size="9">S</text>
    <text x="-22" y="4" text-anchor="middle" font-size="9">W</text>
    <text x="22" y="4" text-anchor="middle" font-size="9">E</text>
  </g>

  <!-- Scale bar -->
  <g transform="translate(30,480)">
    <rect x="0" y="0" width="80" height="6" fill="#333"/>
    <rect x="80" y="0" width="80" height="6" fill="white" stroke="#333"/>
    <text x="0" y="18" font-size="8">0</text>
    <text x="72" y="18" font-size="8">200km</text>
    <text x="152" y="18" font-size="8">400km</text>
  </g>

  <!-- Map Title -->
  <text x="300" y="490" text-anchor="middle" font-size="10" font-style="italic" fill="#555">East Africa — EduQuest Reference Map</text>
</svg>
"""

# ─── UGANDA MAP ──────────────────────────────────────────────────────────────
UGANDA_SVG = """
<svg viewBox="0 0 420 400" width="100%" xmlns="http://www.w3.org/2000/svg"
     style="border:1px solid #ccc; border-radius:4px; background:#e8f4f8; font-family:serif;">

  <!-- Uganda outline -->
  <polygon points="80,30 200,25 270,28 295,90 280,140 235,160 200,175 160,178 110,170 60,180 45,140 55,100 68,60"
           fill="#c8e6c8" stroke="#333" stroke-width="2.5"/>

  <!-- Region borders (internal dashed) -->
  <!-- Northern region horizontal line -->
  <line x1="68" y1="90" x2="290" y2="88" stroke="#777" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Eastern/Central vertical -->
  <line x1="200" y1="88" x2="220" y2="178" stroke="#777" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Western/Central vertical -->
  <line x1="115" y1="88" x2="110" y2="170" stroke="#777" stroke-width="1" stroke-dasharray="4,3"/>

  <!-- Region labels -->
  <text x="175" y="62" text-anchor="middle" font-size="12" fill="#1a1a1a">Northern</text>
  <text x="255" y="128" text-anchor="middle" font-size="12" fill="#1a1a1a">Eastern</text>
  <text x="160" y="128" text-anchor="middle" font-size="12" fill="#1a1a1a">Central</text>
  <text x="78" y="128" text-anchor="middle" font-size="12" fill="#1a1a1a">Western</text>

  <!-- Lake Victoria (SE corner) -->
  <polygon points="200,175 235,160 280,178 268,215 240,230 200,225 185,205"
           fill="#87ceeb" stroke="#1a6a9a" stroke-width="1.5"/>
  <text x="230" y="205" text-anchor="middle" font-size="10" fill="#1a4f72">L. Victoria</text>

  <!-- Lake Albert (W) -->
  <ellipse cx="50" cy="112" rx="9" ry="22" fill="#87ceeb" stroke="#1a6a9a" stroke-width="1.2"/>
  <text x="15" y="112" font-size="8" fill="#1a4f72">L.Albert</text>

  <!-- Lake Edward (SW) -->
  <ellipse cx="62" cy="162" rx="8" ry="14" fill="#87ceeb" stroke="#1a6a9a" stroke-width="1.2"/>
  <text x="20" y="162" font-size="8" fill="#1a4f72">L.Edward</text>

  <!-- Lake Kyoga (central) -->
  <ellipse cx="178" cy="108" rx="22" ry="10" fill="#87ceeb" stroke="#1a6a9a" stroke-width="1"/>
  <text x="178" y="107" text-anchor="middle" font-size="7" fill="#1a4f72">L.Kyoga</text>

  <!-- River Nile (approximate) -->
  <path d="M175,108 Q140,95 100,60 Q90,45 80,30" fill="none" stroke="#4a90c8" stroke-width="2" stroke-dasharray="5,2"/>
  <text x="108" y="78" font-size="8" fill="#1a4f72" transform="rotate(-55,108,78)">R. Nile</text>

  <!-- Mt. Elgon (E) -->
  <polygon points="280,112 290,90 300,112" fill="#a0a0a0" stroke="#555" stroke-width="1"/>
  <text x="310" y="104" font-size="8" fill="#555">Mt. Elgon</text>

  <!-- Rwenzori Mts (W) -->
  <polygon points="52,140 60,122 68,140" fill="#a0a0a0" stroke="#555" stroke-width="1"/>
  <text x="20" y="136" font-size="7" fill="#555">Rwenzori</text>

  <!-- Kampala -->
  <circle cx="195" cy="158" r="5" fill="red"/>
  <text x="205" y="155" font-size="9" fill="red" font-weight="bold">★ Kampala</text>

  <!-- Neighbour labels -->
  <text x="175" y="15" text-anchor="middle" font-size="9" fill="#666" font-style="italic">South Sudan</text>
  <text x="318" y="120" font-size="9" fill="#666" font-style="italic">Kenya</text>
  <text x="175" y="250" text-anchor="middle" font-size="9" fill="#666" font-style="italic">Tanzania</text>
  <text x="15" y="80" font-size="9" fill="#666" font-style="italic">DRC</text>
  <text x="10" y="195" font-size="9" fill="#666" font-style="italic">Rwanda</text>

  <!-- Compass Rose -->
  <g transform="translate(385,50)">
    <text x="0" y="-16" text-anchor="middle" font-size="11" font-weight="bold">N</text>
    <polygon points="0,-13 -4,0 0,4 4,0" fill="#333"/>
    <polygon points="0,13 -4,0 0,-4 4,0" fill="#aaa"/>
    <text x="0" y="26" text-anchor="middle" font-size="9">S</text>
    <text x="-20" y="4" text-anchor="middle" font-size="9">W</text>
    <text x="20" y="4" text-anchor="middle" font-size="9">E</text>
  </g>

  <!-- Scale bar -->
  <g transform="translate(30,370)">
    <rect x="0" y="0" width="60" height="5" fill="#333"/>
    <rect x="60" y="0" width="60" height="5" fill="white" stroke="#333"/>
    <text x="0" y="16" font-size="8">0</text>
    <text x="52" y="16" font-size="8">100km</text>
    <text x="112" y="16" font-size="8">200km</text>
  </g>

  <text x="210" y="390" text-anchor="middle" font-size="9" font-style="italic" fill="#555">Uganda — EduQuest Reference Map</text>
</svg>
"""

# ─── AFRICA CONTINENTAL MAP ──────────────────────────────────────────────────
AFRICA_SVG = """
<svg viewBox="0 0 400 480" width="100%" xmlns="http://www.w3.org/2000/svg"
     style="border:1px solid #ccc; border-radius:4px; background:#e8f4f8; font-family:serif;">

  <!-- Africa continental outline (simplified) -->
  <polygon points="
    180,15  220,12  250,20  285,15  310,30
    330,60  330,90  320,120 330,150 325,180
    340,210 350,240 340,270 320,300 300,330
    280,360 250,390 220,410 200,415
    175,410 155,395 130,370 110,345
    90,310  75,280  65,250  60,220
    50,190  45,160  50,130  55,100
    65,70   80,50   100,30  130,18
  " fill="#f5deb3" stroke="#555" stroke-width="2"/>

  <!-- Horn of Africa -->
  <polygon points="310,120 330,90 360,100 380,130 340,170 320,150 330,130"
           fill="#f5deb3" stroke="#555" stroke-width="1.5"/>

  <!-- Mediterranean coast indent -->
  <path d="M130,18 Q155,8 180,15 Q220,12 250,20 Q285,15 310,30"
        fill="#e8f4f8" stroke="#555" stroke-width="1"/>

  <!-- Key country borders (simplified) -->
  <!-- Egypt/Sudan line -->
  <line x1="240" y1="65" x2="290" y2="68" stroke="#888" stroke-width="0.8" stroke-dasharray="3,2"/>
  <!-- Nigeria area -->
  <line x1="118" y1="165" x2="145" y2="165" stroke="#888" stroke-width="0.8" stroke-dasharray="3,2"/>

  <!-- Major features -->
  <!-- Sahara label -->
  <text x="195" y="110" text-anchor="middle" font-size="11" fill="#c8a060" font-style="italic">Sahara Desert</text>

  <!-- Congo Basin -->
  <text x="175" y="240" text-anchor="middle" font-size="9" fill="#555">Congo Basin</text>

  <!-- Key labels -->
  <text x="240" y="80" text-anchor="middle" font-size="9" fill="#333">Egypt</text>
  <text x="240" y="135" text-anchor="middle" font-size="9" fill="#333">Sudan/Ethiopia</text>
  <text x="115" y="165" text-anchor="middle" font-size="9" fill="#333">Nigeria</text>
  <text x="200" y="200" text-anchor="middle" font-size="9" fill="#333">D.R. Congo</text>

  <!-- East Africa region highlight -->
  <rect x="250" y="175" width="70" height="90" fill="rgba(100,180,100,0.25)" stroke="#2a8a2a" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="285" y="220" text-anchor="middle" font-size="8" fill="#1a5a1a">East Africa</text>

  <!-- South Africa -->
  <text x="195" y="390" text-anchor="middle" font-size="9" fill="#333">South Africa</text>

  <!-- Madagascar -->
  <polygon points="340,285 355,270 365,300 360,340 345,345 335,315"
           fill="#f5deb3" stroke="#555" stroke-width="1.5"/>
  <text x="350" y="310" text-anchor="middle" font-size="7" fill="#555">Mada-gascar</text>

  <!-- Compass -->
  <g transform="translate(370,40)">
    <text x="0" y="-14" text-anchor="middle" font-size="11" font-weight="bold">N</text>
    <polygon points="0,-12 -4,0 0,4 4,0" fill="#333"/>
    <polygon points="0,12 -4,0 0,-4 4,0" fill="#aaa"/>
    <text x="0" y="24" text-anchor="middle" font-size="9">S</text>
    <text x="-18" y="4" text-anchor="middle" font-size="9">W</text>
    <text x="18" y="4" text-anchor="middle" font-size="9">E</text>
  </g>

  <!-- Scale -->
  <g transform="translate(20,450)">
    <rect x="0" y="0" width="70" height="5" fill="#333"/>
    <rect x="70" y="0" width="70" height="5" fill="white" stroke="#333"/>
    <text x="0" y="16" font-size="8">0</text>
    <text x="62" y="16" font-size="8">1000km</text>
    <text x="132" y="16" font-size="8">2000km</text>
  </g>

  <text x="200" y="472" text-anchor="middle" font-size="9" font-style="italic" fill="#555">Africa — EduQuest Reference Map</text>
</svg>
"""
