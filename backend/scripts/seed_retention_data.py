import sqlite3
import datetime
import os
import uuid

# Ensure we can find the DB
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'documents.db')

def seed_retention_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create an 'Invoice' from 10 years ago
    upload_date = (datetime.datetime.now() - datetime.timedelta(days=365*10)).strftime("%Y-%m-%d %H:%M:%S")
    doc_id = int(uuid.uuid4().int >> 64) # random int for ID? No, sqlite uses rowid
    
    # Insert Document
    # We need a valid container ID or None. Let's use None for simplicity or a dummy one.
    cursor.execute('''
        INSERT INTO documents (filename, category, confidence, content, upload_date, status, ocr_status, is_published, metadata, confidentiality_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Old_Invoice_2014.pdf", 
        "Invoice", 
        "0.99", 
        "Legacy content...", 
        upload_date, 
        "Published", 
        "Completed", 
        1, 
        '{"Vendor": "Acme Corp", "Date": "2014-01-01"}',
        'Internal'
    ))
    
    new_id = cursor.lastrowid
    print(f"Seeded Expired Document ID: {new_id} - Date: {upload_date}")
    
    # Ensure Policy Exists for 'Invoice' -> 5 Years -> Delete? Or Archive?
    policies = cursor.execute("SELECT * FROM retention_policies WHERE document_type = 'Invoice'").fetchone()
    if not policies:
        cursor.execute("INSERT INTO retention_policies (document_type, retention_years, action) VALUES (?, ?, ?)", 
                       ('Invoice', 5, 'Delete'))
        print("Created Retention Policy: Invoice -> 5 Years -> Delete")
    else:
        # Force update to Delete for this test if it's not
        if policies['action'] != 'Delete':
             cursor.execute("UPDATE retention_policies SET action = 'Delete' WHERE document_type = 'Invoice'")
             print("Updated Policy to Delete")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        seed_retention_data()
    except Exception as e:
        print(f"Error seeding data: {e}")
