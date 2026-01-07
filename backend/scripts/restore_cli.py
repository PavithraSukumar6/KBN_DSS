import os
import shutil
import sys
import glob

def restore_from_backup(backup_path):
    """
    Restores the database and uploads directory from a specified backup folder.
    """
    if not os.path.exists(backup_path):
        print(f"Error: Backup path '{backup_path}' does not exist.")
        return

    BASE_DIR = os.getcwd() # Run from project root
    
    # Paths in Backup
    bak_db = os.path.join(backup_path, 'documents.db')
    bak_uploads = os.path.join(backup_path, 'uploads')
    
    # Destination Paths
    # Assuming standard locations. 
    # If using backend/documents.db check logic. 
    # backup_service.py tried backend/documents.db then documents.db
    # We should restore to backend/documents.db if it exists there, else root.
    
    dest_db = os.path.join(BASE_DIR, 'backend', 'documents.db')
    if not os.path.exists(os.path.dirname(dest_db)):
         dest_db = os.path.join(BASE_DIR, 'documents.db')
         
    dest_uploads = os.path.join(BASE_DIR, 'uploads')

    print(f"Restoring from: {backup_path}")
    print(f"To: {BASE_DIR}")

    # Restore DB
    if os.path.exists(bak_db):
        try:
            # Shutdown warning? The app should be stopped ideally.
            shutil.copy2(bak_db, dest_db)
            print(f"[Restore] Database restored from {bak_db} to {dest_db}")
        except Exception as e:
            print(f"[Restore] DB Restore Failed: {e}")
    else:
        print("[Restore] Warning: No database.db found in backup.")

    # Restore Uploads
    if os.path.exists(bak_uploads):
        if os.path.exists(dest_uploads):
            print("[Restore] Cleaning existing uploads directory...")
            shutil.rmtree(dest_uploads)
        try:
            shutil.copytree(bak_uploads, dest_uploads)
            print(f"[Restore] Uploads restored.")
        except Exception as e:
            print(f"[Restore] Uploads Restore Failed: {e}")
    else:
        print("[Restore] Warning: No uploads folder found in backup.")

def list_backups():
    BASE_DIR = os.getcwd()
    backups_dir = os.path.join(BASE_DIR, 'backups')
    if not os.path.exists(backups_dir):
        print("No backups directory found.")
        return []
        
    backups = sorted(glob.glob(os.path.join(backups_dir, 'backup_*')), reverse=True)
    return backups

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KBN Restore Utility")
    parser.add_argument('--latest', action='store_true', help="Restore the most recent backup")
    parser.add_argument('--path', type=str, help="Path to specific backup folder")
    
    args = parser.parse_args()
    
    target_backup = None
    
    if args.path:
        target_backup = args.path
    elif args.latest:
        backups = list_backups()
        if backups:
            target_backup = backups[0]
        else:
            print("No backups found.")
            sys.exit(1)
            
    if target_backup:
        confirm = input(f"WARNING: This will OVERWRITE current data with backup from {target_backup}.\nAre you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            restore_from_backup(target_backup)
            print("Restore complete. Please restart the application.")
        else:
            print("Restore cancelled.")
    else:
        print("Usage: python backend/scripts/restore_cli.py --latest OR --path <path>")
        print("Available Backups:")
        for b in list_backups():
            print(f" - {os.path.basename(b)}")
