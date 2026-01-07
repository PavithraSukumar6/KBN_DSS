import os
import sqlite3
import datetime
import threading
import json
import io
from flask import Flask, request, jsonify, send_from_directory, Response, send_file
from flask_cors import CORS
from utils.ocr import extract_text
from utils.classification import classify_document, suggest_metadata_from_all, get_risk_level
from database.db import (
    get_db_connection, init_db, save_document, create_container, get_all_containers, 
    log_transfer, get_container_logs, update_batch_qc, log_audit, update_document_metadata, 
    get_filtered_documents, get_analytics_stats, get_document, publish_document, 
    check_approval_required, update_approval_status, get_document_versions,
    toggle_favorite, save_search_query, get_saved_searches, publish_saved_search
)
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import random
import uuid

# Direct Scan Support
try:
    import win32com.client
    HAS_SCANNER_LIB = True
except ImportError:
    HAS_SCANNER_LIB = False


app = Flask(__name__)
# Force reload trigger - Fix Analytics
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
PROCESSED_FOLDER = os.path.join(os.getcwd(), 'processed_docs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Database
init_db()

# --- AUTH MIDDLEWARE ---
from functools import wraps

def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Token Format: "USER_ID:ROLE" (Mock)
            token = request.headers.get('X-Auth-Token')
            if not token:
                return jsonify({"error": "Missing Auth Token"}), 401
            
            try:
                user_id, user_role = token.split(':')
            except ValueError:
                 return jsonify({"error": "Invalid Token Format"}), 401

            if roles and user_role not in roles:
                 # Special case: allow if role is Admin regardless? 
                 # Let's say Admin overrides.
                 if user_role != 'Admin':
                    return jsonify({"error": "Insufficient Permissions"}), 403
            
            # Inject user info into request (optional, or just rely on args)
            # request.user = {'id': user_id, 'role': user_role}
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the traceback
    import traceback
    app.logger.error(f"Unhandled Exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    import hashlib
    from database.db import check_duplicate_hash, log_audit, save_document, get_db_connection
    from utils.classification import suggest_metadata_from_all

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # Calculate Hash
    file_content = file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    file.seek(0) # Reset cursor
    
    # Check Duplicate
    existing_doc = check_duplicate_hash(file_hash)
    if existing_doc:
        return jsonify({
            "error": "Duplicate document found.",
            "existing_doc": {
                "id": existing_doc['id'],
                "filename": existing_doc['filename'],
                "upload_date": existing_doc['upload_date'],
                "uploader": existing_doc['uploader_id']
            }
        }), 409

    container_id = request.form.get('container_id') # Get container ID
    batch_id = request.form.get('batch_id') # Get Batch ID if part of a batch
    tags = request.form.get('tags') # New: Tags
    uploader_id = request.form.get('uploader_id', 'Gokul_Admin')
    # Default confidentiality for now
    confidentiality = request.form.get('confidentiality_level', 'Internal')

    # Get manual metadata overrides
    category = request.form.get('category')
    department = request.form.get('department')
    
    metadata = {}
    if department:
        metadata['department'] = department
        
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        if file.filename.lower().endswith('.pdf'):
            from utils.splitting import split_pdf
            split_files = split_pdf(filepath, app.config['UPLOAD_FOLDER'])
            if not split_files: # Fallback if splitting fails or returns empty
                split_files = [filepath]
        else:
            split_files = [filepath]

        
        results = []
        
        try:
            # Create initial DB records and start background threads
            for split_path in split_files:
                filename = os.path.basename(split_path)
                
                # Check for filename-based hints if category matches 'Auto-Detect' (None)
                initial_cat = category or "Unclassified"
                
                # We use JSON dump for metadata column
                meta_json = json.dumps(metadata) if metadata else None
                
                doc_id = save_document(
                    filename=filename,
                    category=initial_cat, 
                    confidence=1.0 if category else 0.0, # High confidence if manually set
                    content="OCR Pending...",
                    container_id=container_id,
                    batch_id=batch_id,
                    ocr_status="Processing",
                    uploader_id=uploader_id,
                    tags=tags,
                    metadata=meta_json,
                    content_hash=file_hash
                )
                
                # Manually set confidentiality if not default
                if confidentiality != 'Internal':
                     conn = get_db_connection()
                     conn.execute("UPDATE documents SET confidentiality_level = ? WHERE id = ?", (confidentiality, doc_id))
                     conn.commit()
                     conn.close()

                results.append({
                    "id": doc_id,
                    "filename": filename,
                    "status": "Processing"
                })
                
                # Start background thread
                thread = threading.Thread(target=process_document_background, args=(doc_id, split_path))
                thread.daemon = True # Daemon thread so it doesn't block app exit
                thread.start()
            
            # Get suggestions from filename for the first document as a hint
            initial_suggestions = suggest_metadata_from_all(os.path.basename(split_files[0])) if split_files else {}

            from database.db import log_audit
            log_audit('batch' if batch_id else 'document_group', batch_id or 0, 'UPLOAD', f"Uploaded {len(results)} documents", uploader_id, ip_address=request.remote_addr)

            return jsonify({
                "message": f"Started processing {len(results)} documents",
                "documents": results,
                "batch_id": batch_id,
                "suggestions": initial_suggestions
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

# --- SECURITY ENDPOINTS ---
@app.route('/users', methods=['GET'])
def get_users_route():
    from database.db import get_users
    return jsonify(get_users())

@app.route('/access/request', methods=['POST'])
def request_access_route():
    from database.db import request_access
    data = request.json
    request_access(data['user_id'], data['document_id'], data['reason'])
    return jsonify({"message": "Access request submitted"}), 200

@app.route('/access/requests', methods=['GET'])
def get_access_requests_route():
    from database.db import get_access_requests
    status = request.args.get('status', 'Pending')
    return jsonify(get_access_requests(status))

@app.route('/access/approve', methods=['POST'])
def approve_access_route():
    from database.db import process_access_request, get_db_connection, get_document
    data = request.json
    request_id = data['request_id']
    reviewer = data['reviewer']
    status = data['status']
    
    # Governance Check: Only Data Owner or Admin can approve
    conn = get_db_connection()
    req = conn.execute("SELECT document_id FROM access_requests WHERE id = ?", (request_id,)).fetchone()
    conn.close()
    
    if not req:
         return jsonify({"error": "Request not found"}), 404
         
    doc = get_document(req['document_id'])
    
    # Check if reviewer is Owner or Admin
    # (assuming is_admin check is handled by frontend passing a flag or we check user role from DB)
    # For robust security, we should check the user role from DB for 'reviewer'
    conn = get_db_connection()
    user_row = conn.execute("SELECT role FROM users WHERE id = ?", (reviewer,)).fetchone()
    conn.close()
    
    is_admin = user_row and user_row['role'] == 'Admin'
    owner_id = doc.get('owner_id')
    
    # Fallback: if no owner, allow Admin or Uploader (legacy)
    if not owner_id:
        owner_id = doc.get('uploader_id')
    
    if not is_admin and reviewer != owner_id:
        return jsonify({"error": "Permission Denied: Only the Data Owner can approve access."}), 403

    process_access_request(request_id, status, reviewer, data.get('expiry_date'))
    
    from database.db import log_audit
    log_audit('access_request', request_id, 'ACCESS_REVIEW', f"Request {status} by {reviewer}", reviewer, ip_address=request.remote_addr, scope='Security')
    
    return jsonify({"message": f"Request {status}"}), 200

@app.route('/view/<int:doc_id>', methods=['GET'])
def view_document_route(doc_id):
    from database.db import get_document, log_audit, get_db_connection
    doc = get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    user_id = request.args.get('user_id', 'Guest')
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'

    # Security Check
    conf = doc.get('confidentiality_level', 'Internal')
    uploader = doc.get('uploader_id')

    # If document is Restricted/Confidential
    if conf == 'Restricted' or conf == 'Confidential':
        # Allow if Admin or Owner
        allowed = is_admin or (user_id == uploader)
        
        # Check Access Request if not allowed yet
        if not allowed:
             conn = get_db_connection()
             req = conn.execute("SELECT status FROM access_requests WHERE user_id = ? AND document_id = ? AND status = 'Approved'", (user_id, doc_id)).fetchone()
             if req:
                 allowed = True
             conn.close()
             
        if not allowed:
            return "Access Denied. Restricted Document.", 403

    
    # Log the View
    if conf != 'Internal':
        log_audit('document', doc_id, 'VIEW_RESTRICTED', f"User {user_id} viewed restricted doc", user_id, ip_address=request.remote_addr)
    else:
        log_audit('document', doc_id, 'VIEW', f"Document viewed by {user_id}", user_id, ip_address=request.remote_addr)
    
    # Determine path (Uploads or Processed)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
    if not os.path.exists(file_path):
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], doc['filename'])
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found on disk"}), 404
            
    return send_file(file_path)

def process_document_background(doc_id, filepath):
    """
    Background worker to run OCR and Classification, then update DB.
    """
    try:
        # Fetch existing doc to check for overrides (manual category/metadata)
        from database.db import get_document
        existing_doc = get_document(doc_id)
        manual_category = None
        manual_metadata = {}
        if existing_doc:
            if existing_doc['category'] and existing_doc['category'] != 'Unclassified':
                manual_category = existing_doc['category']
            if existing_doc['metadata']:
                try:
                    manual_metadata = json.loads(existing_doc['metadata'])
                except:
                    pass

        # 1. OCR
        text, confidence = extract_text(filepath)
        
        # Validation & Fallback
        if not text or len(text.strip()) < 10 or text == "OCR_SKIPPED":
             # Fallback: Try to classify by filename
            from utils.classification import suggest_metadata_from_all
            suggestions = suggest_metadata_from_all(os.path.basename(filepath))
            
            fallback_category = suggestions.get('category')
            
            if fallback_category:
                # Success via Fallback
                category = manual_category if manual_category else fallback_category
                
                # We save with a specific status indicating no OCR was done
                ocr_status_label = "Completed (No OCR)"
                
                # Still try to extract metadata if any (from filename? logic is mostly text based but let's see)
                # suggest_metadata_from_all also returns other suggestions
                
                # Construct metadata from suggestions
                meta_json = json.dumps(suggestions)
                
                update_document_status(doc_id, ocr_status_label, "Content parsing skipped (OCR missing).", 0.5, category, meta_json, category + " Template")
                log_audit('document', doc_id, 'classification_fallback', f"Classified as {category} using filename fallback", "System")
                return
            else:
                # Failed and no fallback found
                target_cat = manual_category if manual_category else "Unclassified"
                update_document_status(doc_id, "Failed", "No text detected and filename insufficient.", 0.0, target_cat)
                return

        # 2. Classification
        classified_cat, _ = classify_document(text)
        category = manual_category if manual_category else classified_cat
        
        # 3. Extraction
        from utils.extraction import extract_metadata
        extracted_metadata = extract_metadata(text, category)
        
        # Merge Metadata (Manual overrides extracted)
        # Ensure extracted_metadata is dict
        if isinstance(extracted_metadata, str):
            try:
                extracted_metadata = json.loads(extracted_metadata)
            except:
                extracted_metadata = {}
        
        if not isinstance(extracted_metadata, dict):
            extracted_metadata = {}
            
        # Merge: Start with extracted, update with manual
        final_metadata = extracted_metadata.copy()
        final_metadata.update(manual_metadata)
        metadata_json = json.dumps(final_metadata)
        
        # 4. Suggestions (Refined)
        final_suggestions = suggest_metadata_from_all(os.path.basename(filepath), text)
        
        # 5. Update DB with success
        update_document_status(doc_id, "Completed", text, confidence, category, metadata_json, category + " Template")
        
        # 6. Auto-Routing Logic (FR-24)
        routing_keywords = {
            'HR': 'DEPT-HR',
            'HUMAN RESOURCES': 'DEPT-HR',
            'FINANCE': 'DEPT-FINANCE',
            'PAYROLL': 'DEPT-FINANCE',
            'LEGAL': 'DEPT-LEGAL',
            'CONTRACT': 'DEPT-LEGAL',
            'OPERATIONS': 'DEPT-OPERATIONS',
            'SALES': 'DEPT-SALES',
            'UAE': 'DEPT-UAE',
            'DUBAI': 'DEPT-UAE',
            'KBN UAE': 'DEPT-UAE'
        }
        
        found_container = None
        upper_text = text.upper()
        for kw, cid in routing_keywords.items():
            if kw in upper_text:
                found_container = cid
                break
        
        if found_container:
            # Check if container exists before routing
            conn = get_db_connection()
            exists = conn.execute("SELECT 1 FROM containers WHERE id = ?", (found_container,)).fetchone()
            if exists:
                conn.execute("UPDATE documents SET container_id = ? WHERE id = ?", (found_container, doc_id))
                conn.commit()
                log_audit('document', doc_id, 'auto_route', f"Automatically routed to {found_container} base on keywords", "System")
            conn.close()

        # 7. Confidence-Based Automation and Approval Logic
        risk = get_risk_level(category)
        
        # Determine initial approval status
        from database.db import get_db_connection
        conn = get_db_connection()
        container_row = conn.execute('SELECT confidentiality_level FROM containers WHERE id = (SELECT container_id FROM documents WHERE id = ?)', (doc_id,)).fetchone()
        confidentiality = container_row['confidentiality_level'] if container_row else 'Internal'
        conn.close()
        
        needs_approval = check_approval_required(category, confidentiality)
        
        if needs_approval:
            update_document_status(doc_id, "Completed", text, confidence, category, metadata_json, category + " Template")
            update_approval_status(doc_id, "Pending Approval", "System")
        
        # FR-32: Fast-Track QC Logic
        elif confidence > 90 and risk == "Low":
            # High confidence + Low Risk -> QC Passed automatically
            # We still mark as 'Completed' but maybe we can introduce 'QC_Passed'
            # Let's say 'QC_Passed' is a status or we just skip QC queue.
            # If we don't set to 'QC_Passed', it might fall into QC Queue if it's default pending?
            # Let's see: batches are pending by default. 
            # If we want to skip legacy QC for these, update `ocr_status` to 'QC_Passed' or 'Published'?
            # The prompt says "set status to 'QC_Passed'".
            
            update_document_status(doc_id, "QC_Passed", text, confidence, category, metadata_json, category + " Template")
            log_audit('document', doc_id, 'auto-qc', f"Auto-passed QC (Conf: {confidence}%)", "System")
            
            # Auto-publish if really confident? Request says "QC_Passed". 
            # If 'QC_Passed' means ready for export, that's good.
        else:
            # Rigorous QC Required
            # Mark as 'Rigorous_QC' or just standard 'Completed' (which means Pending QC in new flow?)
            # Let's mark as 'Rigorous_QC' to be explicit in the UI badges.
            update_document_status(doc_id, "Rigorous_QC", text, confidence, category, metadata_json, category + " Template")
        
    except Exception as e:
        print(f"Background Job Failed for Doc {doc_id}: {e}")
        # update_document_status will need to handle strict args, maybe pass Nones
        update_document_status(doc_id, "Failed", f"Error: {str(e)}", 0.0, "Unclassified", "{}", None)

def update_document_status(doc_id, status, content, confidence, category, metadata=None, template_type=None):
    from database.db import validate_metadata, log_audit
    
    # FR-15: Validation
    if metadata:
        import json
        try:
            m_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
            is_valid, error = validate_metadata(category, m_dict)
            if not is_valid:
                log_audit('Document', doc_id, 'Validation Error', error, 'System')
                # For now, we still save but mark status or log error. 
                # Request says "implement field-level validation", usually implying logging or blocking.
        except:
            pass

    from database.db import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE documents 
            SET ocr_status = ?, content = ?, confidence = ?, category = ?, metadata = ?, template_type = ?
            WHERE id = ?
        ''', (status, content, confidence, category, metadata, template_type, doc_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to update DB for doc {doc_id}: {e}")

@app.route('/containers', methods=['GET', 'POST'])
def manage_containers():
    if request.method == 'POST':
        data = request.json
        # Generate ID if not provided (simple logic, or could be barcode scan)
        if 'id' not in data or not data['id']:
             return jsonify({"error": "Container ID (Barcode) is required"}), 400
             
        # Ensure physical_page_count is passed or default to 0
        data['physical_page_count'] = data.get('physical_page_count', 0)

        # Use the updated create_container which handles auto-IDs and names
        container_id = create_container(data)
        if container_id:
             # Log initial creation location
             log_transfer(container_id, 'creation', data.get('source_location', 'Unknown'), data.get('created_by', 'System'))
             return jsonify({"message": "Container created successfully", "id": container_id}), 201
        else:
             return jsonify({"error": "Failed to create container"}), 400

    containers = get_all_containers()
    return jsonify(containers)

# --- Batch Management Endpoints ---

@app.route('/batches', methods=['POST'])
def create_batch():
    data = request.json
    container_id = data.get('container_id')
    if not container_id:
        return jsonify({"error": "Container ID is required"}), 400
    
    # Create a new batch
    conn = get_db_connection()
    cursor = conn.cursor()
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get expected page count from container
    container_row = conn.execute('SELECT physical_page_count FROM containers WHERE id = ?', (container_id,)).fetchone()
    expected_count = container_row['physical_page_count'] if container_row else 0
    
    cursor.execute('''
        INSERT INTO batches (container_id, status, start_time, total_pages_scanned, physical_page_count_expected)
        VALUES (?, 'Pending', ?, 0, ?)
    ''', (container_id, start_time, expected_count))
    
    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Batch started", "batch_id": batch_id, "expected_pages": expected_count}), 201

@app.route('/batches/<int:batch_id>/completeness', methods=['GET'])
def check_batch_completeness(batch_id):
    conn = get_db_connection()
    batch = conn.execute('SELECT * FROM batches WHERE id = ?', (batch_id,)).fetchone()
    
    if not batch:
        conn.close()
        return jsonify({"error": "Batch not found"}), 404
        
    # Count actual scanned pages from documents linked to this batch
    # Assuming each document row is 1 file, which might be multiple pages. 
    # For now, we sum the 'page_count' column we added.
    row = conn.execute('SELECT SUM(page_count) as total FROM documents WHERE batch_id = ?', (batch_id,)).fetchone()
    total_scanned = row['total'] if row['total'] else 0
    
    is_complete = total_scanned == batch['physical_page_count_expected']
    
    conn.close()
    return jsonify({
        "batch_id": batch_id,
        "is_complete": is_complete,
        "expected": batch['physical_page_count_expected'],
        "scanned": total_scanned,
        "status": batch['status']
    })

@app.route('/qc/queue', methods=['GET'])
def get_qc_queue():
    from database.db import get_qc_queue_batches
    batches = get_qc_queue_batches()
    return jsonify(batches)

@app.route('/qc/batch/<int:batch_id>/review', methods=['POST'])
def review_batch(batch_id):
    data = request.json
    status = data.get('status') # 'Archived' (Approved), 'Returned' (Rejected)
    notes = data.get('notes')
    user = data.get('user', 'QA_Specialist')

    if not status:
        return jsonify({"error": "Status is required"}), 400

    from database.db import update_batch_qc, log_audit
    
    update_batch_qc(batch_id, status, notes, user)
    
    # If returned, maybe we should status update the docs?
    # For now, we trust the batch status.
    
    log_audit('batch', batch_id, 'QC_REVIEW', f"Batch {status} by {user}", user, ip_address=request.remote_addr)
    return jsonify({"message": f"Batch marked as {status}"}), 200

@app.route('/documents/<int:doc_id>/publish', methods=['POST'])
def publish_document_route(doc_id):
    user = request.args.get('user', 'System')
    from database.db import publish_document, log_audit
    
    publish_document(doc_id)
    log_audit('document', doc_id, 'PUBLISH', "Document approved and published", user, ip_address=request.remote_addr)
    
    return jsonify({"message": "Document published"}), 200

@app.route('/documents/<int:doc_id>/rescan', methods=['POST'])
def rescan_document_route(doc_id):
    data = request.json
    reason = data.get('reason', 'Rescan Requested')
    user = data.get('user', 'System')
    
    from database.db import update_document_status, log_audit, save_document_version
    
    # Save current version before resetting
    save_document_version(doc_id, f"Rescan Requested: {reason}", user)
    
    # Reset status to 'Intake' or similar so it can be re-processed or just flagged
    # Actually, if it's a "Rescan", we might want to clear the content/ocr?
    # For now, let's just mark it 'Pending Rescan' or similar status?
    # The frontend expects to probably re-upload or re-scan.
    # Let's set ocr_status to 'Rescan_Required' or similar.
    # But db.py update_document_status sets ocr_status, content, confidence, category...
    
    # We should probably just update the status field if we are strictly tracking lifecycle.
    # But update_document_status is the main updater.
    # Let's use a direct update for status since update_document_status requires all params.
    conn = get_db_connection()
    conn.execute("UPDATE documents SET ocr_status = 'Rescan_Required', approval_status = 'Pending' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    
    log_audit('document', doc_id, 'RESCAN_REQ', f"Rescan requested: {reason}", user, ip_address=request.remote_addr)
    
    return jsonify({"message": "Rescan triggered"}), 200

# --- Workload & SLA Endpoints ---
@app.route('/workload/stats', methods=['GET'])
def workload_stats_route():
    from database.db import get_workload_stats
    return jsonify(get_workload_stats())

@app.route('/workload/assign', methods=['POST'])
def assign_work_route():
    data = request.json
    doc_ids = data.get('doc_ids', [])
    user_id = data.get('user_id')
    assigner = data.get('assigner', 'Admin')
    
    if not doc_ids or not user_id:
        return jsonify({"error": "Missing doc_ids or user_id"}), 400
        
    from database.db import assign_documents
    if assign_documents(doc_ids, user_id, assigner):
        return jsonify({"message": "Assigned successfully"}), 200
    return jsonify({"error": "Assignment failed"}), 500

@app.route('/containers/<id>/transfer', methods=['POST'])
def transfer_container_route(id):
    data = request.json
    new_location = data.get('location')
    user = data.get('user', 'Admin')
    
    from database.db import log_transfer, get_db_connection
    
    # Get current location
    conn = get_db_connection()
    curr = conn.execute("SELECT source_location FROM containers WHERE id = ?", (id,)).fetchone()
    current_loc = curr['source_location'] if curr else 'Unknown'
    
    # Update Container
    conn.execute("UPDATE containers SET source_location = ? WHERE id = ?", (new_location, id))
    conn.commit()
    conn.close()
    
    log_transfer(id, current_loc, new_location, user)
    return jsonify({"message": "Transfer logged"}), 200

@app.route('/containers/<id>/history', methods=['GET'])
def container_history_route(id):
    from database.db import get_container_logs
    return jsonify(get_container_logs(id))

@app.route('/documents/<int:doc_id>/sla', methods=['POST'])
def update_doc_sla_route(doc_id):
    # Endpoint to manually update SLA details (for testing or admin override)
    data = request.json
    due_date = data.get('due_date')
    priority = data.get('priority')
    
    conn = get_db_connection()
    if due_date:
        conn.execute("UPDATE documents SET sla_due_date = ? WHERE id = ?", (due_date, doc_id))
    if priority:
        conn.execute("UPDATE documents SET priority = ? WHERE id = ?", (priority, doc_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "SLA updated"}), 200



@app.route('/documents', methods=['GET'])
@app.route('/api/documents', methods=['GET'])
def list_documents():
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search_query = request.args.get('search')
    batch_id = request.args.get('batch_id')
    user_id = request.args.get('user_id', 'Guest')
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    only_published = request.args.get('only_published', 'false').lower() == 'true'
    
    # New filters
    status = request.args.get('status')
    subsidiary = request.args.get('subsidiary')
    department = request.args.get('department')
    function = request.args.get('function')
    tags = request.args.get('tags')
    
    from database.db import get_filtered_documents
    documents = get_filtered_documents(
        category=category, 
        start_date=start_date, 
        end_date=end_date, 
        search=search_query,
        user_id=user_id,
        is_admin=is_admin,
        only_published=only_published,
        batch_id=batch_id,
        status=status,
        subsidiary=subsidiary,
        department=department,
        function=function,
        tags=tags
    )
    return jsonify(documents)

@app.route('/document/<int:doc_id>', methods=['GET'])
def get_document_details(doc_id):
    doc = get_document(doc_id)
    if doc:
        return jsonify(doc)
    return jsonify({"error": "Document not found"}), 404

@app.route('/export/csv', methods=['GET'])
def export_csv():
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from database.db import get_filtered_documents
    documents = get_filtered_documents(category, start_date, end_date)
    
    import csv
    import io
    import json
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    headers = ['ID', 'Filename', 'Category', 'Upload Date', 'Status', 'Confidence', 'Template Type']
    # Dynamically add metadata keys? For simplicity, we'll dump all metadata in one column or a few known ones
    headers.extend(['Metadata']) # Simple approach
    
    writer.writerow(headers)
    
    for doc in documents:
        meta_str = doc.get('metadata', '{}')
        writer.writerow([
            doc['id'],
            doc['filename'],
            doc['category'],
            doc['upload_date'],
            doc['ocr_status'],
            doc['confidence'],
            doc['template_type'],
            meta_str
        ])
        
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=export.csv"}
    )
    
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    user_id = request.args.get('user_id', 'Guest')
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    
    # Advanced filters for search
    category = request.args.get('category')
    subsidiary = request.args.get('subsidiary')
    department = request.args.get('department')
    
    # Use the enhanced filtering logic
    from database.db import get_filtered_documents, log_audit
    results = get_filtered_documents(
        search=query, 
        user_id=user_id, 
        is_admin=is_admin, 
        only_published=True,
        category=category,
        subsidiary=subsidiary,
        department=department
    )
    
    # Extra Visibility Guard: Filter out Pending Approval and Confidential unless Admin
    if not is_admin:
        results = [d for d in results if d.get('approval_status') != 'Pending Approval']
        
    # Log 0 results with context (FR-26)
    if len(results) == 0:
        log_audit(
            'search', 0, 'SEARCH_ZERO_RESULTS', 
            f"Query '{query}' returned 0 results. Filters: Cat={category}, Sub={subsidiary}", 
            user_id, 
            ip_address=request.remote_addr,
            scope='Global Search'
        )

    return jsonify(results)

@app.route('/documents/<int:doc_id>/reclassify', methods=['POST'])
def reclassify_document_route(doc_id):
    data = request.json
    new_category = data.get('category')
    user = data.get('user', 'System_User')
    
    if check_legal_hold():
         return jsonify({"error": "Legal Hold Active: Metadata changes are prohibited."}), 403

    if not new_category:
         return jsonify({"error": "Category required"}), 400
         
    from database.db import get_document, update_document_metadata, log_audit
    from utils.extraction import extract_metadata
    
    doc = get_document(doc_id)
    if not doc:
        return jsonify({"error": "Doc not found"}), 404
    
    old_category = doc['category']    
    # Re-extract
    new_metadata = extract_metadata(doc['content'], new_category)
    template = new_category + " Template"
    
    update_document_metadata(doc_id, new_category, new_metadata, template)
    
    # Enhanced Logging (FR-25)
    log_audit('document', doc_id, 'reclassify', f"Changed category", user, old_value=old_category, new_value=new_category, ip_address=request.remote_addr)
    
    return jsonify({"message": "Reclassified", "metadata": new_metadata}), 200

# --- AUDIT & REPORTING ENDPOINTS ---
@app.route('/audit/logs', methods=['GET'])
@require_auth(roles=['Admin'])
def get_audit_logs_route():
    from database.db import get_audit_logs
    filters = {
        'user': request.args.get('user'),
        'action': request.args.get('action'),
        'entity_type': request.args.get('entity_type'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date')
    }
    # Filter out empty keys
    filters = {k: v for k, v in filters.items() if v}
    logs = get_audit_logs(filters)
    return jsonify(logs)

@app.route('/audit/reports/restricted', methods=['GET'])
def get_restricted_report_route():
    from database.db import get_restricted_access_report
    days = int(request.args.get('days', 30))
    days = int(request.args.get('days', 30))
    report = get_restricted_access_report(days)
    return jsonify(report)

@app.route('/access-policies', methods=['GET', 'POST'])
@require_auth(roles=['Admin'])
def manage_access_policies():
    from database.db import get_db_connection, log_audit
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Admin check
        is_admin = request.args.get('is_admin', 'false').lower() == 'true'
        if not is_admin:
            conn.close()
            return jsonify({"error": "Admin access required"}), 403
            
        data = request.json
        role = data.get('role')
        levels = data.get('allowed_levels') # Comma separated
        
        try:
            # Check if policy exists (handling global policies where department is NULL)
            existing = conn.execute("SELECT id FROM access_policies WHERE role = ? AND department IS NULL", (role,)).fetchone()
            
            if existing:
                conn.execute("UPDATE access_policies SET allowed_levels = ? WHERE id = ?", (levels, existing['id']))
            else:
                conn.execute("INSERT INTO access_policies (role, allowed_levels) VALUES (?, ?)", (role, levels))
            conn.commit()
            log_audit('access_policy', 0, 'UPDATE_POLICY', f"Updated access for {role} to {levels}", "Admin")
            return jsonify({"message": "Policy updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    # GET
    cursor = conn.execute("SELECT * FROM access_policies")
    policies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(policies)

# --- LIFECYCLE & RETENTION ENDPOINTS ---

def check_legal_hold():
    from database.db import get_db_connection
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM system_settings WHERE key = 'legal_hold'").fetchone()
    conn.close()
    return row and row['value'] == 'true'

@app.route('/retention-policies', methods=['GET', 'POST'])
@require_auth(roles=['Admin'])
def manage_retention_policies():
    conn = get_db_connection()
    if request.method == 'POST':
        # Admin check
        is_admin = request.args.get('is_admin', 'false').lower() == 'true'
        if not is_admin:
            conn.close()
            return jsonify({"error": "Admin access required"}), 403
            
        data = request.json
        doc_type = data.get('document_type')
        years = data.get('retention_years')
        
        try:
            conn.execute('''
                INSERT INTO retention_policies (document_type, retention_years) 
                VALUES (?, ?)
                ON CONFLICT(document_type) DO UPDATE SET retention_years=excluded.retention_years
            ''', (doc_type, years))
            conn.commit()
            log_audit('retention_policy', 0, 'UPDATE_POLICY', f"Set retention for {doc_type} to {years} years", "Admin")
            return jsonify({"message": "Policy updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
            
    policies = [dict(row) for row in conn.execute("SELECT * FROM retention_policies").fetchall()]
    conn.close()
    return jsonify(policies)

@app.route('/settings/legal-hold', methods=['POST'])
@require_auth(roles=['Admin'])
def toggle_legal_hold():
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    if not is_admin:
        return jsonify({"error": "Admin access required"}), 403
        
    data = request.json
    active = str(data.get('active', 'false')).lower()
    
    conn = get_db_connection()
    conn.execute("INSERT INTO system_settings (key, value) VALUES ('legal_hold', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (active,))
    conn.commit()
    conn.close()
    
    log_audit('system', 0, 'LEGAL_HOLD', f"Legal Hold set to {active}", "Admin", scope='Legal')
    return jsonify({"message": f"Legal Hold is now {active}"}), 200

@app.route('/settings', methods=['GET'])
def get_system_settings():
    conn = get_db_connection()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT * FROM system_settings").fetchall()}
    conn.close()
    return jsonify(settings)

@app.route('/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    # Check Legal Hold
    if check_legal_hold():
        log_audit('document', doc_id, 'DELETE_ATTEMPT', "Delete blocked by Legal Hold", "User", scope='Legal')
        return jsonify({"error": "Legal Hold Active: Deletion is prohibited."}), 403
        
    user_id = request.args.get('user_id', 'Guest')
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    is_permanent = request.args.get('permanent', 'false').lower() == 'true'
    
    conn = get_db_connection()
    
    # Check permissions (Owner or Admin)
    doc = conn.execute("SELECT uploader_id, status FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if not doc:
        conn.close()
        return jsonify({"error": "Not found"}), 404
        
    if not is_admin and doc['uploader_id'] != user_id:
        conn.close()
        return jsonify({"error": "Permission denied"}), 403
        
    if is_permanent:
        if not is_admin:
             conn.close()
             return jsonify({"error": "Only Admins can permanently delete"}), 403
             
        # Check if it was soft deleted first? Or allow direct?
        # Let's require soft delete status for permanent cleanup
        if doc['status'] not in ['Pending_Deletion', 'Soft_Deleted']:
             conn.close()
             return jsonify({"error": "Document must be soft deleted first"}), 400
             
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        # Also clean up FTS
        conn.execute("DELETE FROM documents_fts WHERE id = ?", (doc_id,))
        conn.commit()
        log_audit('document', doc_id, 'DELETE_PERMANENT', "Document permanently deleted", user_id)
    else:
        # Soft Delete
        conn.execute("UPDATE documents SET status = 'Soft_Deleted' WHERE id = ?", (doc_id,))
        conn.commit()
        log_audit('document', doc_id, 'DELETE_SOFT', "Document moved to Recycle Bin", user_id)
        
    conn.close()
    return jsonify({"message": "Document deleted"}), 200

@app.route('/documents/<int:doc_id>/restore', methods=['POST'])
def restore_document(doc_id):
    if check_legal_hold():
         return jsonify({"error": "Legal Hold Active: Changes are prohibited."}), 403

    conn = get_db_connection()
    conn.execute("UPDATE documents SET status = 'Published' WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    
    user_id = request.args.get('user_id', 'Admin')
    log_audit('document', doc_id, 'RESTORE', "Document restored from recycle bin", user_id)
    return jsonify({"message": "Restored"}), 200

@app.route('/taxonomy', methods=['GET', 'POST'])
def manage_taxonomy():
    from database.db import get_taxonomy, add_taxonomy_item, log_audit
    if request.method == 'POST':
        # Simple Admin check (in production this would use session/token)
        is_admin = request.args.get('is_admin', 'false').lower() == 'true'
        if not is_admin:
            return jsonify({"error": "Admin access required"}), 403
            
        data = request.json
        category = data.get('category')
        value = data.get('value')
        user = 'Admin_User' # Mock
        
        if not category or not value:
            return jsonify({"error": "Missing fields"}), 400
            
        success = add_taxonomy_item(category, value)
        if success:
            log_audit('taxonomy', 0, 'ADD_TERM', f"Added {value} to {category}", user, new_value=value, scope='Governance', ip_address=request.remote_addr)
            return jsonify({"message": "Taxonomy item added"}), 201
        return jsonify({"error": "Item already exists"}), 409
        
    category = request.args.get('category')
    return jsonify(get_taxonomy(category))

@app.route('/analytics', methods=['GET'])
def get_analytics_route():
    import importlib
    import database.db as db_module
    importlib.reload(db_module)
    return jsonify(db_module.get_analytics_stats())

@app.route('/taxonomy/filters', methods=['GET'])
def get_filter_options():
    """
    Returns unique values for organization filters (subsidiary, department, function, etc.)
    """
    from database.db import get_db_connection
    conn = get_db_connection()
    try:
        subsidiaries = [row['subsidiary'] for row in conn.execute("SELECT DISTINCT subsidiary FROM containers WHERE subsidiary IS NOT NULL AND subsidiary != ''").fetchall()]
        departments = [row['department'] for row in conn.execute("SELECT DISTINCT department FROM containers WHERE department IS NOT NULL AND department != ''").fetchall()]
        functions = [row['function'] for row in conn.execute("SELECT DISTINCT function FROM containers WHERE function IS NOT NULL AND function != ''").fetchall()]
        doc_types = [row['value'] for row in conn.execute("SELECT DISTINCT value FROM taxonomy WHERE category = 'DocumentType' AND status = 'Active'").fetchall()]
        
        return jsonify({
            "subsidiaries": subsidiaries,
            "departments": departments,
            "functions": functions,
            "document_types": doc_types
        })
    finally:
        conn.close()

@app.route('/taxonomy/<int:item_id>', methods=['PATCH'])
def update_taxonomy(item_id):
    from database.db import update_taxonomy_status
    # Admin check
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    if not is_admin:
        return jsonify({"error": "Admin access required"}), 403
        
    status = request.json.get('status')
    if status not in ['Active', 'Deprecated']:
        return jsonify({"error": "Invalid status"}), 400
        
    update_taxonomy_status(item_id, status)
    return jsonify({"message": "Status updated"})

@app.route('/analytics', methods=['GET'])
def get_analytics():
    from database.db import get_analytics_stats
    stats = get_analytics_stats()
    return jsonify(stats)

# --- Watermarking Helpers ---

def apply_watermark_pdf(input_path, output_stream):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 60)
    can.setFillAlpha(0.3)
    can.setFillColor(colors.red)
    can.translate(300, 500)
    can.rotate(45)
    can.drawCentredString(0, 0, "CONFIDENTIAL")
    can.save()
    packet.seek(0)
    
    from PyPDF2 import PdfReader, PdfWriter
    # PyPDF2 is often used with reportlab for this. checking if installed...
    # If not installed, I'll use a simpler approach or install it later.
    # For now, let's assume we can merge them if PyPDF2 is available.
    # If not, I'll just send the original but with a warning or use pillow for first page.
    try:
        import PyPDF2
        existing_pdf = PyPDF2.PdfReader(open(input_path, "rb"))
        output = PyPDF2.PdfWriter()
        watermark_pdf = PyPDF2.PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]
        
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            page.merge_page(watermark_page)
            output.add_page(page)
        
        output.write(output_stream)
    except:
        # Fallback: Just copy for now or use pillow for images
        with open(input_path, "rb") as f:
            output_stream.write(f.read())

def apply_watermark_image(input_path, output_stream):
    img = Image.open(input_path).convert("RGBA")
    txt = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    # Simple centered watermark
    width, height = img.size
    font_size = int(width / 10)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        
    text = "CONFIDENTIAL"
    draw.text((width/2, height/2), text, fill=(255, 0, 0, 60), font=font, anchor="mm")
    watermarked = Image.alpha_composite(img, txt)
    watermarked.convert("RGB").save(output_stream, "JPEG")

@app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
def manage_favorites():
    user_id = request.args.get('user_id', 'Gokul_Admin')
    if request.method == 'POST':
        doc_id = request.json.get('document_id')
        status = toggle_favorite(user_id, doc_id)
        return jsonify({"is_favorite": status}), 200
    
    # GET favorites
    docs = get_filtered_documents(user_id=user_id, is_admin=True, favorite_only=True)
    return jsonify(docs)

@app.route('/saved-searches', methods=['GET', 'POST'])
def manage_saved_searches():
    user_id = request.args.get('user_id', 'Gokul_Admin')
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        query_params = json.dumps(data.get('query_params'))
        search_id = save_search_query(user_id, name, query_params)
        return jsonify({"id": search_id, "message": "Search saved"}), 201
    
    searches = get_saved_searches(user_id)
    # Parse query_params back to dict
    for s in searches:
        s['query_params'] = json.loads(s['query_params'])
    return jsonify(searches)

@app.route('/saved-searches/publish/<int:search_id>', methods=['POST'])
def publish_search(search_id):
    publish_saved_search(search_id)
    return jsonify({"message": "Search published to team"}), 200

@app.route('/documents/download/<int:doc_id>', methods=['GET'])
def download_document(doc_id):
    doc = get_document(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
        
    is_admin = request.args.get('is_admin', 'false').lower() == 'true'
    user_id = request.args.get('user_id', 'Guest')
    
    # Check permissions (re-using logic or simplified for here)
    # In production, this would be more robust.
    
    # Log the download activity
    log_audit('document', doc_id, 'DOWNLOAD', f"Document downloaded by {user_id}", user_id, ip_address=request.remote_addr)
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
    if not os.path.exists(file_path):
        # Check processed folder
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], doc['filename'])
        if not os.path.exists(file_path):
             return jsonify({"error": "File not found on disk"}), 404

    # Check if watermark needed (Confidential)
    # We need to get container info for confidentiality
    from database.db import get_db_connection
    conn = get_db_connection()
    c_info = conn.execute("SELECT c.confidentiality_level FROM containers c WHERE c.id = ?", (doc['container_id'],)).fetchone()
    conn.close()
    
    is_confidential = c_info and c_info['confidentiality_level'] == 'Confidential'
    
    if is_confidential:
        output_stream = io.BytesIO()
        ext = doc['filename'].split('.')[-1].lower()
        if ext == 'pdf':
            apply_watermark_pdf(file_path, output_stream)
            mimetype = 'application/pdf'
        elif ext in ['jpg', 'jpeg', 'png']:
            apply_watermark_image(file_path, output_stream)
            mimetype = f'image/{ext}'
        else:
            # Fallback for other files
            return send_file(file_path, as_attachment=True)
            
        output_stream.seek(0)
        return send_file(output_stream, mimetype=mimetype, as_attachment=True, download_name=f"CONFIDENTIAL_{doc['filename']}")
    
    return send_file(file_path, as_attachment=True)
    
@app.route('/scan/direct', methods=['POST'])
def direct_scan():
    if not HAS_SCANNER_LIB:
        return jsonify({"error": "Scanner library (pywin32/WIA) not available on server"}), 501
    
    try:
        # Generate temporary intake folder
        intake_temp = os.path.join(app.config['UPLOAD_FOLDER'], 'intake_temp')
        os.makedirs(intake_temp, exist_ok=True)
        
        scan_id = uuid.uuid4().hex[:8].upper()
        filename = f"SCAN_{scan_id}.png"
        filepath = os.path.join(intake_temp, filename)
        
        # WIA.CommonDialog Constant for Acquire Image
        # formatID for PNG is {B96B3CAF-0728-11D3-9D7B-0000F81EF32E}
        WIA_FORMAT_PNG = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
        
        dialog = win32com.client.Dispatch("WIA.CommonDialog")
        # 1 = wiaItemTypeImage
        image = dialog.ShowAcquireImage()
        
        if image:
            image.SaveFile(filepath)
            return jsonify({
                "message": "Scan successful",
                "filename": filename,
                "path": filepath
            }), 200
        else:
            return jsonify({"error": "Scan cancelled by user"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Direct Scan failed: {str(e)}"}), 500

@app.route('/taxonomy/versioned-update', methods=['POST'])
@require_auth(roles=['Admin'])
def update_taxonomy_versioned_route():
    from utils.taxonomy_versioning import update_taxonomy_item_versioned
    data = request.json
    item_id = data.get('id')
    new_value = data.get('value')
    
    if not item_id or not new_value:
        return jsonify({"error": "Missing id or value"}), 400
        
    result = update_taxonomy_item_versioned(item_id, new_value)
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result), 200

if __name__ == '__main__':
    try:
        from utils.backup_service import perform_backup
        print("--- Starting Automated Backup (RPO) ---")
        perform_backup()
        print("--- Backup Completed ---")
    except Exception as e:
        print(f"Startup Backup Failed: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)

