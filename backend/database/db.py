import sqlite3
import datetime

DB_NAME = 'documents.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # This allows us to access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                category TEXT,
                confidence TEXT,
                upload_date TEXT,
                content TEXT,
                status TEXT DEFAULT 'Processed',
                container_id TEXT,
                batch_id INTEGER,
                page_count INTEGER DEFAULT 1,
                FOREIGN KEY(batch_id) REFERENCES batches(id)
            );

            CREATE TABLE IF NOT EXISTS containers (
                id TEXT PRIMARY KEY,
                name TEXT,
                subsidiary TEXT,
                department TEXT,
                function TEXT,
                date_range TEXT,
                confidentiality_level TEXT,
                source_location TEXT,
                created_by TEXT,
                created_at TEXT,
                physical_page_count INTEGER DEFAULT 0,
                parent_id TEXT,
                barcode TEXT UNIQUE,
                FOREIGN KEY(parent_id) REFERENCES containers(id)
            );

            CREATE TABLE IF NOT EXISTS transfer_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                container_id TEXT,
                previous_location TEXT,
                new_location TEXT,
                transferred_by TEXT,
                timestamp TEXT,
                FOREIGN KEY(container_id) REFERENCES containers(id)
            );
            
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                container_id TEXT,
                status TEXT DEFAULT 'Pending',
                start_time TEXT,
                end_time TEXT,
                total_pages_scanned INTEGER DEFAULT 0,
                physical_page_count_expected INTEGER,
                FOREIGN KEY(container_id) REFERENCES containers(id)
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                action TEXT,
                details TEXT,
                performed_by TEXT,
                timestamp TEXT
            );

            CREATE TABLE IF NOT EXISTS approval_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_type TEXT, -- 'Category' or 'Confidentiality'
                match_value TEXT,
                is_active INTEGER DEFAULT 1
            );
        ''')

        # Migration: Add columns if they don't exist (running this safe for existing DBs)
        try:
            conn.execute('ALTER TABLE containers ADD COLUMN physical_page_count INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass # Column likely exists

        # Migration: Add columns if they don't exist
        for col, col_type in [
            ('batch_id', 'INTEGER'), ('page_count', 'INTEGER DEFAULT 1'), 
            ('container_id', 'TEXT'), ('tags', 'TEXT'), 
            ('ocr_status', "TEXT DEFAULT 'Pending'"), ('metadata', 'TEXT'), 
            ('template_type', 'TEXT'), ('is_published', 'INTEGER DEFAULT 0'), 
            ('uploader_id', 'TEXT'), ('approval_status', "TEXT DEFAULT 'Not Required'"),
            ('uid', 'TEXT UNIQUE')
        ]:
            try:
                conn.execute(f'ALTER TABLE documents ADD COLUMN {col} {col_type}')
            except sqlite3.OperationalError:
                pass

        # Migration for containers
        for col, col_type in [('parent_id', 'TEXT'), ('barcode', 'TEXT UNIQUE'), ('name', 'TEXT')]:
            try:
                conn.execute(f'ALTER TABLE containers ADD COLUMN {col} {col_type}')
            except sqlite3.OperationalError:
                pass

        # Create Taxonomy Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS taxonomy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, -- 'DocumentType' or 'Department'
                value TEXT NOT NULL,
                status TEXT DEFAULT 'Active', -- 'Active' or 'Deprecated'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, value)
            );
        ''')

        # Seed Taxonomy if empty
        count = conn.execute("SELECT COUNT(*) FROM taxonomy").fetchone()[0]
        if count == 0:
            defaults = [
                ('DocumentType', 'Invoice'), ('DocumentType', 'Contract'), 
                ('DocumentType', 'ID'), ('DocumentType', 'Report'),
                ('DocumentType', 'HR'), ('DocumentType', 'Legal'), ('DocumentType', 'Other'),
                ('Department', 'Finance'), ('Department', 'HR'), ('Department', 'Legal'),
                ('Department', 'Operations'), ('Department', 'Sales')
            ]
            conn.executemany("INSERT INTO taxonomy (category, value) VALUES (?, ?)", defaults)

        # Merged into loop above

        # Create versioning and approval tables
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                filename TEXT,
                category TEXT,
                confidence TEXT,
                content TEXT,
                metadata TEXT,
                version_timestamp TEXT,
                reason TEXT,
                user_id TEXT,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                action TEXT,
                details TEXT,
                performed_by TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id TEXT,
                document_id INTEGER,
                PRIMARY KEY (user_id, document_id),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                name TEXT,
                query_params TEXT,
                is_public INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # FR-17: FTS5 Virtual Table for Global Search
        conn.executescript('''
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                id UNINDEXED,
                filename,
                content,
                category,
                tags
            );

            -- Triggers to sync FTS table
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(id, filename, content, category, tags)
                VALUES (new.id, new.filename, new.content, new.category, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                DELETE FROM documents_fts WHERE id = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                DELETE FROM documents_fts WHERE id = old.id;
                INSERT INTO documents_fts(id, filename, content, category, tags)
                VALUES (new.id, new.filename, new.content, new.category, new.tags);
            END;
        ''')

        # Sync existing data to FTS if empty
        fts_count = conn.execute("SELECT COUNT(*) FROM documents_fts").fetchone()[0]
        if fts_count == 0:
            conn.execute("INSERT INTO documents_fts(id, filename, content, category, tags) SELECT id, filename, content, category, tags FROM documents")

        # Insert Default Policies if empty
        cursor = conn.execute("SELECT COUNT(*) FROM approval_policies")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO approval_policies (match_type, match_value) VALUES ('Category', 'HR')")
            conn.execute("INSERT INTO approval_policies (match_type, match_value) VALUES ('Confidentiality', 'Confidential')")
            conn.execute("INSERT INTO approval_policies (match_type, match_value) VALUES ('Category', 'ID')")

        # Hierarchical Seeding: Root and Departments
        root = conn.execute("SELECT id FROM containers WHERE id = 'ROOT'").fetchone()
        if not root:
            conn.execute("INSERT INTO containers (id, name, subsidiary, created_by, created_at, barcode) VALUES ('ROOT', 'KBN', 'KBN Group', 'System', ?, 'BC-ROOT-001')", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            
            # Seed Departments as sub-folders
            departments = ['Finance', 'HR', 'Legal', 'Operations', 'Sales']
            for dept in departments:
                id_slug = f"DEPT-{dept.upper()}"
                conn.execute("INSERT INTO containers (id, name, department, parent_id, created_by, created_at, barcode) VALUES (?, ?, ?, 'ROOT', 'System', ?, ?)", 
                             (id_slug, dept, dept, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"BC-{id_slug}"))
    conn.close()

import uuid
import random

def generate_barcode():
    return f"BC-{random.randint(1000, 9999)}-{uuid.uuid4().hex[:6].upper()}"

def generate_uid(prefix="DOC"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}-V1"


# ... existing functions ...

def save_document(filename, category, confidence, content, container_id=None, batch_id=None, ocr_status='Processed', metadata=None, template_type=None, uploader_id=None, tags=None):
    conn = get_db_connection()
    upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    doc_uid = generate_uid()
    with conn:
        cursor = conn.execute('''
            INSERT INTO documents (filename, category, confidence, content, upload_date, container_id, batch_id, ocr_status, metadata, template_type, uploader_id, tags, uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, category, confidence, content, upload_date, container_id, batch_id, ocr_status, metadata, template_type, uploader_id, tags, doc_uid))
    doc_id = cursor.lastrowid
    conn.close()
    return doc_id

def save_document_version(doc_id, reason, user_id):
    conn = get_db_connection()
    doc = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return False
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn.execute('''
        INSERT INTO document_versions (document_id, filename, category, confidence, content, metadata, version_timestamp, reason, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, doc['filename'], doc['category'], doc['confidence'], doc['content'], doc['metadata'], timestamp, reason, user_id))
    
    conn.commit()
    conn.close()
    return True

def publish_document(doc_id):
    conn = get_db_connection()
    conn.execute("UPDATE documents SET is_published = 1, approval_status = 'Approved' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

def update_approval_status(doc_id, status, user, notes=None):
    conn = get_db_connection()
    conn.execute("UPDATE documents SET approval_status = ? WHERE id = ?", (status, doc_id))
    conn.commit()
    conn.close()
    
    # Log the decision
    details = f"Approval status changed to {status}."
    if notes:
        details += f" Notes: {notes}"
    log_audit('document', doc_id, 'approval_action', details, user)

def get_approval_policies():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM approval_policies")
    policies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return policies

def check_approval_required(category, confidentiality):
    conn = get_db_connection()
    policies = conn.execute("SELECT * FROM approval_policies WHERE is_active = 1").fetchall()
    conn.close()
    
    for p in policies:
        if p['match_type'] == 'Category' and p['match_value'] == category:
            return True
        if p['match_type'] == 'Confidentiality' and p['match_value'] == confidentiality:
            return True
            
    return False

def get_document_versions(doc_id):
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM document_versions WHERE document_id = ? ORDER BY version_timestamp DESC', (doc_id,))
    versions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return versions

def create_container(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    container_id = data.get('id') or f"CONT-{uuid.uuid4().hex[:8].upper()}"
    barcode = data.get('barcode') or generate_barcode()
    name = data.get('name') or data.get('id')

    try:
        cursor.execute('''
            INSERT INTO containers (id, name, subsidiary, department, function, date_range, confidentiality_level, source_location, created_by, created_at, physical_page_count, parent_id, barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (container_id, name, data.get('subsidiary'), data.get('department'), data.get('function'), data.get('date_range'), data.get('confidentiality_level'), data.get('source_location'), data.get('created_by'), created_at, data.get('physical_page_count', 0), data.get('parent_id'), barcode))
        conn.commit()
        return container_id
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def log_transfer(container_id, previous_loc, new_loc, transferred_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO transfer_log (container_id, previous_location, new_location, transferred_by, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (container_id, previous_loc, new_loc, transferred_by, timestamp))
    conn.commit()
    conn.close()

def update_batch_qc(batch_id, status, notes, user):
    conn = get_db_connection()
    cursor = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE batches 
        SET qc_status = ?, qc_notes = ?, qc_by = ?, qc_date = ? 
        WHERE id = ?
    ''', (status, notes, user, date, batch_id))
    conn.commit()
    conn.close()

def log_audit(entity_type, entity_id, action, details, user):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO audit_log (entity_type, entity_id, action, details, performed_by, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (entity_type, entity_id, action, details, user, timestamp))
    conn.commit()
    conn.close()

def update_document_metadata(doc_id, category, metadata, template_type, user='System'):
    # FR-13: Preserve historical data before update
    save_document_version(doc_id, "Metadata Update", user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get old data for comparison/logging
    old_doc = conn.execute('SELECT category, metadata FROM documents WHERE id = ?', (doc_id,)).fetchone()
    
    cursor.execute('''
        UPDATE documents 
        SET category = ?, metadata = ?, template_type = ? 
        WHERE id = ?
    ''', (category, metadata, template_type, doc_id))
    conn.commit()
    conn.close()
    
    # Log the change
    details = f"Metadata updated. Category: {category}."
    if old_doc and old_doc['category'] != category:
        details = f"Category changed from {old_doc['category']} to {category}."
    
    log_audit('document', doc_id, 'metadata_update', details, user)

def get_all_containers():
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM containers ORDER BY created_at DESC')
    containers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return containers

def get_filtered_documents(category=None, start_date=None, end_date=None, search=None, user_id=None, is_admin=False, only_published=False, batch_id=None, status=None, subsidiary=None, department=None, function=None, tags=None, favorite_only=False, container_id=None):
    conn = get_db_connection()
    
    # Base query with JOIN to containers for organization filters
    # Join with favorites to check if current user favorited it
    query = """
        SELECT d.*, c.subsidiary, c.department, c.function, c.confidentiality_level,
               CASE WHEN fav.document_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite
        FROM documents d
        LEFT JOIN containers c ON d.container_id = c.id
        LEFT JOIN favorites fav ON d.id = fav.document_id AND fav.user_id = ?
        WHERE 1=1
    """
    params = [user_id]
    
    if batch_id:
        query += " AND d.batch_id = ?"
        params.append(batch_id)

    if container_id:
        query += " AND d.container_id = ?"
        params.append(container_id)

    # Permission Handling
    if not is_admin:
        query += """ AND (
            c.confidentiality_level IS NULL 
            OR c.confidentiality_level != 'Confidential'
            OR d.uploader_id = ?
        )"""
        params.append(user_id)
        
        query += " AND (d.approval_status != 'Pending Approval' OR d.uploader_id = ?)"
        params.append(user_id)

    if only_published:
        query += " AND d.is_published = 1"

    # Standard filters
    if category:
        query += " AND d.category = ?"
        params.append(category)
        
    if start_date:
        query += " AND d.upload_date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND d.upload_date <= ?"
        params.append(end_date + " 23:59:59")
        
    if status:
        # Check both ocr_status and approval_status? FR says "Lifecycle: Status (Draft, Published, Archived)"
        # We'll map 'Published' to is_published=1, 'Archived' to ocr_status='Archived' (if we had it)
        # For now, let's filter by ocr_status or approval_status if they match
        if status == 'Published':
            query += " AND d.is_published = 1"
        elif status == 'Pending':
            query += " AND d.approval_status = 'Pending Approval'"
        else:
            query += " AND d.ocr_status = ?"
            params.append(status)

    if subsidiary:
        query += " AND c.subsidiary = ?"
        params.append(subsidiary)
    
    if department:
        query += " AND c.department = ?"
        params.append(department)
        
    if function:
        query += " AND c.function = ?"
        params.append(function)

    if tags:
        query += " AND d.tags LIKE ?"
        params.append(f"%{tags}%")

    if favorite_only:
        query += " AND fav.document_id IS NOT NULL"

    # Global Search with FTS5 Ranking and Snippet
    if search:
        # We join with FTS table and use MATCH
        # Snippets are generated here. Snippet(table, column_index, start, end, ellipsis, tokens)
        query = """
            SELECT d.*, c.subsidiary, c.department, c.function, c.confidentiality_level,
                   CASE WHEN fav.document_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
                   snippet(documents_fts, 2, '<b>', '</b>', '...', 15) as ocr_snippet,
                   rank as relevance
            FROM documents d
            JOIN documents_fts f ON d.id = f.id
            LEFT JOIN containers c ON d.container_id = c.id
            LEFT JOIN favorites fav ON d.id = fav.document_id AND fav.user_id = ?
            WHERE f.documents_fts MATCH ? AND """ + query[query.find("WHERE")+6:] # Reuse filters
        params.insert(1, search) # params[0] is user_id
        query += " ORDER BY relevance ASC, d.upload_date DESC"
    else:
        query += " ORDER BY d.upload_date DESC"
    
    cursor = conn.execute(query, params)
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documents

def get_analytics_stats():
    conn = get_db_connection()
    
    # 1. Total Documents
    total = conn.execute("SELECT COUNT(*) as count FROM documents").fetchone()['count']
    
    # 2. By Category
    cat_cursor = conn.execute("SELECT category, COUNT(*) as count FROM documents GROUP BY category")
    by_category = {row['category']: row['count'] for row in cat_cursor.fetchall()}
    
    # 3. By Status (OCR Status)
    status_cursor = conn.execute("SELECT ocr_status, COUNT(*) as count FROM documents GROUP BY ocr_status")
    by_status = {row['ocr_status']: row['count'] for row in status_cursor.fetchall()}
    
    # 4. Daily Throughput
    throughput_cursor = conn.execute("""
        SELECT date(upload_date) as date, COUNT(*) as count 
        FROM documents 
        GROUP BY date(upload_date) 
        ORDER BY date DESC LIMIT 7
    """)
    daily_throughput = [dict(row) for row in throughput_cursor.fetchall()]
    
    conn.close()
    return {
        "total_documents": total,
        "by_category": by_category,
        "by_status": by_status,
        "daily_throughput": daily_throughput
    }

# --- Taxonomy Management ---
def get_taxonomy(category=None):
    conn = get_db_connection()
    query = "SELECT * FROM taxonomy WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    cursor = conn.execute(query, params)
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

def add_taxonomy_item(category, value):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO taxonomy (category, value) VALUES (?, ?)", (category, value))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_taxonomy_status(item_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE taxonomy SET status = ? WHERE id = ?", (status, item_id))
    conn.commit()
    conn.close()

# --- Metadata Validation (FR-15) ---
def validate_metadata(category, metadata):
    """
    Validates metadata fields based on document category.
    Returns: (is_valid, error_message)
    """
    errors = []
    
    if category == 'Invoice':
        # Example rules for Invoice
        if 'due_date' in metadata:
            import datetime
            try:
                datetime.datetime.strptime(metadata['due_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Invalid Due Date format (YYYY-MM-DD)")
        
        if 'amount' in metadata:
            try:
                float(str(metadata['amount']).replace(',', ''))
            except ValueError:
                errors.append("Amount must be numeric")

    elif category == 'Contract':
        if 'start_date' in metadata and 'end_date' in metadata:
            # Add date comparison logic if needed
            pass

    return (len(errors) == 0, ", ".join(errors))

def get_container_logs(container_id):
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM transfer_log WHERE container_id = ? ORDER BY timestamp DESC', (container_id,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs


def get_all_documents():
    conn = get_db_connection()
    cursor = conn.execute('SELECT id, filename, category, confidence, upload_date, status FROM documents ORDER BY upload_date DESC')
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documents

def get_document(doc_id):
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def search_documents(query):
    conn = get_db_connection()
    # Search in filename, category, or content
    search_term = f'%{query}%'
    cursor = conn.execute('''
        SELECT id, filename, category, confidence, upload_date, status 
        FROM documents 
        WHERE filename LIKE ? OR category LIKE ? OR content LIKE ?
        ORDER BY upload_date DESC
    ''', (search_term, search_term, search_term))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
def toggle_favorite(user_id, doc_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if exists
    fav = cursor.execute("SELECT 1 FROM favorites WHERE user_id = ? AND document_id = ?", (user_id, doc_id)).fetchone()
    if fav:
        cursor.execute("DELETE FROM favorites WHERE user_id = ? AND document_id = ?", (user_id, doc_id))
        status = False
    else:
        cursor.execute("INSERT INTO favorites (user_id, document_id) VALUES (?, ?)", (user_id, doc_id))
        status = True
    conn.commit()
    conn.close()
    return status

def save_search_query(user_id, name, query_params, is_public=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO saved_searches (user_id, name, query_params, is_public) VALUES (?, ?, ?, ?)", 
                   (user_id, name, query_params, is_public))
    conn.commit()
    search_id = cursor.lastrowid
    conn.close()
    return search_id

def get_saved_searches(user_id):
    conn = get_db_connection()
    # Get user's searches AND public ones
    cursor = conn.execute("SELECT * FROM saved_searches WHERE user_id = ? OR is_public = 1 ORDER BY created_at DESC", (user_id,))
    searches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return searches

def publish_saved_search(search_id):
    conn = get_db_connection()
    conn.execute("UPDATE saved_searches SET is_public = 1 WHERE id = ?", (search_id,))
    conn.commit()
    conn.close()
