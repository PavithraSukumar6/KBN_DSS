import os
import sys
import requests
import hashlib

# Configuration
BASE_URL = "http://localhost:5000"
TEST_FILE_NAME = "test_duplicate.txt"
TEST_FILE_CONTENT = b"This is a unique test file content for duplicate detection."

def create_test_file():
    with open(TEST_FILE_NAME, "wb") as f:
        f.write(TEST_FILE_CONTENT)

def cleanup():
    if os.path.exists(TEST_FILE_NAME):
        os.remove(TEST_FILE_NAME)

def upload_file(expect_status):
    print(f"Uploading {TEST_FILE_NAME} (Expect {expect_status})...")
    with open(TEST_FILE_NAME, "rb") as f:
        files = {'file': (TEST_FILE_NAME, f)}
        data = {'user_id': 'Tester'}
        try:
            res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
            print(f"Status: {res.status_code}")
            if res.status_code == expect_status:
                print("PASS")
                if res.status_code == 409:
                    print(f"Response: {res.json()}")
            else:
                print(f"FAIL: Expected {expect_status}, got {res.status_code}")
                try:
                    err_json = res.json()
                    if 'traceback' in err_json:
                        print(f"Server Traceback:\n{err_json['traceback']}")
                    else:
                        print(f"Response: {err_json}")
                except:
                     print(f"Response: {res.text}")
        except Exception as e:
            print(f"Error: {e}")

def run_test():
    create_test_file()
    
    # 1. First Upload -> Success (200)
    print("\n--- Test 1: Initial Upload ---")
    upload_file(200)
    
    # 2. Second Upload -> Conflict (409)
    print("\n--- Test 2: Duplicate Upload ---")
    upload_file(409)
    
    cleanup()

if __name__ == "__main__":
    run_test()
