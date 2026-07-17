def get_edumerc_policy(level: str) -> dict:
    """
    Returns the distribution of questions across current and previous class levels.
    E.g. For 'Primary 5' (P.5), returns {"Primary 5": 0.60, "Primary 4": 0.25, "Primary 3": 0.15}
    """
    # Normalize level
    l = level.lower().replace("p.", "primary ").replace("p", "primary ")
    
    if "baby" in l:
        return {"Baby Class": 1.0}
    elif "middle" in l:
        return {"Middle Class": 0.80, "Baby Class": 0.20}
    elif "top" in l:
        return {"Top Class": 0.60, "Middle Class": 0.30, "Baby Class": 0.10}
        
    elif "primary 1" in l:
        return {"Primary 1": 0.70, "Top Class": 0.30}
    elif "primary 2" in l:
        return {"Primary 2": 0.70, "Primary 1": 0.30}
    elif "primary 3" in l:
        return {"Primary 3": 0.70, "Primary 2": 0.30}
        
    elif "primary 4" in l:
        return {"Primary 4": 0.65, "Primary 3": 0.20, "Primary 2": 0.15}
    elif "primary 5" in l:
        return {"Primary 5": 0.60, "Primary 4": 0.25, "Primary 3": 0.15}
    elif "primary 6" in l:
        return {"Primary 6": 0.50, "Primary 5": 0.40, "Primary 4": 0.10}
    elif "primary 7" in l:
        return {"Primary 7": 0.20, "Primary 6": 0.30, "Primary 5": 0.40, "Primary 4": 0.10}
        
    # Default fallback for Secondary or unrecognized
    return {level: 1.0}

def get_allowed_terms(current_term: str) -> list:
    """
    Returns the allowed terms to query based on EDUMERC policy (Current + Previous only).
    Example: Term 2 -> ['Term 1', 'Term 2']
    """
    t = current_term.lower()
    if "term 1" in t or "bot" in t:
        return ["Term 1", "Unknown"]
    elif "term 2" in t:
        return ["Term 1", "Term 2", "Unknown"]
    elif "term 3" in t or "eot" in t or "mock" in t or "ple" in t:
        return ["Term 1", "Term 2", "Term 3", "Unknown"]
    
    # Default
    return [current_term, "Unknown"]
