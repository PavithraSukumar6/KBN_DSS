import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def check_endpoint(url, method="GET"):
    try:
        if method == "GET":
            return requests.get(url)
        elif method == "DELETE":
            return requests.delete(url)
    except Exception as e:
        log(f"Request failed: {e}", "ERROR")
        return None

def verify_actions():
    log("--- Starting Action Verification ---")
    
    # 1. Fetch Documents list to get a valid ID
    log("Fetching document list...")
    list_res = check_endpoint(f"{BASE_URL}/documents")
    if not list_res or list_res.status_code != 200:
        log("Failed to fetch documents list", "FAIL")
        return

    docs = list_res.json()
    if not docs:
        log("No documents found to test with.", "WARN")
        return

    test_doc = docs[0]
    log(f"Testing with Document ID: {test_doc['id']} (File: {test_doc['filename']})")

    # 2. Test Details (Metadata) Endpoint
    log("Testing Details Endpoint...")
    details_res = check_endpoint(f"{BASE_URL}/documents/{test_doc['id']}/details")
    if details_res and details_res.status_code == 200:
        log("Details Endpoint: OK", "PASS")
        print(json.dumps(details_res.json(), indent=2)[:200] + "...")
    else:
        log(f"Details Endpoint Failed: {details_res.status_code if details_res else 'Error'}", "FAIL")

    # 3. Test Versions Endpoint (Used by View)
    log("Testing Versions Endpoint...")
    ver_res = check_endpoint(f"{BASE_URL}/documents/{test_doc['id']}/versions")
    if ver_res and ver_res.status_code == 200:
        log("Versions Endpoint: OK", "PASS")
        print(str(ver_res.json())[:200])
    else:
        log(f"Versions Endpoint Failed: {ver_res.status_code if ver_res else 'Error'}", "FAIL")

    # 4. Test View URL Reachability
    view_url = f"{BASE_URL}/view/{test_doc['id']}?user_id=TestBot"
    log(f"Testing View URL: {view_url}")
    # We expect a file stream or redirect. 
    # Just checking headers here.
    try:
        view_res = requests.head(view_url)
        if view_res.status_code in [200, 302, 301]:
             log(f"View URL Reachable (Status: {view_res.status_code})", "PASS")
        else:
             log(f"View URL returned unusual status: {view_res.status_code}", "WARN")
    except Exception as e:
        log(f"View URL check failed: {e}", "FAIL")

    log("--- Verification Complete ---")

if __name__ == "__main__":
    verify_actions()
