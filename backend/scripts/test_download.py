import requests
import os

BASE_URL = "http://localhost:5000"

def test_download():
    # 1. Get a document ID (assuming database is seeded)
    res = requests.get(f"{BASE_URL}/documents?user_id=Gokul_Admin&is_admin=true")
    docs = res.json()
    if not docs:
        print("No documents found to test download.")
        return

    doc = docs[0]
    doc_id = doc['id']
    filename = doc['filename']
    print(f"Testing download for doc {doc_id} ({filename})...")

    # 2. Try download
    res = requests.get(f"{BASE_URL}/documents/download/{doc_id}?user_id=Gokul_Admin&is_admin=true")
    if res.status_code == 200:
        print(f"Download successful. Content-Type: {res.headers.get('Content-Type')}")
        # Save to temp file
        with open(f"test_download_{filename}", "wb") as f:
            f.write(res.content)
        print(f"Saved to test_download_{filename}")
    else:
        print(f"Download failed with status {res.status_code}: {res.text}")

if __name__ == "__main__":
    test_download()
