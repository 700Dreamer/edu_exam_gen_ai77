import math
from core.syllabus_master import get_master_topics

def generate_exam_blueprint(subject: str, level: str, term: str, question_count: int, specific_topic: str = "") -> dict:
    """
    Generates a deterministic mapping of Question Numbers to specific syllabus topics.
    Ensures pedagogical pacing (early topics in early questions, complex later).
    Returns a dictionary like: {"Q1": "Sets", "Q2": "Whole Numbers", ...}
    """
    blueprint = {}
    
    # 1. If a specific topic is forced, map all questions to it.
    if specific_topic and specific_topic.strip():
        for i in range(1, question_count + 1):
            blueprint[f"Q{i}"] = specific_topic.strip()
        return blueprint

    # 2. Get master syllabus topics
    master_topics = get_master_topics(subject, level)
    
    # Fallback if no topics exist
    if not master_topics:
        for i in range(1, question_count + 1):
            blueprint[f"Q{i}"] = "General Subject Knowledge"
        return blueprint

    # 3. Filter topics based on Term
    # Term 1: First 33% | Term 2: First 66% | Term 3 (or EOT/Mock): 100%
    term_lower = term.lower()
    if "term 1" in term_lower or "bot" in term_lower:
        cutoff = math.ceil(len(master_topics) * 0.33)
        available_topics = master_topics[:cutoff]
    elif "term 2" in term_lower:
        cutoff = math.ceil(len(master_topics) * 0.66)
        available_topics = master_topics[:cutoff]
    else:
        # Term 3 or End of Year tests whole syllabus
        available_topics = master_topics

    if not available_topics:
        available_topics = master_topics

    # 4. Chronological Mapping (Distribute topics sequentially)
    # E.g. 20 questions, 5 topics => Q1-Q4 get Topic 1, Q5-Q8 get Topic 2...
    topics_len = len(available_topics)
    questions_per_topic = max(1, question_count / topics_len)
    
    for i in range(1, question_count + 1):
        # Calculate which topic index this question falls into
        topic_idx = int((i - 1) / questions_per_topic)
        # Cap index in case of floating point rounding issues
        topic_idx = min(topic_idx, topics_len - 1)
        
        blueprint[f"Q{i}"] = available_topics[topic_idx]

    return blueprint
