import requests
import time
import os

BASE_URL = "http://localhost:5000"

def test_delete():
    print("--- Starting Delete Functionality Test ---")
    
    # 1. Create dummy file
    with open("delete_test.txt", "w") as f: f.write("Delete Me " + str(time.time()))
    
    # 2. Upload
    print("Uploading file...")
    files = {'file': open("delete_test.txt", 'rb')}
    data = {'uploader_id': 'Tester', 'category': 'Test'}
    res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    assert res.status_code == 200, f"Upload failed: {res.text}"
    doc_id = res.json()['documents'][0]['id']
    print(f"File uploaded. ID: {doc_id}")
    
    time.sleep(1)
    
    # 3. Delete
    print(f"Deleting ID: {doc_id}...")
    # Fix: Must pass matching user_id or is_admin
    res = requests.delete(f"{BASE_URL}/documents/{doc_id}?user_id=Tester")
    
    print(f"Delete Response Code: {res.status_code}")
    print(f"Delete Response Text: {res.text}")
    
    assert res.status_code == 200, "Delete failed"
    
    # 4. Verify - Should be gone from list OR status=Soft_Deleted
    # By default list hides deleted
    list_res = requests.get(f"{BASE_URL}/documents")
    all_ids = [d['id'] for d in list_res.json()]
    
    if doc_id in all_ids:
        print("FAIL: Document still visible in default list.")
        # Check status
        doc = requests.get(f"{BASE_URL}/documents/{doc_id}/details").json()
        print(f"Document Status: {doc.get('status')} (Expected: Soft_Deleted)")
    else:
        print("SUCCESS: Document verified deleted (hidden from list).")

    # Cleanup
    os.remove("delete_test.txt")

if __name__ == "__main__":
    test_delete()
