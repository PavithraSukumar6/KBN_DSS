# Risk Levels for different categories
RISK_LEVELS = {
    "Invoice": "Low",
    "Contract": "Medium",
    "ID": "High",
    "Report": "Low",
    "HR": "High",
    "Legal": "Medium",
    "Other": "High"
}

def classify_document(text):
    """
    Classifies a document based on keywords found in the text.
    Returns a tuple: (Category, Confidence_Score)
    """
    text_lower = text.lower()
    
    # Define keywords for each category
    keywords = {
        "Invoice": ["invoice", "total", "amount", "due date", "bill to", "tax"],
        "Contract": ["contract", "agreement", "parties", "signature", "terms"],
        "ID": ["identity", "passport", "driver", "license", "dob", "name"],
        "Report": ["report", "summary", "analysis", "conclusion", "table of contents"],
        "HR": ["employee", "payroll", "resume", "hiring", "compliance", "salary"],
        "Legal": ["legal", "court", "lawsuit", "attorney", "proceedings", "deposition"]
    }
    
    scores = {category: 0 for category in keywords}
    
    # Calculate scores based on keyword presence
    for category, terms in keywords.items():
        for term in terms:
            if term in text_lower:
                scores[category] += 1
                
    # Find the category with the highest score
    best_category = max(scores, key=scores.get)
    max_score = scores[best_category]
    
    # Determine confidence (Simple heuristic)
    if max_score >= 3:
        confidence = "High"
    elif max_score > 0:
        confidence = "Medium"
    else:
        best_category = "Other"
        confidence = "Low"
        
    return best_category, confidence

def get_risk_level(category):
    return RISK_LEVELS.get(category, "High")

def suggest_metadata_from_all(filename, text=""):
    """
    Scans filename and text for suggestions.
    """
    combined = (filename + " " + text).lower()
    
    suggestions = {}
    
    # Category suggestions based on specific keywords
    if "invoice" in combined or "bill" in combined:
        suggestions['category'] = "Invoice"
    elif "contract" in combined or "agreement" in combined:
        suggestions['category'] = "Contract"
    elif "hr" in combined or "employee" in combined:
        suggestions['category'] = "HR"
    elif "legal" in combined or "court" in combined:
        suggestions['category'] = "Legal"

    # Department suggestions based on keywords
    dept_keywords = {
        "Finance": ["finance", "invoice", "payroll", "bill", "tax", "payment"],
        "HR": ["hr", "employee", "hiring", "resume", "staff"],
        "Legal": ["legal", "court", "contract", "agreement", "lawsuit"],
        "Operations": ["ops", "operations", "logistics", "supply"],
    }
    
    for dept, terms in dept_keywords.items():
        for term in terms:
            if term in combined:
                suggestions['department'] = dept
                break
        if 'department' in suggestions: break

    # Date suggestion (very simple regex check)
    import re
    date_match = re.search(r'(\d{4}[-]\d{2}[-]\d{2})', combined)
    if date_match:
        suggestions['date'] = date_match.group(1)
        
    return suggestions
