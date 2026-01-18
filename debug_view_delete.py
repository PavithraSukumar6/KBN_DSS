import sqlite3
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database.db import get_filtered_documents, get_db_connection

def debug_check():
    conn = get_db_connection()
    
    # 1. Check Soft Delete Status
    print("\n--- Checking Soft Deleted Documents ---")
    deleted_docs = conn.execute("SELECT id, filename, status, is_deleted, is_published FROM documents WHERE status = 'Soft_Deleted' OR is_deleted = 1").fetchall()
    
    if not deleted_docs:
        print("No soft-deleted documents found in DB.")
    else:
        for doc in deleted_docs:
            print(f"Doc {doc['id']}: Status='{doc['status']}', is_deleted={doc['is_deleted']}, Published={doc['is_published']}")
            
    # 2. Simulate Filter Query (as called by Frontend)
    print("\n--- Simulating filtered query (Default View) ---")
    # Dashboard calls with: category='', start_date='', end_date='', approval_status='', status='', ...
    docs = get_filtered_documents(status='', user_id='Gokul_Admin', is_admin=True)
    
    deleted_visible = [d for d in docs if d['status'] == 'Soft_Deleted' or d['is_deleted'] == 1]
    if deleted_visible:
        print(f"FAILURE: Found {len(deleted_visible)} deleted documents in default view!")
        for d in deleted_visible:
             print(f" - Visible Doc {d['id']}: {d['filename']} (Status: {d['status']}, is_deleted: {d['is_deleted']})")
    else:
        print("SUCCESS: No deleted documents visible in default view.")

    # 3. Check View File Paths
    print("\n--- Checking File Paths for View ---")
    all_docs = conn.execute("SELECT id, filename FROM documents LIMIT 5").fetchall()
    
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    processed_folder = os.path.join(os.getcwd(), 'processed_docs')
    
    print(f"Upload Folder: {upload_folder}")
    print(f"Processed Folder: {processed_folder}")
    
    for doc in all_docs:
        fname = doc['filename']
        path1 = os.path.join(upload_folder, fname)
        path2 = os.path.join(processed_folder, fname)
        
        found = False
        if os.path.exists(path1):
            print(f"Doc {doc['id']} ({fname}): Found in Uploads")
            found = True
        elif os.path.exists(path2):
            print(f"Doc {doc['id']} ({fname}): Found in Processed")
            found = True
        else:
            print(f"Doc {doc['id']} ({fname}): NOT FOUND on disk!")

    conn.close()

if __name__ == "__main__":
    debug_check()
