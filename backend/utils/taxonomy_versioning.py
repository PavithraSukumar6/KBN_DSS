import sqlite3
from database.db import get_db_connection

def update_taxonomy_item_versioned(item_id, new_value, new_status='Active'):
    """
    Updates a taxonomy item by deprecating the old version and inserting a new one.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Get existing item
        old_item = cur.execute("SELECT * FROM taxonomy WHERE id = ?", (item_id,)).fetchone()
        if not old_item:
            return {"error": "Item not found"}
            
        current_version = old_item['version_number'] if 'version_number' in old_item.keys() else 1
        category = old_item['category']
        
        # 1. Mark old item as 'Archived' (or Deprecated, but user said 'keep old version')
        # If we use 'Deprecated' it usually means "don't use". 
        # Let's status = 'Version_Locked' or just keep 'Deprecated' if that's the system standard.
        # But wait, unique constraint on (category, value) might exist?
        # Check db.py schema... UNIQUE(category, value) IS there!
        # So we can't keep "HR" and "HR" (v2).
        # This implies we are updating the VALUE. e.g. HR -> Human Resources.
        # If we just change status, that's fine.
        
        # If we are changing Value: "HR" -> "People Ops".
        # We can Insert "People Ops" (v2). Old "HR" (v1) stays but status should handle it.
        # But if we change HIERARCHY (logic not fully defined in DB yet), it's vague.
        # User said: "If I change the folder hierarchy, keep the old version".
        
        # Let's assume this function handles Value or Status changes.
        
        # Step 1: Update old row to ensure it doesn't conflict if we were reusing value (unlikely for versioning).
        # Actually, best practice:
        # Old: ID=1, Val=HR, Ver=1, Status=Deprecated
        # New: ID=2, Val=Human Resources, Ver=2, Status=Active, Parent=1
        
        cur.execute("UPDATE taxonomy SET status = 'Archived' WHERE id = ?", (item_id,))
        
        # Step 2: Insert new
        new_version = current_version + 1
        cur.execute('''
            INSERT INTO taxonomy (category, value, status, version_number, parent_version_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (category, new_value, new_status, new_version, item_id))
        
        conn.commit()
        return {"message": "Taxonomy updated with new version", "new_version": new_version}
        
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        conn.close()
