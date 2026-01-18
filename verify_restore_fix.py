import urllib.request
import urllib.parse
import json
import sqlite3
import os

BASE_URL = "http://localhost:5000"

def get_db_connection():
    return sqlite3.connect('backend/documents.db')

def make_request(method, url, data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            data_bytes = urllib.parse.urlencode(data).encode('utf-8')
            req.data = data_bytes
        
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test_restore_workflow():
    print("\n--- Testing Restore Workflow ---")
    
    try:
        conn = get_db_connection()
        doc = conn.execute("SELECT id, filename FROM documents ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        
        if not doc:
            print("No documents found to test.")
            return
            
        doc_id = doc[0]
        print(f"Testing with Document ID: {doc_id} ({doc[1]})")
        
        # 2. Soft Delete it
        print(f"Soft Deleting Doc {doc_id}...")
        status, response = make_request('DELETE', f"{BASE_URL}/documents/{doc_id}?user_id=TestAdmin")
        print(f"Soft Delete Status: {status}")
            
        conn = get_db_connection()
        row = conn.execute("SELECT is_deleted, status FROM documents WHERE id = ?", (doc_id,)).fetchone()
        conn.close()
        print(f"DB State after Delete: is_deleted={row[0]}, status={row[1]}")
        
        if row[0] != 1:
            print("FAILURE: Document was not soft deleted (is_deleted!=1)")
            # Proceed anyway to test restore if possible? No.
        
        # 3. Restore it
        print(f"Restoring Doc {doc_id}...")
        status, response = make_request('POST', f"{BASE_URL}/documents/{doc_id}/restore?user_id=TestAdmin")
        print(f"Restore Status: {status}")
        print(f"Restore Response: {response}")
        
        # 4. Verify Final State
        conn = get_db_connection()
        row = conn.execute("SELECT is_deleted, status FROM documents WHERE id = ?", (doc_id,)).fetchone()
        conn.close()
        print(f"DB State after Restore: is_deleted={row[0]}, status={row[1]}")
        
        if row[0] == 0 and row[1] == 'Published':
            print("SUCCESS: Document restored to Published state.")
        else:
            print(f"FAILURE: Document state incorrect. Expected is_deleted=0, status='Published'. Got {row}")

    except Exception as e:
        print(f"Test Failed with Exception: {e}")

if __name__ == "__main__":
    test_restore_workflow()
