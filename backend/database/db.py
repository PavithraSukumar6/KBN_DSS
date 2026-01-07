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
                timestamp TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                scope TEXT
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
            ('uid', 'TEXT'), ('confidentiality_level', 'TEXT'),
            ('sla_due_date', 'TEXT'), ('priority', "TEXT DEFAULT 'Medium'"), 
            ('assigned_to', 'TEXT'), ('sla_status', "TEXT DEFAULT 'On Track'")
        ]:
            try:
                conn.execute(f'ALTER TABLE documents ADD COLUMN {col} {col_type}')
            except sqlite3.OperationalError:
                pass

        # Create Index for UID
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_uid ON documents(uid)")

        # Migration for containers
        for col, col_type in [('parent_id', 'TEXT'), ('barcode', 'TEXT'), ('name', 'TEXT')]:
            try:
                conn.execute(f'ALTER TABLE containers ADD COLUMN {col} {col_type}')
            except sqlite3.OperationalError:
                pass
        
        # Create Index for Barcode
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_containers_barcode ON containers(barcode)")

        # Migration for batches (QC Support)
        for col, col_type in [
            ('qc_status', "TEXT DEFAULT 'Pending'"), 
            ('qc_notes', 'TEXT'), 
            ('qc_by', 'TEXT'), 
            ('qc_date', 'TEXT')
        ]:
            try:
                conn.execute(f'ALTER TABLE batches ADD COLUMN {col} {col_type}')
            except sqlite3.OperationalError:
                pass

        # Migration: Add owner_id for Data Governance
        # Default owner is the system or can be backfilled with uploader
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN owner_id TEXT")
            # Backfill documents: set owner_id = uploader_id if null
            conn.execute("UPDATE documents SET owner_id = uploader_id WHERE owner_id IS NULL AND uploader_id IS NOT NULL")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE containers ADD COLUMN owner_id TEXT")
            # Backfill containers: set owner_id = created_by if null
            conn.execute("UPDATE containers SET owner_id = created_by WHERE owner_id IS NULL AND created_by IS NOT NULL")
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE documents ADD COLUMN content_hash TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON documents(content_hash)")
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

        # Access Policies Table (Role-Based Access to Confidentiality Levels)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS access_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                allowed_levels TEXT, -- Comma separated: 'Public,Internal,Confidential'
                department TEXT, -- Null for global policy
                UNIQUE(role, department)
            );
        ''')
        
        # Seed Default Access Policies if empty
        policy_count = conn.execute("SELECT COUNT(*) FROM access_policies").fetchone()[0]
        if policy_count == 0:
            defaults = [
                ('Admin', 'Public,Internal,Confidential,Restricted', None),
                ('Manager', 'Public,Internal,Confidential', None),
                ('Operator', 'Public,Internal', None),
                ('Viewer', 'Public,Internal', None),
                ('Intern', 'Public', None)
            ]
            conn.executemany("INSERT INTO access_policies (role, allowed_levels, department) VALUES (?, ?, ?)", defaults)

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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                scope TEXT
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

        conn.executescript('''
            CREATE TABLE IF NOT EXISTS retention_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT UNIQUE,
                retention_years INTEGER,
                action TEXT DEFAULT 'Archive', -- 'Archive', 'Delete'
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

        # SECURITY: Users & Roles
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                role TEXT, -- 'Admin', 'Operator', 'Viewer'
                scope TEXT, -- 'Holding', 'Subsidiary', 'Department'
                assigned_scope_value TEXT -- e.g. 'Finance' or 'KBN Group'
            );

            CREATE TABLE IF NOT EXISTS access_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                document_id INTEGER,
                status TEXT DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected', 'Expired'
                reason TEXT,
                expiry_date TEXT,
                request_date TEXT,
                reviewed_by TEXT,
                review_date TEXT,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );
        ''')

        # Seed Users
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            users = [
                ('Gokul_Admin', 'Gokul Admin', 'Admin', 'Holding', 'KBN Group'),
                ('Operator_Finance', 'Fin Operator', 'Operator', 'Department', 'Finance'),
                ('Operator_HR', 'HR Operator', 'Operator', 'Department', 'HR'),
                ('Viewer_Guest', 'Guest Viewer', 'Viewer', 'Holding', 'KBN Group')
            ]
            conn.executemany("INSERT INTO users (id, name, role, scope, assigned_scope_value) VALUES (?, ?, ?, ?, ?)", users)

        # Migration: Add confidentiality_level to documents
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN confidentiality_level TEXT DEFAULT 'Internal'")
            conn.execute("ALTER TABLE documents ADD COLUMN confidentiality_level TEXT DEFAULT 'Internal'")
        except sqlite3.OperationalError:
            pass

        # Migration: Add extended audit fields
        for col in ['old_value', 'new_value', 'ip_address', 'scope']:
            try:
                conn.execute(f'ALTER TABLE audit_log ADD COLUMN {col} TEXT')
            except sqlite3.OperationalError:
                pass

    conn.close()

    # Post-Migration: Add status column logic separate from main block if needed, 
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'Intake'")
        # Sync old ocr_status to new status if needed
        conn.execute("UPDATE documents SET status = 'Published' WHERE ocr_status = 'Completed' AND status = 'Intake'")
         # Seed System Settings
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('legal_hold', 'false')")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

import uuid
import random

def generate_barcode():
    return f"BC-{random.randint(1000, 9999)}-{uuid.uuid4().hex[:6].upper()}"

def generate_uid(prefix="DOC"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}-V1"


# ... existing functions ...

def check_duplicate_hash(file_hash):
    conn = get_db_connection()
    doc = conn.execute("SELECT id, filename, upload_date, uploader_id FROM documents WHERE content_hash = ?", (file_hash,)).fetchone()
    conn.close()
    return dict(doc) if doc else None

def save_document(filename, category, confidence, content, container_id=None, batch_id=None, ocr_status='Processed', metadata=None, template_type=None, uploader_id=None, tags=None, owner_id=None, content_hash=None):
    conn = get_db_connection()
    upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    doc_uid = generate_uid()
    
    # Default owner to uploader if not specified
    if not owner_id and uploader_id:
        owner_id = uploader_id

    with conn:
        cursor = conn.execute('''
            INSERT INTO documents (filename, category, confidence, content, upload_date, container_id, batch_id, ocr_status, metadata, template_type, uploader_id, tags, uid, owner_id, confidentiality_level, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (filename, category, confidence, content, upload_date, container_id, batch_id, ocr_status, metadata, template_type, uploader_id, tags, doc_uid, owner_id, 'Internal', content_hash))
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

    container_id = data.get('id') or f"CONT-{uuid.uuid4().hex[:8].upper()}"
    barcode = data.get('barcode') or generate_barcode()
    name = data.get('name') or data.get('id')
    owner = data.get('owner_id') or data.get('created_by')

    try:
        cursor.execute('''
            INSERT INTO containers (id, name, subsidiary, department, function, date_range, confidentiality_level, source_location, created_by, created_at, physical_page_count, parent_id, barcode, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (container_id, name, data.get('subsidiary'), data.get('department'), data.get('function'), data.get('date_range'), data.get('confidentiality_level'), data.get('source_location'), data.get('created_by'), created_at, data.get('physical_page_count', 0), data.get('parent_id'), barcode, owner))
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
    conn.commit()
    conn.close()

def get_container_logs(container_id):
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM transfer_log WHERE container_id = ? ORDER BY timestamp DESC", (container_id,)).fetchall()
    conn.close()
    return [dict(row) for row in logs]

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

def get_qc_queue_batches():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM batches WHERE status IN ('Pending', 'In Progress') ORDER BY start_time DESC")
    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return batches

def log_audit(entity_type, entity_id, action, details, user, old_value=None, new_value=None, ip_address=None, scope=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO audit_log (entity_type, entity_id, action, details, performed_by, timestamp, old_value, new_value, ip_address, scope)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (entity_type, entity_id, action, details, user, timestamp, old_value, new_value, ip_address, scope))
    conn.commit()
    conn.close()

def get_audit_logs(filters=None):
    conn = get_db_connection()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('user'):
            query += " AND performed_by LIKE ?"
            params.append(f"%{filters['user']}%")
        if filters.get('action'):
            query += " AND action = ?"
            params.append(filters['action'])
        if filters.get('entity_type'):
            query += " AND entity_type = ?"
            params.append(filters['entity_type'])
        if filters.get('start_date'):
            query += " AND timestamp >= ?"
            params.append(filters['start_date'])
        if filters.get('end_date'):
            query += " AND timestamp <= ?"
            params.append(filters['end_date'] + " 23:59:59")
            
    query += " ORDER BY timestamp DESC LIMIT 500"
    logs = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()
    return logs

def get_restricted_access_report(days=30):
    conn = get_db_connection()
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    query = """
        SELECT al.*, d.filename, d.confidentiality_level 
        FROM audit_log al
        JOIN documents d ON al.entity_id = d.id
        WHERE al.entity_type = 'document' 
          AND al.action LIKE 'VIEW%'
          AND al.timestamp >= ?
          AND (d.confidentiality_level = 'Confidential' OR d.confidentiality_level = 'Restricted')
        ORDER BY al.timestamp DESC
    """
    report = [dict(row) for row in conn.execute(query, (start_date,)).fetchall()]
    conn.close()
    return report

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
    # 1. Get User Role & Scope
    cursor_user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_role_data = cursor_user.fetchone()
    
    # Defaults if user not found (Guest)
    role = user_role_data['role'] if user_role_data else 'Viewer'
    scope = user_role_data['scope'] if user_role_data else 'Holding' # Holding means Global
    scope_val = user_role_data['assigned_scope_value'] if user_role_data else 'KBN Group'

    # 2. Need-to-Know: Department Isolation
    # If not Admin and scope is limited, strictly filter by container department
    if role != 'Admin' and not is_admin:
        if scope == 'Subsidiary':
            query += " AND c.subsidiary = ?"
            params.append(scope_val)
        elif scope == 'Department':
            # Strict Isolation: Only documents in this Department's containers
            # OR documents explicitly shared (access_requests)? For now, strict isolation.
            query += " AND c.department = ?"
            params.append(scope_val)

        # 3. Confidentiality Clearance (Role-Based)
        # Fetch allowed levels for this role (Global policy for now, could be Dept specific)
        policy = conn.execute("SELECT allowed_levels FROM access_policies WHERE role = ? LIMIT 1", (role,)).fetchone()
        allowed_levels_str = policy['allowed_levels'] if policy else 'Public,Internal'
        allowed_levels = [l.strip() for l in allowed_levels_str.split(',')]
        
        # Build strict filter: (Level IN allowed OR Owner OR Admin OR Access Approved)
        # Assuming is_admin handles Admin case.
        # We need to filter rows where:
        # (effective_confidentiality IN allowed_levels) OR (uploader_id = user) OR (owner_id = user)
        # Since effective_confidentiality is calculated in SELECT, we might need a WHERE clause using COALESCE(d.confidentiality, c.confidentiality, 'Internal')
        
        placeholders = ','.join(['?'] * len(allowed_levels))
        
        # We add the permission logic. Note: 'access_status' check logic for specific docs is complex in WHERE.
        # But we can check access_requests table.
        
        # Complex permission block
        permission_clause = f"""
            AND (
                COALESCE(d.confidentiality_level, c.confidentiality_level, 'Internal') IN ({placeholders})
                OR d.uploader_id = ?
                OR d.owner_id = ?
                OR EXISTS (SELECT 1 FROM access_requests ar WHERE ar.document_id = d.id AND ar.user_id = ? AND ar.status = 'Approved')
            )
        """
        query += permission_clause
        params.extend(allowed_levels)
        params.extend([user_id, user_id, user_id])
    
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
        if status == 'Published':
            query += " AND d.is_published = 1"
        elif status == 'Pending':
            query += " AND d.approval_status = 'Pending Approval'"
        elif status in ['Soft_Deleted', 'Pending_Deletion', 'Archived', 'Intake']:
             query += " AND d.status = ?"
             params.append(status)
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
            SELECT d.*, c.subsidiary, c.department, c.function, 
                   COALESCE(d.confidentiality_level, c.confidentiality_level, 'Internal') as effective_confidentiality,
                   CASE WHEN fav.document_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
                   snippet(documents_fts, 2, '<b>', '</b>', '...', 15) as ocr_snippet,
                   rank as relevance,
                   (SELECT status FROM access_requests WHERE user_id = ? AND document_id = d.id AND status = 'Approved') as access_status
            FROM documents d
            JOIN documents_fts f ON d.id = f.id
            LEFT JOIN containers c ON d.container_id = c.id
            LEFT JOIN favorites fav ON d.id = fav.document_id AND fav.user_id = ?
            WHERE f.documents_fts MATCH ? AND """ + query[query.find("WHERE")+6:] # Reuse filters
        params.insert(0, user_id) # For access_status subquery
        # params[1] is already user_id (from original params initialization for favorites)
        params.insert(2, search)
        query += " ORDER BY relevance ASC, d.upload_date DESC"
    else:
        # Non-search query
        # We need to inject the extra columns for confidentiality and access status
        select_clause = """
            SELECT d.*, c.subsidiary, c.department, c.function,
                   COALESCE(d.confidentiality_level, c.confidentiality_level, 'Internal') as effective_confidentiality,
                   CASE WHEN fav.document_id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
                   (SELECT status FROM access_requests WHERE user_id = ? AND document_id = d.id AND status = 'Approved') as access_status
        """
        params.insert(0, user_id) # For access_status
        query = select_clause + query[query.find("FROM"):]
        query += " ORDER BY d.upload_date DESC"
    
    cursor = conn.execute(query, params)
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documents

def get_users():
    conn = get_db_connection()
    users = [dict(row) for row in conn.execute("SELECT * FROM users").fetchall()]
    conn.close()
    return users

def request_access(user_id, doc_id, reason):
    conn = get_db_connection()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO access_requests (user_id, document_id, reason, request_date) VALUES (?, ?, ?, ?)", 
                 (user_id, doc_id, reason, date))
    conn.commit()
    conn.close()

def get_access_requests(status='Pending'):
    conn = get_db_connection()
    query = """
        SELECT ar.*, d.filename, u.name as user_name 
        FROM access_requests ar
        JOIN documents d ON ar.document_id = d.id
        JOIN users u ON ar.user_id = u.id
    """
    if status:
        query += " WHERE ar.status = ?"
        cursor = conn.execute(query, (status,))
    else:
        cursor = conn.execute(query)
        
    reqs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reqs

def process_access_request(req_id, status, reviewer, expiry=None):
    conn = get_db_connection()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE access_requests SET status = ?, reviewed_by = ?, review_date = ?, expiry_date = ? WHERE id = ?", 
                 (status, reviewer, date, expiry, req_id))
    conn.commit()
    conn.close()

def get_analytics_stats():
    conn = get_db_connection()
    
    # 1. Total Documents
    total = conn.execute("SELECT COUNT(*) as count FROM documents").fetchone()['count']
    
    # 2. By Category
    cat_cursor = conn.execute("SELECT category, COUNT(*) as count FROM documents GROUP BY category")
    by_category = {str(row['category'] or 'Unclassified'): row['count'] for row in cat_cursor.fetchall()}
    
    # 3. By Status (OCR Status)
    try:
        status_cursor = conn.execute("SELECT ocr_status, COUNT(*) as count FROM documents GROUP BY ocr_status")
        by_status = {str(row['ocr_status'] or 'Unknown'): row['count'] for row in status_cursor.fetchall()}
    except Exception as e:
        print(f"Error in status stats: {e}")
        by_status = {}
    except Exception as e:
        print(f"Error in status stats: {e}")
        by_status = {}
    
    # 4. Daily Throughput
    try:
        throughput_cursor = conn.execute("""
            SELECT date(upload_date) as date, COUNT(*) as count 
            FROM documents 
            GROUP BY date(upload_date) 
            ORDER BY date DESC LIMIT 7
        """)
        daily_throughput = [dict(row) for row in throughput_cursor.fetchall()]
        # Sort manually to be safe? No, SQL handles it.
        # Check for None dates
        daily_throughput = [d for d in daily_throughput if d['date']]
    except Exception as e:
        print(f"Error in throughput stats: {e}")
        daily_throughput = []
    
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

def assign_documents(doc_ids, user_id, assigner):
    conn = get_db_connection()
    try:
        # doc_ids is a list of IDs
        placeholders = ','.join(['?'] * len(doc_ids))
        conn.execute(f"UPDATE documents SET assigned_to = ? WHERE id IN ({placeholders})", [user_id] + doc_ids)
        conn.commit()
        
        # Log audit for each? Or one bulk log? Bulk log is cleaner for system, but singular logs better for history.
        # Let's do one bulk log entry for the batch of assignments to avoid spamming audit log
        log_audit('workload', 0, 'ASSIGN_BULK', f"Assigned {len(doc_ids)} docs to {user_id}", assigner)
        return True
    except Exception as e:
        print(f"Assignment failed: {e}")
        return False
    finally:
        conn.close()

def update_sla_status(doc_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE documents SET sla_status = ? WHERE id = ?", (status, doc_id))
    conn.commit()
    conn.close()

def get_workload_stats():
    conn = get_db_connection()
    
    # By Status
    status_counts = {row['ocr_status']: row['count'] for row in conn.execute("SELECT ocr_status, COUNT(*) as count FROM documents GROUP BY ocr_status").fetchall()}
    
    # By SLA Status
    sla_counts = {row['sla_status']: row['count'] for row in conn.execute("SELECT sla_status, COUNT(*) as count FROM documents WHERE sla_status IS NOT NULL GROUP BY sla_status").fetchall()}
    
    # By Assignee
    assignee_counts = {row['assigned_to']: row['count'] for row in conn.execute("SELECT assigned_to, COUNT(*) as count FROM documents WHERE assigned_to IS NOT NULL GROUP BY assigned_to").fetchall()}
    
    # Priority Breakdown
    priority_counts = {row['priority']: row['count'] for row in conn.execute("SELECT priority, COUNT(*) as count FROM documents GROUP BY priority").fetchall()}

    conn.close()
    return {
        "status_distribution": status_counts,
        "sla_status": sla_counts,
        "assignee_load": assignee_counts,
        "priority_breakdown": priority_counts
    }
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
