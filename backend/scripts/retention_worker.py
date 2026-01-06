import sqlite3
import datetime
import os
import sys

# Ensure we can find the DB
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'documents.db')

def log_audit(conn, entity_type, entity_id, action, details, user="System"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute('''
        INSERT INTO audit_log (entity_type, entity_id, action, details, performed_by, timestamp, scope)
        VALUES (?, ?, ?, ?, ?, ?, 'Lifecycle')
    ''', (entity_type, entity_id, action, details, user, timestamp))

def run_retention_process():
    print(f"[{datetime.datetime.now()}] Starting Retention Worker...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 1. Fetch Active Policies
        policies = cursor.execute("SELECT * FROM retention_policies").fetchall()
        if not policies:
            print("No retention policies active.")
            return

        for policy in policies:
            doc_type = policy['document_type']
            years = policy['retention_years']
            action = policy['action'] # 'Archive' or 'Delete'
            
            # Calculate cutoff
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=years * 365)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"Processing '{doc_type}' - Cutoff: {cutoff_date} - Action: {action}")
            
            # Find candidate documents
            # Only process Active/Published documents
            query = """
                SELECT id, filename, status FROM documents 
                WHERE category = ? 
                AND upload_date < ? 
                AND status IN ('Published', 'Completed', 'Processing', 'Intake')
            """
            candidates = cursor.execute(query, (doc_type, cutoff_date)).fetchall()
            
            print(f"  Found {len(candidates)} candidates.")
            
            for doc in candidates:
                new_status = 'Archived' if action == 'Archive' else 'Pending_Deletion'
                
                # Update status
                cursor.execute("UPDATE documents SET status = ? WHERE id = ?", (new_status, doc['id']))
                
                # Log
                log_audit(conn, 'document', doc['id'], 'RETENTION_ACTION', f"Auto-{action} due to policy ({years} years)", "RetentionWorker")
                print(f"  Updated Doc #{doc['id']} ({doc['filename']}) to {new_status}")
                
        conn.commit()
    except Exception as e:
        print(f"Error executing retention worker: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_retention_process()
