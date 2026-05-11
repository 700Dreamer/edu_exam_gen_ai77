# Master Syllabus Definition (Registry)
# Comprehensive Registry for P1-S6

MASTER_SYLLABUS = {
    "Pre-Primary": {
        "Baby Class": ["Colors", "Shapes", "Scribbling", "Singing", "Socializing"],
        "Middle Class": ["Numbers 1-10", "Letter sounds", "Drawing", "Self-care", "Community"],
        "Top Class": ["Writing names", "Number operations (simple)", "Reading (3-letter words)", "Environment", "Religious stories"]
    },
    "Mathematics": {
        "Primary 1": ["Sets", "Count & Write numbers", "Addition", "Subtraction", "Shapes", "Days of Week"],
        "Primary 2": ["Sets", "Number Values", "Addition with carrying", "Subtraction with borrowing", "Length", "Weight", "Capacity"],
        "Primary 3": ["Fractions", "Graphs", "Time", "Money", "Geometry", "Algebraic Expressions"],
        "Primary 4": ["Place Value", "Operations on whole numbers", "Fractions", "Decimals", "Integers", "Geometry", "Data"],
        "Primary 5": ["Set Concepts", "Whole Numbers", "Operations", "Fractions", "Decimals", "Ratios", "Data Handling"],
        "Primary 6": ["Sets", "Whole Numbers", "Fractions", "Decimals", "Percentages", "Integers", "Geometry", "Algebra"],
        "Primary 7": ["Sets", "Whole Numbers", "Fractions", "Decimals", "Integers", "Ratio & Proportion", "Percentages", "Time", "Money", "Capacity", "Geometry", "Algebra", "Coordinate Geometry"],
        "Senior 1": ["Sets", "Number Bases", "Fractions/Decimals", "Integers", "Algebraic Expressions", "Geometry", "Business Math"],
        "Senior 2": ["Mapping/Relations", "Vectors", "Matrices", "Simultaneous Equations", "Pythagoras Theorem", "Trigonometry"],
        "Senior 3": ["Quadratic Equations", "Circle Properties", "Similarity", "Enlargement", "Business Math - Interest"],
        "Senior 4": ["Linear Programming", "Probability", "Statistics", "Trigonometry 3D", "Loci", "Transformation Geometry"],
        "Senior 5": ["Differentiation", "Integration", "Complex Numbers", "Algebra 2", "Coordinate Geometry of Circle"],
        "Senior 6": ["Numerical Methods", "Mechanics", "Probability Distributions", "Differential Equations"]
    },
    "Science": {
        "Primary 1": ["Living things", "Our Body", "Food", "Plants", "Health & Sanitation"],
        "Primary 2": ["Environment", "Animals", "Insects", "Human Body", "Weather", "Soil"],
        "Primary 3": ["Systems", "Birds", "Plants", "Water", "Accidents", "Personal Hygiene"],
        "Primary 4": ["Plants", "Insects", "Personal Hygiene", "Environment", "Human Body", "Weather"],
        "Primary 5": ["Poultry", "Bee Keeping", "Soil", "Matter", "Human Body (Immune System)", "First Aid"],
        "Primary 6": ["Accidents/Safety", "Fungi", "Cattle", "Human Body (Respiratory)", "Sound", "Environment"],
        "Primary 7": ["Human Body (Circulation)", "Excretion", "Plants (Reproduction)", "Energy", "Machines", "Electricity", "Magnetism"]
    },
    "English": {
        "Primary 1": ["Self", "Home", "School", "Community", "Animals", "Prepositions", "Tenses"],
        "Primary 2": ["Family", "Health", "Food", "Numbers", "Days/Months", "Conjunctions"],
        "Primary 3": ["Hobbies", "Occupations", "Travel", "Compass Directions", "Punctuation"],
        "Primary 4": ["Describing People", "Dictionary Use", "Pronouns", "Letter Writing"],
        "Primary 5": ["Similes", "Adjectives", "Opposites", "Future Tense", "Telephones"],
        "Primary 6": ["Debating", "Post Office", "Hotels", "Travel", "Environment"],
        "Primary 7": ["Direct/Indirect Speech", "Active/Passive Voice", "Punctuation", "Composition", "Letter Writing", "Poetry"],
        "Senior 1": ["Grammar", "Creative Writing", "Comprehension", "Poetry Analysis", "Plays"],
        "Senior 4": ["Comprehension", "Summary Writing", "Grammar Usage", "Creative Writing", "Literature Analysis"]
    },
    "Social Studies": {
        "Primary 1": ["Family", "School", "Things we do", "People at work"],
        "Primary 2": ["Our Community", "Social Services", "Peace & Security", "Weather"],
        "Primary 3": ["Map Skills", "District History", "Livelihood", "Management of resources"],
        "Primary 4": ["Physical Features", "Vegetation", "People of our District", "Leaders"],
        "Primary 5": ["Regions of Uganda", "Uganda's Independence", "Our Neighbors", "Natural Resources"],
        "Primary 6": ["East African Community", "Resources of East Africa", "History of EA", "Government"],
        "Primary 7": ["History of East Africa", "Political Organization", "Culture/Home", "Economy", "Map Reading", "Citizenship"]
    },
    "Physics": {
        "Senior 1": ["Measurement", "Simple Machines", "Density", "Magnetism"],
        "Senior 2": ["Force", "Newton's Laws", "Pressure", "Archimedes Principle"],
        "Senior 3": ["Light", "Lenses", "Waves", "Sound"],
        "Senior 4": ["Mechanics", "Heat", "Light", "Sound", "Electricity", "Magnetism", "Modern Physics"],
        "Senior 6": ["Mechanics (Projectiles)", "Thermodynamics", "Electromagnetism", "Quantum Physics"]
    },
    "Chemistry": {
        "Senior 1": ["Lab Safety", "States of Matter", "Atoms", "Elements"],
        "Senior 2": ["Chemical Reactions", "Gas Laws", "Acids & Bases"],
        "Senior 3": ["Periodic Table", "Chemical Bonding", "Electrochemistry"],
        "Senior 4": ["Atomic Structure", "Periodic Table", "Bonding", "Electrolysis", "Organic Chemistry", "Metals", "Salts"],
        "Senior 6": ["Organic Chemistry (Adv)", "Physical Chemistry", "Transition Elements", "Kinetics"]
    },
    "Biology": {
        "Senior 1": ["Introduction to Biology", "Cells", "Classification"],
        "Senior 4": ["Cells", "Classification", "Nutrition", "Transport", "Respiration", "Excretion", "Genetics", "Ecology"],
        "Senior 6": ["Biochemistry", "Molecular Biology", "Evolution", "Ecology & Conservation"]
    },
    "Religious Education": {
        "Primary 7": ["God's Creation", "Jesus Christ", "Holy Spirit", "Community Service", "Values"]
    },
    "ICT": {
        "Senior 4": ["Computer Basics", "Word Processing", "Spreadsheets", "Internet Safety", "Binary Systems"]
    }
}

ALL_SUBJECTS = sorted(list(MASTER_SYLLABUS.keys()))
ALL_LEVELS = ["Baby Class", "Middle Class", "Top Class"] + [f"Primary {i}" for i in range(1, 8)] + [f"Senior {i}" for i in range(1, 7)]

def get_master_topics(subject: str, level: str):
    return MASTER_SYLLABUS.get(subject, {}).get(level, [])

def normalize_level(level_str: str):
    if not level_str: return "Unknown"
    l = str(level_str).strip().upper()
    # Normalize P1 -> Primary 1, S4 -> Senior 4
    if l.startswith("P") and l[1:].isdigit():
        return f"Primary {l[1:]}"
    if l.startswith("S") and l[1:].isdigit():
        return f"Senior {l[1:]}"
    # Standardize phrasing
    if "PRIMARY" in l: return l.capitalize()
    if "SENIOR" in l: return l.capitalize()
    return level_str
