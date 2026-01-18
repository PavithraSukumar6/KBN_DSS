import requests
import time
import os

BASE_URL = "http://localhost:5000"

def test_versioning():
    print("--- Starting Versioning Test ---")
    
    # 1. Create dummy files
    # 1. Create dummy files
    ts = time.time()
    with open("ver_v1.txt", "w") as f: f.write(f"Version 1 Content {ts}")
    with open("ver_v2.txt", "w") as f: f.write(f"Version 2 Content {ts}")
    
    # 2. Upload V1
    print("Uploading V1...")
    files = {'file': open("ver_v1.txt", 'rb')}
    data = {'uploader_id': 'Tester', 'category': 'Test'}
    res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    assert res.status_code == 200
    v1_id = res.json()['documents'][0]['id']
    print(f"V1 Uploaded. ID: {v1_id}")
    
    # Wait for processing (status update)
    time.sleep(2)
    
    # 3. Upload V2 (superseding V1)
    print("Uploading V2 (superseding V1)...")
    files = {'file': open("ver_v2.txt", 'rb')}
    data = {'uploader_id': 'Tester', 'category': 'Test', 'parent_doc_id': v1_id}
    res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    if res.status_code != 200:
        print("Error uploading V2:", res.text)
        return
    v2_id = res.json()['documents'][0]['id']
    print(f"V2 Uploaded. ID: {v2_id}")
    
    time.sleep(2)
    
    # 4. Verify Status
    print("Verifying Statuses...")
    v1_doc = requests.get(f"{BASE_URL}/documents/{v1_id}/details").json()
    v2_doc = requests.get(f"{BASE_URL}/documents/{v2_id}/details").json()
    
    print(f"V1 Status: {v1_doc['status']} (Expected: Superseded)")
    print(f"V2 Status: {v2_doc['status']} (Expected: Published)")
    print(f"V2 Version Number: {v2_doc['version_number']} (Expected: 2)")
    
    assert v1_doc['status'] == 'Superseded', f"V1 status wrong: {v1_doc['status']}"
    assert v2_doc['status'] == 'Published', f"V2 status wrong: {v2_doc['status']}"
    assert v2_doc['version_number'] == 2, f"V2 version wrong: {v2_doc['version_number']}"
    
    # 5. Verify Listing (Default filter)
    print("Verifying List Filter (V1 should be hidden)...")
    list_res = requests.get(f"{BASE_URL}/documents")
    all_ids = [d['id'] for d in list_res.json()]
    
    if v1_id in all_ids:
        print("FAIL: V1 is still in the default list!")
    else:
        print("SUCCESS: V1 is hidden.")
        
    if v2_id in all_ids:
        print("SUCCESS: V2 is visible.")
    else:
        print("FAIL: V2 is missing from list!")

    # 6. Verify Versions Endpoint
    print("Verifying /versions endpoint...")
    vers = requests.get(f"{BASE_URL}/documents/{v2_id}/versions").json()
    print(f"Versions found: {len(vers)}")
    ver_ids = [v['id'] for v in vers]
    assert v1_id in ver_ids and v2_id in ver_ids, "Not all versions returned"
    print("SUCCESS: Both versions found linked.")
    
    print("--- Test Complete: SUCCESS ---")

    # Cleanup
    os.remove("ver_v1.txt")
    os.remove("ver_v2.txt")

if __name__ == "__main__":
    test_versioning()
