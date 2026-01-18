
def classify_document(text):
    """
    Classifies document based on keywords in OCR text.
    Returns: 'Invoice', 'Receipt', 'Contract', 'Report', or 'Unknown'
    """
    text = text.lower()
    
    if any(keyword in text for keyword in ['invoice', 'bill to', 'amount due', 'tax invoice']):
        return 'Invoice', 0.95
    
    if any(keyword in text for keyword in ['receipt', 'transaction', 'payment', 'total']):
        # Receipt / Invoice overlap, but 'receipt' keyword usually distinct for POS
        return 'Receipt', 0.85
        
    if any(keyword in text for keyword in ['contract', 'agreement', 'undersigned', 'parties']):
        return 'Contract', 0.90
        
    if any(keyword in text for keyword in ['report', 'summary', 'analysis', 'status']):
        return 'Report', 0.80
        
    return 'Unknown', 0.0

def suggest_metadata_from_all(filename, text=None):
    """
    Fallback metadata suggestion based on filename.
    """
    suggestions = {}
    lower_name = filename.lower()
    if 'invoice' in lower_name:
        suggestions['category'] = 'Invoice'
    elif 'receipt' in lower_name:
        suggestions['category'] = 'Receipt'
    elif 'contract' in lower_name:
        suggestions['category'] = 'Contract'
    return suggestions

def get_risk_level(category):
    """
    Determines risk level based on category.
    """
    high_risk = ['Contract', 'Legal', 'Tax']
    if category in high_risk:
        return 'High'
    return 'Low'
