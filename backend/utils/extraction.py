import re
import json

def extract_metadata(text, category):
    """
    Extracts metadata from text based on the document category.
    Returns a dictionary of extracted fields.
    """
    metadata = {}
    
    if category == "Invoice":
        metadata = extract_invoice_metadata(text)
    elif category == "Contract":
        metadata = extract_contract_metadata(text)
    elif category == "ID":
        metadata = extract_id_metadata(text)
    
    return json.dumps(metadata)

def extract_invoice_metadata(text):
    data = {}
    
    # Simple Heuristic Regex Patterns
    
    # Amount (e.g., $1,234.56 or 1234.56)
    # Looking for 'Total' or 'Amount' followed by numbers
    amount_match = re.search(r'(?:Total|Amount|Balance|Due)[\s\:\$]*([\d,\.]+)', text, re.IGNORECASE)
    if amount_match:
        data['total_amount'] = amount_match.group(1)
        
    # Date (e.g., 01/01/2024 or 2024-01-01)
    date_match = re.search(r'(?:Date|Due)[\s\:]*(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})', text, re.IGNORECASE)
    if date_match:
        data['date'] = date_match.group(1)
        
    # Vendor (Very hard with simple regex, usually requires NER or known vendor list)
    # Placeholder: First line or capitalized words near top?
    # For now, let's just look for "Vendor:" or "From:"
    vendor_match = re.search(r'(?:Vendor|From|Bill To)[\s\:]*([A-Za-z0-9\s,]+)', text, re.IGNORECASE)
    if vendor_match:
        data['vendor'] = vendor_match.group(1).split('\n')[0].strip()
        
    return data

def extract_contract_metadata(text):
    data = {}
    
    # Date
    date_match = re.search(r'(?:Date|Effective)[\s\:]*(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})', text, re.IGNORECASE)
    if date_match:
        data['contract_date'] = date_match.group(1)
        
    # Parties (looking for "Between X and Y")
    parties_match = re.search(r'Between\s+(.*?)\s+and\s+(.*?)[\.,\n]', text, re.IGNORECASE)
    if parties_match:
        data['party_1'] = parties_match.group(1).strip()
        data['party_2'] = parties_match.group(2).strip()
        
    return data

def extract_id_metadata(text):
    data = {}
    
    # ID Number (Generic 8+ digits)
    id_match = re.search(r'(?:ID|No|Number)[\s\.\:]*([A-Z0-9-]{6,})', text, re.IGNORECASE)
    if id_match:
        data['id_number'] = id_match.group(1)
        
    return data
