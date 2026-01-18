import urllib.request
import urllib.parse
import json
import time
import os
import sqlite3
import datetime
import mimetypes

# Configuration
BASE_URL = 'http://localhost:5000'
DB_PATH = 'backend/documents.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def encode_multipart_formdata(fields, files):
    boundary = '---BOUNDARY' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    crlf = b'\r\n'
    encoded_data = []

    for key, value in fields.items():
        encoded_data.append(('--' + boundary).encode())
        encoded_data.append(crlf)
        encoded_data.append(('Content-Disposition: form-data; name="%s"' % key).encode())
        encoded_data.append(crlf)
        encoded_data.append(crlf)
        encoded_data.append(str(value).encode())
        encoded_data.append(crlf)

    for key, filepath in files.items():
        filename = os.path.basename(filepath)
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        with open(filepath, 'rb') as f:
            file_content = f.read()
            
        encoded_data.append(('--' + boundary).encode())
        encoded_data.append(crlf)
        encoded_data.append(('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename)).encode())
        encoded_data.append(crlf)
        encoded_data.append(('Content-Type: %s' % mime_type).encode())
        encoded_data.append(crlf)
        encoded_data.append(crlf)
        encoded_data.append(file_content)
        encoded_data.append(crlf)

    encoded_data.append(('--' + boundary + '--').encode())
    encoded_data.append(crlf)

    body = b"".join(encoded_data)
    content_type = 'multipart/form-data; boundary=' + boundary
    return content_type, body

def verify_fix():
    print("--- Starting Verification (Urllib) ---")
    
    # 1. Create a dummy file
    filename = 'test_manual_cat.txt'
    with open(filename, 'w') as f:
        f.write("Some random content that might be classified as Reference or Other.")
        
    # 2. Upload with Manual Category "Legal"
    print("Uploading file with manual category 'Legal'...")
    try:
        fields = {
            'category': 'Legal',
            'uploader_id': 'Verifier',
            'tags': 'verify_fix'
        }
        files = {'file': filename}
        
        content_type, body = encode_multipart_formdata(fields, files)
        
        req = urllib.request.Request(f"{BASE_URL}/upload", data=body)
        req.add_header('Content-Type', content_type)
        
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            doc_id = res_json[0]['id']
            print(f"Upload successful. Doc ID: {doc_id}")
            
    except urllib.error.HTTPError as e:
        print(f"Upload failed HTTP: {e.code} {e.read().decode()}")
        return
    except Exception as e:
        print(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Wait for Background Processing
    print("Waiting for background processing...")
    
    conn = get_db_connection()
    doc = None
    for i in range(10):
        time.sleep(1)
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if doc and doc['status'] != 'Processing':
            break
            
    conn.close()
    
    if not doc:
        print("Error: Document not found in DB.")
        return

    print(f"Document Status: {doc['status']}")
    print(f"Document Category: {doc['category']}")
    print(f"Document Confidence: {doc['confidence']}")
    print(f"OCR Status: {doc['ocr_status']}")
    
    # 5. Assertions
    success = True
    
    if doc['category'] != 'Legal':
        print("FAILURE: Category mismatch. Expected 'Legal'.")
        success = False
    else:
        print("SUCCESS: Category matches manual input.")
        
    try:
        conf_val = float(doc['confidence'])
        if conf_val < 0.99:
             print(f"FAILURE: Confidence too low ({conf_val}). Expected 1.0 needed for manual override.")
             success = False
        else:
             print("SUCCESS: Confidence is high (1.0).")
    except:
        print(f"FAILURE: Confidence invalid: {doc['confidence']}")
        success = False

    if success:
        print("\n--- VERIFICATION PASSED ---")
    else:
        print("\n--- VERIFICATION FAILED ---")

if __name__ == "__main__":
    verify_fix()
