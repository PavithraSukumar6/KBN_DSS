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
    
    # 1. Invoice Number
    # Pattern: /INV[- ]?\d+/ or /Invoice #:\s*(\d+)/
    inv_match = re.search(r'(?:INV[- ]?\d+)|(?:Invoice\s*#[:\.]?\s*([\w-]+))', text, re.IGNORECASE)
    if inv_match:
        # Group 1 might be None if the first part of OR matched
        data['invoice_number'] = inv_match.group(1) if inv_match.group(1) else inv_match.group(0)
    else:
        # Fallback generic
        inv_match_generic = re.search(r'Invoice\s*(?:No|Number)?[:\.]?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if inv_match_generic:
            data['invoice_number'] = inv_match_generic.group(1)

    # 2. Date
    # Pattern: /\d{2}[/-]\d{2}[/-]\d{4}/ (DD-MM-YYYY or MM-DD-YYYY or similar)
    date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', text)
    if date_match:
        data['date'] = date_match.group(1)
        
    # 3. Total Amount
    amount_match = re.search(r'(?:Total|Amount|Balance|Due)[\s\:\$]*([\d,\.]+)', text, re.IGNORECASE)
    if amount_match:
        data['total_amount'] = amount_match.group(1)

    # 4. Contextual Parsing for Companies
    # "Bill To:" -> Addressed Company
    bill_to_match = re.search(r'(?:Bill|Ship)\s*To[:\.]?\s*([^\n]+)', text, re.IGNORECASE)
    if bill_to_match:
        data['addressed_company'] = bill_to_match.group(1).strip()
        
    # "From:" -> Issuing Company
    # Often the issuing company is at the very top or explicitly "From:"
    from_match = re.search(r'(?:From|Vendor)[:\.]?\s*([^\n]+)', text, re.IGNORECASE)
    if from_match:
        data['issuing_company'] = from_match.group(1).strip()
    else:
        # Fallback: First non-empty line usually Issuing Company in headers
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            data['issuing_company'] = lines[0] # Naive assumption, but standard for headers
            
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
