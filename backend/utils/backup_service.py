import os
import shutil
import datetime

def perform_backup():
    """
    Automatically copies the database and upload repository to a backups folder.
    Should be called on server start.
    """
    BASE_DIR = os.getcwd() # Should be backend/ or project root?
    # app.py runs from backend/ usually if user does 'python backend/app.py' from root?
    # Wait, the user command is 'python backend/app.py' from PROJECT ROOT.
    # So os.getcwd() is C:\Users\GOKUL\OneDrive\Desktop\KBN_Project
    
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
    DB_FILE = os.path.join(BASE_DIR, 'backend', 'documents.db') # db.py says 'documents.db', but need to check if it's relative to db.py or execution.
    # checking db.py: DB_NAME = 'documents.db' -> defaults to CWD if not abs path.
    # If I run from root, and db.py is imported, CWD is root.
    # Let's assume documents.db is in root or backend? 
    # Usually it creates it in the CWD of execution.
    # If user ran `python backend/app.py`, CWD is root. So documents.db is likely in root.
    # BUT, let's look at `ls` results if I could... I'll check `ls` first to be super safe. 
    # Actually, I'll code it to try finding it.
    
    if not os.path.exists(DB_FILE):
        # Try root
        DB_FILE = os.path.join(BASE_DIR, 'documents.db')
    
    UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subfolder = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_subfolder, exist_ok=True)
    
    # Copy DB
    if os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, os.path.join(backup_subfolder, 'documents.db'))
            print(f"[Backup] Database backed up to {backup_subfolder}")
        except Exception as e:
            print(f"[Backup] DB Backup Failed: {e}")
    else:
        print(f"[Backup] Warning: Database file not found at {DB_FILE}")
        
    # Copy Uploads (Repository)
    if os.path.exists(UPLOADS_DIR):
        try:
            # We use copytree for folders. ignore if exists (but we made a timestamped folder so it shouldn't)
            shutil.copytree(UPLOADS_DIR, os.path.join(backup_subfolder, 'uploads'))
            print(f"[Backup] Uploads backed up to {backup_subfolder}")
        except Exception as e:
            print(f"[Backup] Uploads Backup Failed: {e}")

if __name__ == "__main__":
    perform_backup()
