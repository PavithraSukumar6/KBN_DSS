
import time
import json
import sqlite3
import os
import sys

# Add backend to path to import app if needed, or just use DB directly for setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_db_connection, save_document, request_access
from app import process_document_background

def setup_test_data():
    conn = get_db_connection()
    # Create test users
    conn.execute("INSERT OR IGNORE INTO users (id, role, name) VALUES ('OwnerUser', 'Operator', 'Owner User')")
    conn.execute("INSERT OR IGNORE INTO users (id, role, name) VALUES ('OtherUser', 'Operator', 'Other User')")
    conn.commit()
    conn.close()

def test_classification_fallback():
    print("\n[TEST] Classification Fallback (Filename)")
    # 1. Create a dummy file path (doesn't need to exist on disk for OCR skip test if we mock extract_text, 
    # but process_document_background calls extract_text.
    # We rely on ocr.py returning "OCR_SKIPPED" or similar if file missing/tesseract missing.
    # Actually if file missing, PIL might error.
    # We should create a dummy empty file.
    dummy_path = os.path.abspath(os.path.join(os.getcwd(), "..", "uploads", "Test_Invoice_Fallback.png"))
    with open(dummy_path, 'w') as f:
        f.write("dummy content")
        
    conn = get_db_connection()
    cursor = conn.execute("INSERT INTO documents (filename, upload_date, ocr_status, owner_id) VALUES (?, ?, ?, ?)", 
                          ("Test_Invoice_Fallback.png", "2025-01-01", "Processing", "OwnerUser"))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Run background process synchronously
    print(f"Processing Doc ID: {doc_id}")
    process_document_background(doc_id, dummy_path)
    
    # Check Result
    conn = get_db_connection()
    doc = conn.execute("SELECT category, ocr_status, metadata FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    
    print(f"Result Category: {doc['category']}")
    print(f"Result Status: {doc['ocr_status']}")
    
    if doc['category'] == 'Invoice' and "No OCR" in doc['ocr_status']:
        print("PASS: Classification fallback worked.")
    else:
        print("FAIL: Classification fallback failed.")

def test_governance_owner_approval():
    print("\n[TEST] Governance: Owner Approval")
    conn = get_db_connection()
    # Create Doc owned by OwnerUser
    cursor = conn.execute("INSERT INTO documents (filename, owner_id, confidentiality_level) VALUES (?, ?, ?)", 
                          ("Confidential_Doc", "OwnerUser", "Confidential"))
    doc_id = cursor.lastrowid
    
    # Create Access Request for OtherUser
    cursor = conn.execute("INSERT INTO access_requests (user_id, document_id, status) VALUES (?, ?, ?)", 
                          ("OtherUser", doc_id, "Pending"))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # We need to simulate the API call logic.
    # Since we can't easily make HTTP requests without running server, we will import the route function logic?
    # Or just copy the logic effectively or use `app.test_client()`.
    from app import app
    client = app.test_client()
    
    # 1. Attempt Approve by OtherUser (Should Fail)
    res = client.post('/access/approve', json={
        "request_id": req_id,
        "status": "Approved",
        "reviewer": "OtherUser"
    })
    
    if res.status_code == 403:
        print("PASS: OtherUser denied approval (403).")
    else:
        print(f"FAIL: OtherUser got {res.status_code}: {res.json}")

    # 2. Attempt Approve by OwnerUser (Should Success)
    res = client.post('/access/approve', json={
        "request_id": req_id,
        "status": "Approved",
        "reviewer": "OwnerUser"
    })
    
    if res.status_code == 200:
        print("PASS: OwnerUser granted approval (200).")
    else:
        print(f"FAIL: OwnerUser got {res.status_code}: {res.json}")

if __name__ == "__main__":
    try:
        setup_test_data()
        test_classification_fallback()
        test_governance_owner_approval()
    except Exception as e:
        print(f"Test Suite Failed: {e}")
