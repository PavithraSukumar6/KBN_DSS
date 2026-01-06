import requests
import json

BASE_URL = "http://localhost:5000"

def test_lifecycle():
    print("--- STARTING LIFECYCLE VERIFICATION ---")
    
    # 1. Setup Retention Policy
    print("\n1. Setting Retention Policy...")
    res = requests.post(f"{BASE_URL}/retention-policies?is_admin=true", json={
        "document_type": "Invoice",
        "retention_years": 5
    })
    print(f"Policy Set Status: {res.status_code}")
    assert res.status_code == 200
    
    # 2. Toggle Legal Hold ON
    print("\n2. Activating Legal Hold...")
    res = requests.post(f"{BASE_URL}/settings/legal-hold?is_admin=true", json={"active": True})
    print(f"Legal Hold On: {res.json()}")
    
    # 3. Attempt Delete (Should Fail)
    # Get a doc first
    docs = requests.get(f"{BASE_URL}/documents").json()
    if not docs:
        print("No documents to test delete. Skipping delete test.")
    else:
        doc_id = docs[0]['id']
        print(f"\n3. Attempting to delete Doc {doc_id} under Hold...")
        res = requests.delete(f"{BASE_URL}/documents/{doc_id}?is_admin=true")
        print(f"Delete Status: {res.status_code} (Expected 403)")
        assert res.status_code == 403
        
    # 4. Toggle Legal Hold OFF
    print("\n4. Deactivating Legal Hold...")
    res = requests.post(f"{BASE_URL}/settings/legal-hold?is_admin=true", json={"active": False})
    print(f"Legal Hold Off: {res.json()}")
    
    # 5. Attempt Soft Delete (Should Succeed)
    if docs:
        doc_id = docs[0]['id']
        print(f"\n5. Soft Deleting Doc {doc_id}...")
        res = requests.delete(f"{BASE_URL}/documents/{doc_id}?is_admin=true")
        print(f"Delete Status: {res.status_code} (Expected 200)")
        assert res.status_code == 200
        
        # Verify status
        doc = requests.get(f"{BASE_URL}/document/{doc_id}").json()
        print(f"Doc Status: {doc.get('status')} (Expected 'Soft_Deleted')")
        assert doc.get('status') == 'Soft_Deleted'
        
        # 6. Restore
        print(f"\n6. Restoring Doc {doc_id}...")
        res = requests.post(f"{BASE_URL}/documents/{doc_id}/restore?is_admin=true")
        print(f"Restore Status: {res.status_code}")
        assert res.status_code == 200
        
        doc = requests.get(f"{BASE_URL}/document/{doc_id}").json()
        print(f"Doc Status: {doc.get('status')} (Expected 'Published')")

    print("\n--- LIFECYCLE VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    try:
        test_lifecycle()
    except Exception as e:
        print(f"Verification Failed: {e}")
