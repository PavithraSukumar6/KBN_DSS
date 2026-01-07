
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documents.db')

def verify_content():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Count Documents
    try:
        count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        print(f"Total Documents in DB: {count}")
        
        if count > 0:
            rows = cursor.execute("SELECT id, filename, status, category FROM documents LIMIT 5").fetchall()
            print("First 5 docs:", rows)
    except Exception as e:
        print(f"Error querying documents: {e}")

    conn.close()

if __name__ == "__main__":
    verify_content()
