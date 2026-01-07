import sqlite3
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_db_connection, save_document, create_container, init_db

def setup_test_data():
    # Ensure tables exist
    init_db()
    
    conn = get_db_connection()
    
    # 2. Create Users
    conn.execute("INSERT OR REPLACE INTO users (id, role, scope, assigned_scope_value) VALUES ('HR_Mgr', 'Manager', 'Department', 'HR')")
    conn.execute("INSERT OR REPLACE INTO users (id, role, scope, assigned_scope_value) VALUES ('HR_Intern', 'Intern', 'Department', 'HR')")
    conn.execute("INSERT OR REPLACE INTO users (id, role, scope, assigned_scope_value) VALUES ('Fin_Mgr', 'Manager', 'Department', 'Finance')")
    
    # 3. Create Containers
    conn.execute("INSERT OR IGNORE INTO containers (id, name, department) VALUES ('CONT-HR', 'HR Docs', 'HR')")
    conn.execute("INSERT OR IGNORE INTO containers (id, name, department) VALUES ('CONT-FIN', 'Finance Docs', 'Finance')")
    
    # 4. Create Documents
    # HR Public (Visible to Intern)
    cursor = conn.execute("INSERT INTO documents (filename, container_id, confidentiality_level, category, uploader_id, is_published) VALUES ('HR_Public.pdf', 'CONT-HR', 'Public', 'Policy', 'HR_Mgr', 1)")
    doc_hr_pub = cursor.lastrowid
    
    # HR Confidential (Hidden from Intern, Visible to Manager)
    # Note: Using confidentiality_level column
    cursor = conn.execute("INSERT INTO documents (filename, container_id, confidentiality_level, category, uploader_id, is_published) VALUES ('HR_Secret.pdf', 'CONT-HR', 'Confidential', 'Contract', 'HR_Mgr', 1)")
    doc_hr_conf = cursor.lastrowid
    
    # Finance Public (Hidden from HR due to Department Isolation)
    cursor = conn.execute("INSERT INTO documents (filename, container_id, confidentiality_level, category, uploader_id, is_published) VALUES ('Fin_Public.pdf', 'CONT-FIN', 'Public', 'Invoice', 'Fin_Mgr', 1)")
    doc_fin_pub = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return doc_hr_pub, doc_hr_conf, doc_fin_pub
    
    conn.commit()
    conn.close()
    return doc_hr_pub, doc_hr_conf, doc_fin_pub

def get_visible_docs(user_id):
    # Simulate the query logic from get_filtered_documents
    # We can't import the exact function if it relies on request args easily without mocking,
    # but let's try importing it or reproducing the logic.
    # Actually, let's copy the Critical Logic to verify IT specifically.
    
    conn = get_db_connection()
    
    # Logic duplication from db.py for testing
    cursor_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor_user.fetchone()
    role = user_row['role']
    scope = user_row['scope']
    scope_val = user_row['assigned_scope_value']
    
    query = """
        SELECT d.filename 
        FROM documents d
        JOIN containers c ON d.container_id = c.id
        WHERE 1=1
    """
    params = []
    
    # Dept Isolation
    if role != 'Admin':
        if scope == 'Department':
            query += " AND c.department = ?"
            params.append(scope_val)
            
        # Confidentiality
        policy_row = conn.execute("SELECT allowed_levels FROM access_policies WHERE role = ?", (role,)).fetchone()
        
        if not policy_row:
             print(f"WARNING: No policy found for role '{role}'. Defaulting to Public.")
             allowed = ['Public']
        else:
             allowed = policy_row['allowed_levels'].split(',')
        
        allowed = [x.strip() for x in allowed]
        
        placeholders = ','.join(['?'] * len(allowed))
        query += f" AND (d.confidentiality_level IN ({placeholders}) OR d.uploader_id = ?)"
        params.extend(allowed)
        params.append(user_id)
        
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [r['filename'] for r in rows]

def run_tests():
    print("Setting up data...")
    try:
        setup_test_data()
    except Exception as e:
        print(f"Setup failed (ignoring uniqueness constraints): {e}")

    print("\n[TEST] 1. HR Intern should see HR Public Only")
    docs = get_visible_docs('HR_Intern')
    print(f"   Visible: {docs}")
    if 'HR_Public.pdf' in docs and 'HR_Secret.pdf' not in docs and 'Fin_Public.pdf' not in docs:
        print("PASS")
    else:
        print("FAIL")

    print("\n[TEST] 2. HR Manager should see HR Public AND Confidential")
    docs = get_visible_docs('HR_Mgr')
    print(f"   Visible: {docs}")
    if 'HR_Public.pdf' in docs and 'HR_Secret.pdf' in docs and 'Fin_Public.pdf' not in docs:
        print("PASS")
    else:
        print("FAIL (Check Department Isolation)")

    print("\n[TEST] 3. Finance Manager should see Finance Public Only")
    docs = get_visible_docs('Fin_Mgr')
    print(f"   Visible: {docs}")
    if 'Fin_Public.pdf' in docs and 'HR_Public.pdf' not in docs:
        print("PASS")
    else:
        print("FAIL")

if __name__ == "__main__":
    run_tests()
