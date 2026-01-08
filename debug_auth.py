
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'documents.db'

def debug_users():
    if not os.path.exists(DB_NAME):
        print(f"Database not found at {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check Table Info
    print("--- Table Info ---")
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        if 'password_hash' not in columns:
            print("CRITICAL: password_hash column is MISSING!")
            # Attempt to fix
            print("Attempting to add password_hash column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
                conn.commit()
                print("Column added.")
            except Exception as e:
                print(f"Failed to add column: {e}")
        else:
            print("password_hash column exists.")

    except Exception as e:
        print(f"Error checking table: {e}")

    # Check Users
    print("\n--- Users Data ---")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    updates_needed = True # FORCE UPDATE
    
    for user in users:
        uid = user['id']
        name = user['name']
        pwd = user['password_hash'] if 'password_hash' in user.keys() else None
        
        status = "OK" if pwd else "MISSING PASSWORD"
        print(f"User: {uid} | Name: {name} | Hash: {pwd and pwd[:10]}... | Status: {status}")
        
        if not pwd:
            updates_needed = True
            
    if updates_needed or len(users) == 0:
        print("\n--- Fixing/Seeding Users ---")
        # Define default users map
        default_users = [
            ('Gokul_Admin', 'Gokul Admin', 'Admin', 'Holding', 'KBN Group', 'admin123'),
            ('Manager_Dave', 'Dave Manager', 'Manager', 'Subsidiary', 'KBN Group', 'manager123'),
            ('Operator_Sue', 'Sue Operator', 'Operator', 'Department', 'Finance', 'operator123'),
            ('Viewer_Tom', 'Tom Viewer', 'Viewer', 'Department', 'Sales', 'viewer123'),
            ('Intern_Joe', 'Joe Intern', 'Intern', 'Department', 'Operations', 'intern123'),
            # Legacy/Previous names if they exist
            ('Operator_Finance', 'Fin Operator', 'Operator', 'Department', 'Finance', 'operator123'),
            ('Viewer_Guest', 'Guest Viewer', 'Viewer', 'Holding', 'KBN Group', 'viewer123')
        ]
        
        for u in default_users:
            uid, name, role, scope, scope_val, raw_pass = u
            p_hash = generate_password_hash(raw_pass)
            
            # Check if exists
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (uid,))
            exists = cursor.fetchone()
            
            if exists:
                print(f"Updating password for {uid}...")
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (p_hash, uid))
            else:
                print(f"Inserting new user {uid}...")
                cursor.execute("INSERT INTO users (id, name, role, scope, assigned_scope_value, password_hash) VALUES (?, ?, ?, ?, ?, ?)", 
                             (uid, name, role, scope, scope_val, p_hash))
        
        conn.commit()
        print("Users updated.")

    # Verify One Login
    print("\n--- Verification ---")
    cursor.execute("SELECT password_hash FROM users WHERE id = 'Gokul_Admin'")
    row = cursor.fetchone()
    if row and check_password_hash(row['password_hash'], 'admin123'):
        print("Login Check (Gokul_Admin / admin123): SUCCESS")
    else:
        print("Login Check (Gokul_Admin / admin123): FAILED")

    conn.close()

if __name__ == "__main__":
    debug_users()
