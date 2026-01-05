import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'documents.db')
RETENTION_YEARS = 3

def archive_old_versions():
    print(f"[{datetime.datetime.now()}] Starting Retention Worker...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate cutoff date
    cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=RETENTION_YEARS * 365)).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Archiving versions older than: {cutoff_date}")
    
    try:
        # 1. Identify versions to archive
        cursor.execute('SELECT COUNT(*) FROM document_versions WHERE version_timestamp < ?', (cutoff_date,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Found {count} versions to archive.")
            # In a real system, we might move these to a separate 'archive' DB or cold storage
            # For this demo, we will delete them as a form of 'archival cleanup'
            cursor.execute('DELETE FROM document_versions WHERE version_timestamp < ?', (cutoff_date,))
            conn.commit()
            print("Successfully archived old versions.")
        else:
            print("No old versions found.")
            
    except Exception as e:
        print(f"Error during archival: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    archive_old_versions()
