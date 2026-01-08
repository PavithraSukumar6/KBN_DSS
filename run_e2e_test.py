
import requests
import json
import os

BASE_URL = 'http://localhost:5000'

def run_test():
    print("Starting E2E Test...")
    
    # 1. Get Container ID
    print("Fetching containers...")
    containers = requests.get(f"{BASE_URL}/containers").json()
    target_container = next((c for c in containers if c['name'] == 'Test_QA_Container'), None)
    
    if not target_container:
        print("FAIL: Test_QA_Container not found.")
        return
    
    container_id = target_container['id']
    print(f"PASS: Found container {container_id}")
    
    # 2. Upload Document
    print("Uploading document...")
    # Create dummy file
    with open('test_doc.txt', 'w') as f:
        f.write("This is a test document content for QA.")
        
    files = {'file': ('test_doc.txt', open('test_doc.txt', 'rb'))}
    data = {
        'container_id': container_id,
        'fast_track': 'true',
        'uploader_id': 'QA_Bot',
        'department': 'Testing'
    }
    
    res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    
    if res.status_code != 200:
        print(f"FAIL: Upload failed {res.status_code} - {res.text}")
        return
        
    doc_data = res.json()
    print(f"PASS: Upload successful. Response: {json.dumps(doc_data, indent=2)}")
    
    # 3. Verify Status
    print("Verifying document status...")
    # Fetch specific doc or search
    # The upload response usually contains the doc ID in 'documents' list
    uploaded_id = doc_data['documents'][0]['id']
    
    # Check details
    # We use the filter logic: GET /documents?status=Published
    res_docs = requests.get(f"{BASE_URL}/documents?status=Published").json()
    
    found_doc = next((d for d in res_docs if d['id'] == uploaded_id), None)
    
    if found_doc:
        print(f"PASS: Document {uploaded_id} found in 'Published' list.")
        print(f"Details: Status={found_doc['status']}, Container={found_doc['container_id']}")
        
        if found_doc['status'] == 'Published' and found_doc['container_id'] == container_id:
             print("SUCCESS: End-to-End Logic Verified.")
        else:
             print("FAIL: Metadata mismatch.")
    else:
        print(f"FAIL: Document {uploaded_id} NOT found in Published list. (Check status)")
        # Check actual status
        all_docs = requests.get(f"{BASE_URL}/documents").json()
        actual = next((d for d in all_docs if d['id'] == uploaded_id), None)
        if actual:
            print(f"DEBUG: Actual status is '{actual['status']}'")

if __name__ == "__main__":
    run_test()
