import sqlite3
import datetime

conn = sqlite3.connect('documents.db')
cursor = conn.cursor()

# 1. Add missing columns to containers
container_cols = [
    ('parent_id', 'TEXT'),
    ('barcode', 'TEXT'),
    ('name', 'TEXT')
]

for col, col_type in container_cols:
    try:
        cursor.execute(f'ALTER TABLE containers ADD COLUMN {col} {col_type}')
        print(f"Added {col} to containers")
    except sqlite3.OperationalError:
        print(f"{col} already exists in containers")

# 2. Add missing columns to documents
document_cols = [
    ('uid', 'TEXT')
]

for col, col_type in document_cols:
    try:
        cursor.execute(f'ALTER TABLE documents ADD COLUMN {col} {col_type}')
        print(f"Added {col} to documents")
    except sqlite3.OperationalError:
        print(f"{col} already exists in documents")

# 3. Create Root container if it doesn't exist
cursor.execute("SELECT 1 FROM containers WHERE id = 'ROOT'")
if not cursor.fetchone():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO containers (id, name, subsidiary, created_by, created_at, barcode) 
        VALUES ('ROOT', 'KBN Group', 'Headquarters', 'System', ?, 'BC-ROOT-001')
    """, (now,))
    print("Created ROOT container")
else:
    print("ROOT container already exists")

# 4. Seed Departments as sub-folders
departments = ['Finance', 'HR', 'Legal', 'Operations', 'Sales', 'UAE']
for dept in departments:
    id_slug = f"DEPT-{dept.upper()}"
    cursor.execute("SELECT 1 FROM containers WHERE id = ?", (id_slug,))
    if not cursor.fetchone():
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO containers (id, name, department, parent_id, created_by, created_at, barcode) 
            VALUES (?, ?, ?, 'ROOT', 'System', ?, ?)
        """, (id_slug, dept, dept, now, f"BC-{id_slug}"))
        print(f"Created {id_slug} container")

conn.commit()
conn.close()
